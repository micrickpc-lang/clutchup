import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import func, select

from database import Base, SessionLocal, engine
from models import CS2Profile, Lobby, User
from routers.matching import next_card, swipe
from schemas import SwipeRequest


@pytest_asyncio.fixture
async def database():
    if not engine.url.database or engine.url.database not in {"test", "teamfinder_test"}:
        pytest.skip("Integration matching tests require an isolated test database")
    await engine.dispose()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


async def make_users():
    async with SessionLocal() as session:
        first = User(telegram_id=101, username="first", first_name="First")
        second = User(telegram_id=102, username="second", first_name="Second")
        session.add_all([first, second])
        await session.flush()
        session.add_all(
            [
                CS2Profile(
                    user_id=first.id,
                    faceit_player_id="f1",
                    faceit_nickname="First",
                    elo=2000,
                    skill_level=9,
                    primary_role="Rifler",
                ),
                CS2Profile(
                    user_id=second.id,
                    faceit_player_id="f2",
                    faceit_nickname="Second",
                    elo=2100,
                    skill_level=9,
                    primary_role="Rifler",
                ),
            ]
        )
        await session.commit()
        return first.id, second.id


def request():
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.exists.return_value = 1
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=redis, settings=SimpleNamespace(presence_ttl_seconds=105)))
    )


async def user(session, user_id):
    return await session.get(User, user_id)


@pytest.mark.asyncio
async def test_cannot_swipe_self(database):
    first, _ = await make_users()
    async with SessionLocal() as session:
        with pytest.raises(HTTPException, match="yourself"):
            await swipe(
                SwipeRequest(target_user_id=first, direction="like"),
                request(),
                BackgroundTasks(),
                await user(session, first),
                session,
            )


@pytest.mark.asyncio
async def test_missing_target(database):
    first, _ = await make_users()
    async with SessionLocal() as session:
        with pytest.raises(HTTPException, match="not found"):
            await swipe(
                SwipeRequest(target_user_id=999, direction="like"),
                request(),
                BackgroundTasks(),
                await user(session, first),
                session,
            )


@pytest.mark.asyncio
async def test_dislike_and_card_exclusion(database):
    first, second = await make_users()
    async with SessionLocal() as session:
        result = await swipe(
            SwipeRequest(target_user_id=second, direction="dislike"),
            request(),
            BackgroundTasks(),
            await user(session, first),
            session,
        )
        assert not result.matched and not result.new_match
        assert await next_card(request(), await user(session, first), session) is None


@pytest.mark.asyncio
async def test_one_sided_and_mutual_like_notify_once(database):
    first, second = await make_users()
    with patch("routers.matching.send_match_notifications", AsyncMock()):
        async with SessionLocal() as session:
            one = await swipe(
                SwipeRequest(target_user_id=second, direction="like"),
                request(),
                BackgroundTasks(),
                await user(session, first),
                session,
            )
            assert not one.matched
        async with SessionLocal() as session:
            tasks = BackgroundTasks()
            mutual = await swipe(
                SwipeRequest(target_user_id=first, direction="like"),
                request(),
                tasks,
                await user(session, second),
                session,
            )
            assert mutual.matched and mutual.new_match and len(tasks.tasks) == 1
        async with SessionLocal() as session:
            tasks = BackgroundTasks()
            duplicate = await swipe(
                SwipeRequest(target_user_id=first, direction="like"),
                request(),
                tasks,
                await user(session, second),
                session,
            )
            assert duplicate.matched and not duplicate.new_match and len(tasks.tasks) == 0
            assert await session.scalar(select(func.count(Lobby.id))) == 1


@pytest.mark.asyncio
async def test_concurrent_mutual_likes_create_one_lobby(database):
    first, second = await make_users()

    async def like(from_id, to_id):
        async with SessionLocal() as session:
            return await swipe(
                SwipeRequest(target_user_id=to_id, direction="like"),
                request(),
                BackgroundTasks(),
                await user(session, from_id),
                session,
            )

    results = await asyncio.gather(like(first, second), like(second, first))
    async with SessionLocal() as session:
        assert await session.scalar(select(func.count(Lobby.id))) == 1
        assert sum(result.new_match for result in results) == 1
