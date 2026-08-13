from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from config import settings
from database import get_session
from models import (
    CS2Profile,
    GameId,
    GameProfile,
    Party,
    PartyMember,
    PartyMemberRole,
    PartyRequest,
    PartyRequestStatus,
    PartyStatus,
    User,
    UserProfile,
)
from schemas import (
    GameName,
    GameProfileResponse,
    GameProfileUpsert,
    PartyCreate,
    PartyMemberResponse,
    PartyPage,
    PartyRequestResponse,
    PartyResponse,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter()


async def ensure_profile(user: User, session: AsyncSession) -> UserProfile:
    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is None:
        profile = UserProfile(
            user_id=user.id,
            display_name=" ".join(filter(None, [user.first_name, user.last_name]))[:128],
            avatar_url=user.photo_url,
            languages=[],
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile


async def profile_response(user: User, session: AsyncSession) -> UserProfileResponse:
    profile = await ensure_profile(user, session)
    faceit = await session.scalar(select(CS2Profile.id).where(CS2Profile.user_id == user.id))
    return UserProfileResponse(
        id=profile.id,
        user_id=user.id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        birth_year=profile.birth_year,
        country_code=profile.country_code,
        bio=profile.bio,
        languages=profile.languages,
        microphone=profile.microphone,
        playstyle=profile.playstyle,
        preferred_schedule=profile.preferred_schedule,
        faceit_connected=faceit is not None,
    )


@router.get("/me", response_model=UserProfileResponse)
async def me(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    return await profile_response(current_user, session)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    payload: UserProfileUpdate, current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    profile = await ensure_profile(current_user, session)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    await session.commit()
    return await profile_response(current_user, session)


def game_profile_response(profile: GameProfile) -> GameProfileResponse:
    return GameProfileResponse(
        id=profile.id,
        game=profile.game.value,
        nickname=profile.nickname,
        primary_role=profile.primary_role,
        secondary_role=profile.secondary_role,
        rank_label=profile.rank_label,
        rank_value=profile.rank_value,
        region=profile.region,
        is_active=profile.is_active,
    )


@router.get("/game-profiles", response_model=list[GameProfileResponse])
async def game_profiles(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    cs2 = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    existing_cs2 = await session.scalar(
        select(GameProfile).where(GameProfile.user_id == current_user.id, GameProfile.game == GameId.cs2)
    )
    if cs2 is not None and existing_cs2 is None:
        session.add(
            GameProfile(
                user_id=current_user.id,
                game=GameId.cs2,
                nickname=cs2.faceit_nickname,
                primary_role=cs2.primary_role,
                secondary_role=cs2.secondary_role,
                rank_label=f"FACEIT {cs2.skill_level}",
                rank_value=cs2.elo,
                region=cs2.country_code,
            )
        )
        await session.commit()
    rows = (await session.scalars(select(GameProfile).where(GameProfile.user_id == current_user.id))).all()
    return [game_profile_response(row) for row in rows]


@router.put("/game-profiles/{game}", response_model=GameProfileResponse)
async def put_game_profile(
    game: GameName, payload: GameProfileUpsert, current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    stmt = (
        insert(GameProfile)
        .values(user_id=current_user.id, game=game, **payload.model_dump())
        .on_conflict_do_update(constraint="uq_game_profile_user_game", set_=payload.model_dump())
        .returning(GameProfile)
    )
    profile = (await session.execute(stmt)).scalar_one()
    await session.commit()
    return game_profile_response(profile)


async def serialize(party: Party, session: AsyncSession, viewer_id: int) -> PartyResponse:
    profiles = {
        p.user_id: p
        for p in (
            await session.scalars(
                select(UserProfile).where(UserProfile.user_id.in_([m.user_id for m in party.members]))
            )
        ).all()
    }
    users = {
        u.id: u
        for u in (await session.scalars(select(User).where(User.id.in_([m.user_id for m in party.members])))).all()
    }
    members = [
        PartyMemberResponse(
            user_id=m.user_id,
            display_name=(
                profiles.get(m.user_id).display_name if profiles.get(m.user_id) else users[m.user_id].first_name
            ),
            avatar_url=(profiles.get(m.user_id).avatar_url if profiles.get(m.user_id) else users[m.user_id].photo_url),
            role=m.role.value,
        )
        for m in party.members
    ]
    request = await session.scalar(
        select(PartyRequest).where(PartyRequest.party_id == party.id, PartyRequest.requester_user_id == viewer_id)
    )
    count = len(members)
    return PartyResponse(
        id=party.id,
        owner_user_id=party.owner_user_id,
        game=party.game.value,
        title=party.title,
        mode=party.mode,
        capacity=party.capacity,
        current_members=count,
        free_slots=max(0, party.capacity - count),
        vibe=party.vibe,
        language=party.language,
        mic_required=party.mic_required,
        rank_min=party.rank_min,
        rank_max=party.rank_max,
        description=party.description,
        status=party.status.value,
        created_at=party.created_at,
        expires_at=party.expires_at,
        members=members,
        request_status=request.status.value if request else None,
    )


@router.post("/parties", response_model=PartyResponse, status_code=201)
async def create_party(payload: PartyCreate, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    await ensure_profile(current_user, session)
    party = Party(
        owner_user_id=current_user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=settings.party_ttl_hours),
        **payload.model_dump(),
    )
    session.add(party)
    await session.flush()
    session.add(PartyMember(party_id=party.id, user_id=current_user.id, role=PartyMemberRole.OWNER))
    await session.commit()
    await session.refresh(party)
    return await serialize(party, session, current_user.id)


@router.get("/parties/discover", response_model=PartyPage)
async def discover_parties(
    current_user: CurrentUser,
    game: GameName,
    mode: str | None = None,
    language: str | None = None,
    mic_required: bool | None = None,
    free_slots: int | None = Query(None, ge=1, le=9),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(UTC)
    clauses = [
        Party.game == GameId(game),
        Party.status == PartyStatus.OPEN,
        Party.expires_at > now,
        Party.owner_user_id != current_user.id,
    ]
    if mode:
        clauses.append(Party.mode == mode)
    if language:
        clauses.append(Party.language == language)
    if mic_required is not None:
        clauses.append(Party.mic_required == mic_required)
    rows = (
        (await session.scalars(select(Party).where(*clauses).order_by(Party.created_at.desc()).limit(50)))
        .unique()
        .all()
    )
    result = []
    for party in rows:
        item = await serialize(party, session, current_user.id)
        if free_slots is None or item.free_slots >= free_slots:
            result.append(item)
    return PartyPage(items=result)


@router.get("/parties/mine", response_model=PartyPage)
async def my_parties(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    ids = select(PartyMember.party_id).where(PartyMember.user_id == current_user.id)
    rows = (
        (await session.scalars(select(Party).where(Party.id.in_(ids)).order_by(Party.updated_at.desc()))).unique().all()
    )
    return PartyPage(items=[await serialize(p, session, current_user.id) for p in rows])


@router.get("/parties/{party_id}", response_model=PartyResponse)
async def party_detail(party_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    party = await session.scalar(select(Party).where(Party.id == party_id))
    if not party:
        raise HTTPException(404, "Party not found")
    return await serialize(party, session, current_user.id)


@router.post("/parties/{party_id}/requests", response_model=PartyRequestResponse, status_code=201)
async def request_join(party_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    party = await session.scalar(select(Party).where(Party.id == party_id))
    if not party or party.status != PartyStatus.OPEN or party.expires_at <= datetime.now(UTC):
        raise HTTPException(409, "Party is not open")
    if party.owner_user_id == current_user.id:
        raise HTTPException(400, "Owner is already in the party")
    existing = await session.scalar(
        select(PartyRequest).where(PartyRequest.party_id == party_id, PartyRequest.requester_user_id == current_user.id)
    )
    if existing and existing.status in (PartyRequestStatus.PENDING, PartyRequestStatus.ACCEPTED):
        raise HTTPException(409, "Request already exists")
    if existing:
        existing.status = PartyRequestStatus.PENDING
    else:
        existing = PartyRequest(party_id=party_id, requester_user_id=current_user.id, status=PartyRequestStatus.PENDING)
        session.add(existing)
    await session.commit()
    await session.refresh(existing)
    profile = await ensure_profile(current_user, session)
    return PartyRequestResponse(
        id=existing.id,
        party_id=party.id,
        party_title=party.title,
        requester_user_id=current_user.id,
        requester_name=profile.display_name,
        status=existing.status.value,
        created_at=existing.created_at,
    )


@router.get("/party-requests/inbox", response_model=list[PartyRequestResponse])
async def request_inbox(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    rows = (
        await session.scalars(
            select(PartyRequest)
            .join(Party)
            .where(or_(Party.owner_user_id == current_user.id, PartyRequest.requester_user_id == current_user.id))
            .order_by(PartyRequest.created_at.desc())
        )
    ).all()
    result = []
    for row in rows:
        profile = await ensure_profile(row.requester, session)
        result.append(
            PartyRequestResponse(
                id=row.id,
                party_id=row.party_id,
                party_title=row.party.title,
                requester_user_id=row.requester_user_id,
                requester_name=profile.display_name,
                status=row.status.value,
                created_at=row.created_at,
            )
        )
    return result


async def decide(request_id: int, accept: bool, current_user: User, session: AsyncSession):
    req = await session.scalar(
        select(PartyRequest).where(PartyRequest.id == request_id).with_for_update(of=PartyRequest)
    )
    if not req or req.party.owner_user_id != current_user.id:
        raise HTTPException(404, "Request not found")
    if req.status != PartyRequestStatus.PENDING:
        raise HTTPException(409, "Request already processed")
    if accept:
        count = len(req.party.members)
        if count >= req.party.capacity:
            req.party.status = PartyStatus.FULL
            raise HTTPException(409, "Party is full")
        session.add(PartyMember(party_id=req.party_id, user_id=req.requester_user_id, role=PartyMemberRole.MEMBER))
        req.status = PartyRequestStatus.ACCEPTED
        if count + 1 >= req.party.capacity:
            req.party.status = PartyStatus.FULL
    else:
        req.status = PartyRequestStatus.REJECTED
    await session.commit()
    return {"status": req.status.value}


@router.post("/party-requests/{request_id}/accept")
async def accept_request(request_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    return await decide(request_id, True, current_user, session)


@router.post("/party-requests/{request_id}/reject")
async def reject_request(request_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    return await decide(request_id, False, current_user, session)


@router.post("/party-requests/{request_id}/cancel")
async def cancel_request(request_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    req = await session.scalar(
        select(PartyRequest).where(PartyRequest.id == request_id, PartyRequest.requester_user_id == current_user.id)
    )
    if not req or req.status != PartyRequestStatus.PENDING:
        raise HTTPException(409, "Request cannot be cancelled")
    req.status = PartyRequestStatus.CANCELLED
    await session.commit()
    return {"status": "CANCELLED"}


@router.post("/parties/{party_id}/close")
async def close_party(party_id: int, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    party = await session.scalar(select(Party).where(Party.id == party_id, Party.owner_user_id == current_user.id))
    if not party:
        raise HTTPException(404, "Party not found")
    party.status = PartyStatus.CLOSED
    await session.commit()
    return {"status": "CLOSED"}
