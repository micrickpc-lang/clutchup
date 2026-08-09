from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from auth import CurrentUser
from database import get_session
from models import CS2Profile, Lobby, Swipe, SwipeDirection, User
from schemas import PlayerCard, ProfilePreferences, ProfileResponse, ProfileUpdate, SwipeRequest, SwipeResponse
from services.bot import send_match_notifications
from services.faceit import FaceitService


router = APIRouter()


def to_player_card(user: User, profile: CS2Profile) -> PlayerCard:
    return PlayerCard(
        user_id=user.id,
        telegram_username=user.username,
        display_name=" ".join(filter(None, [user.first_name, user.last_name])),
        faceit_nickname=profile.faceit_nickname,
        avatar_url=profile.avatar_url or user.photo_url,
        elo=profile.elo,
        skill_level=profile.skill_level,
        kd_ratio=profile.kd_ratio,
        role=profile.role,
        bio=profile.bio,
    )


@router.get("/profile/me", response_model=ProfileResponse | None)
async def get_my_profile(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    return await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))


@router.put("/profile/me", response_model=ProfileResponse)
async def update_my_profile(
    payload: ProfileUpdate,
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    faceit = FaceitService(request.app.state.redis)
    faceit_data = await faceit.get_player_profile(payload.faceit_nickname)
    owner = await session.scalar(
        select(CS2Profile).where(
            CS2Profile.faceit_player_id == faceit_data["player_id"],
            CS2Profile.user_id != current_user.id,
        )
    )
    if owner:
        raise HTTPException(status_code=409, detail="This FACEIT profile is already linked")
    profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    values = {
        "faceit_player_id": faceit_data["player_id"],
        "faceit_nickname": faceit_data["nickname"],
        "avatar_url": faceit_data["avatar"],
        "elo": faceit_data["elo"],
        "skill_level": faceit_data["skill_level"],
        "kd_ratio": faceit_data["kd_ratio"],
        "role": payload.role,
        "bio": payload.bio,
        "is_searching": payload.is_searching,
    }
    if profile is None:
        profile = CS2Profile(user_id=current_user.id, **values)
        session.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.patch("/profile/me", response_model=ProfileResponse)
async def update_profile_preferences(
    payload: ProfilePreferences,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="Connect your FACEIT account first")
    profile.role = payload.role
    profile.bio = payload.bio
    profile.is_searching = payload.is_searching
    await session.commit()
    await session.refresh(profile)
    return profile


@router.get("/cards/next", response_model=PlayerCard | None)
async def next_card(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    own = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    if own is None:
        raise HTTPException(status_code=409, detail="Create your CS2 profile first")
    swiped_ids = select(Swipe.to_user_id).where(Swipe.from_user_id == current_user.id)
    row = (
        await session.execute(
            select(User, CS2Profile)
            .join(CS2Profile, CS2Profile.user_id == User.id)
            .where(
                User.id != current_user.id,
                CS2Profile.is_searching.is_(True),
                func.abs(CS2Profile.elo - own.elo) <= 250,
                User.id.not_in(swiped_ids),
            )
            .order_by(func.abs(CS2Profile.elo - own.elo), User.id)
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    user, profile = row
    return to_player_card(user, profile)


@router.get("/matches", response_model=list[PlayerCard])
async def matches(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(User, CS2Profile)
            .join(CS2Profile, CS2Profile.user_id == User.id)
            .join(
                Lobby,
                or_(
                    and_(Lobby.user_low_id == current_user.id, Lobby.user_high_id == User.id),
                    and_(Lobby.user_high_id == current_user.id, Lobby.user_low_id == User.id),
                ),
            )
            .where(Lobby.is_active.is_(True))
            .order_by(Lobby.created_at.desc())
        )
    ).all()
    return [to_player_card(user, profile) for user, profile in rows]


@router.get("/players/{user_id}", response_model=PlayerCard)
async def player_details(user_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(
            select(User, CS2Profile)
            .join(CS2Profile, CS2Profile.user_id == User.id)
            .where(User.id == user_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return to_player_card(*row)


@router.post("/swipe", response_model=SwipeResponse)
async def swipe(
    payload: SwipeRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    if payload.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot swipe yourself")
    target = await session.scalar(select(User).where(User.id == payload.target_user_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Player not found")
    direction = SwipeDirection(payload.direction)
    stmt = insert(Swipe).values(
        from_user_id=current_user.id, to_user_id=target.id, direction=direction
    ).on_conflict_do_update(
        constraint="uq_swipe_pair", set_={"direction": direction}
    )
    await session.execute(stmt)
    matched = False
    if direction == SwipeDirection.like:
        reverse_like = await session.scalar(
            select(Swipe.id).where(
                Swipe.from_user_id == target.id,
                Swipe.to_user_id == current_user.id,
                Swipe.direction == SwipeDirection.like,
            )
        )
        matched = reverse_like is not None
        if matched:
            low, high = sorted((current_user.id, target.id))
            await session.execute(
                insert(Lobby).values(user_low_id=low, user_high_id=high).on_conflict_do_nothing(
                    constraint="uq_lobby_pair"
                )
            )
    await session.commit()
    if matched:
        background_tasks.add_task(send_match_notifications, current_user, target)
    return SwipeResponse(matched=matched, message="Match!" if matched else "Swipe saved")
