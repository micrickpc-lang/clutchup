import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select

from database import Base, SessionLocal, engine
from models import Party, PartyMember, PartyRequest, PartyRequestStatus, User
from routers.parties import accept_request, create_party, discover_parties, request_join
from schemas import PartyCreate


@pytest_asyncio.fixture
async def database():
    if not engine.url.database or engine.url.database not in {"test", "teamfinder_test"}:
        pytest.skip("Integration party tests require an isolated test database")
    await engine.dispose()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


async def users():
    async with SessionLocal() as session:
        owner = User(telegram_id=501, first_name="Owner")
        guest = User(telegram_id=502, first_name="Guest")
        session.add_all([owner, guest])
        await session.commit()
        return owner.id, guest.id


def payload(game="valorant", capacity=3):
    return PartyCreate(
        game=game,
        title="Ranked tonight",
        mode="Competitive",
        capacity=capacity,
        vibe=65,
        language="en",
        mic_required=True,
        description="Two games, clear comms",
    )


@pytest.mark.asyncio
async def test_create_and_game_filtered_discovery(database):
    owner_id, guest_id = await users()
    async with SessionLocal() as session:
        owner, guest = await session.get(User, owner_id), await session.get(User, guest_id)
        created = await create_party(payload(), owner, session)
        assert created.current_members == 1 and created.free_slots == 2
    async with SessionLocal() as session:
        guest = await session.get(User, guest_id)
        valorant = await discover_parties(guest, "valorant", None, None, None, None, session)
        cs2 = await discover_parties(guest, "cs2", None, None, None, None, session)
        assert [party.id for party in valorant.items] == [created.id]
        assert cs2.items == []


@pytest.mark.asyncio
async def test_duplicate_request_and_accept_membership(database):
    owner_id, guest_id = await users()
    async with SessionLocal() as session:
        owner = await session.get(User, owner_id)
        party = await create_party(payload(capacity=2), owner, session)
    async with SessionLocal() as session:
        guest = await session.get(User, guest_id)
        request = await request_join(party.id, guest, session)
        with pytest.raises(HTTPException, match="already exists"):
            await request_join(party.id, guest, session)
    async with SessionLocal() as session:
        owner = await session.get(User, owner_id)
        result = await accept_request(request.id, owner, session)
        assert result["status"] == "ACCEPTED"
        saved = await session.get(Party, party.id)
        members = (await session.scalars(select(PartyMember).where(PartyMember.party_id == party.id))).all()
        assert len(members) == 2 and saved.status.value == "FULL"


@pytest.mark.asyncio
async def test_rejected_request_is_not_membership(database):
    owner_id, guest_id = await users()
    async with SessionLocal() as session:
        owner = await session.get(User, owner_id)
        party = await create_party(payload(), owner, session)
    async with SessionLocal() as session:
        guest = await session.get(User, guest_id)
        request = await request_join(party.id, guest, session)
        row = await session.get(PartyRequest, request.id)
        row.status = PartyRequestStatus.REJECTED
        await session.commit()
        members = (await session.scalars(select(PartyMember).where(PartyMember.party_id == party.id))).all()
        assert len(members) == 1
