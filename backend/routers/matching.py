from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_session
from models import CS2Profile, Lobby, Swipe, SwipeDirection, User
from schemas import (
    MatchItem,
    MatchPage,
    PlayerDetails,
    ProfileResponse,
    ProfileUpdate,
    SearchPreferences,
    Statistics,
    SwipeRequest,
    SwipeResponse,
)
from services.bot import send_match_notifications
from services.faceit import FaceitService
from services.rate_limit import rate_limit

router = APIRouter()


def stats(
    profile: CS2Profile, *, recent_form: list[str] | None = None, maps: dict[str, int] | None = None
) -> Statistics:
    return Statistics(
        elo=max(0, profile.elo),
        skill_level=max(0, min(10, profile.skill_level)),
        kd_ratio=profile.kd_ratio,
        adr=profile.adr,
        hs_percent=profile.hs_percent,
        win_rate=profile.win_rate,
        matches=profile.matches_count,
        recent_form=recent_form or [],
        map_distribution=maps or {},
    )


async def online(request: Request, user_id: int) -> bool:
    return bool(await request.app.state.redis.exists(f"presence:{user_id}"))


async def details(request: Request, user: User, profile: CS2Profile) -> PlayerDetails:
    return PlayerDetails(
        user_id=user.id,
        telegram_username=user.username,
        display_name=" ".join(filter(None, [user.first_name, user.last_name])),
        faceit_nickname=profile.faceit_nickname,
        avatar_url=profile.avatar_url or user.photo_url,
        country_code=profile.country_code,
        birth_year=profile.birth_year,
        primary_role=profile.primary_role,
        secondary_role=profile.secondary_role,
        playstyle=profile.playstyle,
        bio=profile.bio,
        preferred_maps=profile.preferred_maps or [],
        languages=profile.languages or [],
        microphone=profile.microphone,
        schedule=profile.schedule,
        is_online=await online(request, user.id),
        statistics=stats(profile),
    )


def preferences(profile: CS2Profile) -> SearchPreferences:
    return SearchPreferences(
        elo_min=profile.filter_elo_min,
        elo_max=profile.filter_elo_max,
        max_elo_difference=profile.max_elo_difference,
        roles=profile.filter_roles or [],
        language=profile.filter_language,
        schedule=profile.filter_schedule,
        online_only=profile.online_only,
    )


async def own_profile(current_user: User, session: AsyncSession) -> CS2Profile:
    profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=409, detail="Connect your FACEIT account first")
    return profile


@router.post("/presence", status_code=204)
async def heartbeat(request: Request, current_user: CurrentUser) -> None:
    await request.app.state.redis.setex(
        f"presence:{current_user.id}", request.app.state.settings.presence_ttl_seconds, "1"
    )


@router.get("/profile/me", response_model=ProfileResponse | None)
async def get_my_profile(request: Request, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == current_user.id))
    if profile is None:
        return None
    player = await details(request, current_user, profile)
    return ProfileResponse(**player.model_dump(), is_searching=profile.is_searching, preferences=preferences(profile))


@router.patch("/profile/me", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate, request: Request, current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    profile = await own_profile(current_user, session)
    for name, value in payload.model_dump().items():
        setattr(profile, name, value)
    await session.commit()
    await session.refresh(profile)
    player = await details(request, current_user, profile)
    return ProfileResponse(**player.model_dump(), is_searching=profile.is_searching, preferences=preferences(profile))


@router.get("/preferences", response_model=SearchPreferences)
async def get_preferences(current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    return preferences(await own_profile(current_user, session))


@router.put("/preferences", response_model=SearchPreferences)
async def update_preferences(
    payload: SearchPreferences, current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    profile = await own_profile(current_user, session)
    values = payload.model_dump()
    profile.filter_elo_min = values["elo_min"]
    profile.filter_elo_max = values["elo_max"]
    profile.max_elo_difference = values["max_elo_difference"]
    profile.filter_roles = values["roles"]
    profile.filter_language = values["language"]
    profile.filter_schedule = values["schedule"]
    profile.online_only = values["online_only"]
    await session.commit()
    return payload


async def online_user_ids(request: Request) -> list[int]:
    result: list[int] = []
    async for key in request.app.state.redis.scan_iter(match="presence:*", count=200):
        try:
            result.append(int(str(key).rsplit(":", 1)[1]))
        except (ValueError, IndexError):
            continue
    return result


@router.get("/cards/next", response_model=PlayerDetails | None)
async def next_card(request: Request, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    own = await own_profile(current_user, session)
    elo_min = max(own.filter_elo_min, own.elo - own.max_elo_difference)
    elo_max = min(own.filter_elo_max, own.elo + own.max_elo_difference)
    clauses = [
        User.id != current_user.id,
        CS2Profile.is_searching.is_(True),
        CS2Profile.elo >= elo_min,
        CS2Profile.elo <= elo_max,
        ~select(Swipe.id).where(Swipe.from_user_id == current_user.id, Swipe.to_user_id == User.id).exists(),
    ]
    if own.filter_roles:
        clauses.append(CS2Profile.primary_role.in_(own.filter_roles))
    if own.filter_language:
        clauses.append(CS2Profile.languages.contains([own.filter_language]))
    if own.filter_schedule:
        clauses.append(CS2Profile.schedule == own.filter_schedule)
    if own.online_only:
        ids = await online_user_ids(request)
        if not ids:
            return None
        clauses.append(User.id.in_(ids))
    row = (
        await session.execute(
            select(User, CS2Profile)
            .join(CS2Profile, CS2Profile.user_id == User.id)
            .where(*clauses)
            .order_by(func.abs(CS2Profile.elo - own.elo), User.id)
            .limit(1)
        )
    ).first()
    return None if row is None else await details(request, row[0], row[1])


@router.get("/players/{user_id}", response_model=PlayerDetails)
async def player_details(
    user_id: int, request: Request, current_user: CurrentUser, session: AsyncSession = Depends(get_session)
):
    row = (await session.execute(select(User, CS2Profile).join(CS2Profile).where(User.id == user_id))).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return await details(request, row[0], row[1])


@router.get("/matches", response_model=MatchPage)
async def matches(
    request: Request,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    other_id = case((Lobby.user_low_id == current_user.id, Lobby.user_high_id), else_=Lobby.user_low_id)
    base = select(Lobby).where(
        or_(Lobby.user_low_id == current_user.id, Lobby.user_high_id == current_user.id), Lobby.is_active.is_(True)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = (
        await session.execute(
            select(User, CS2Profile, Lobby)
            .join(Lobby, User.id == other_id)
            .join(CS2Profile, CS2Profile.user_id == User.id)
            .where(
                or_(Lobby.user_low_id == current_user.id, Lobby.user_high_id == current_user.id),
                Lobby.is_active.is_(True),
            )
            .order_by(Lobby.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    items = []
    for user, profile, lobby in rows:
        player = await details(request, user, profile)
        is_new = lobby.low_seen_at is None if current_user.id == lobby.user_low_id else lobby.high_seen_at is None
        items.append(MatchItem(**player.model_dump(), is_new_match=is_new, matched_at=lobby.created_at))
        if current_user.id == lobby.user_low_id and lobby.low_seen_at is None:
            lobby.low_seen_at = func.now()
        elif current_user.id == lobby.user_high_id and lobby.high_seen_at is None:
            lobby.high_seen_at = func.now()
    if rows:
        await session.commit()
    return MatchPage(items=items, page=page, page_size=page_size, total=total)


@router.post("/swipe", response_model=SwipeResponse)
async def swipe(
    payload: SwipeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    await rate_limit(request, f"swipe:{current_user.id}", 60, 60)
    if payload.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot swipe yourself")
    own = await own_profile(current_user, session)
    target_row = (
        await session.execute(select(User, CS2Profile).join(CS2Profile).where(User.id == payload.target_user_id))
    ).first()
    if target_row is None:
        raise HTTPException(status_code=404, detail="Player profile not found")
    target, target_profile = target_row
    if not target_profile.is_searching:
        raise HTTPException(status_code=409, detail="Player is no longer searching")
    elo_min = max(own.filter_elo_min, own.elo - own.max_elo_difference)
    elo_max = min(own.filter_elo_max, own.elo + own.max_elo_difference)
    eligible = elo_min <= target_profile.elo <= elo_max
    eligible = eligible and (not own.filter_roles or target_profile.primary_role in own.filter_roles)
    eligible = eligible and (not own.filter_language or own.filter_language in (target_profile.languages or []))
    eligible = eligible and (not own.filter_schedule or own.filter_schedule == target_profile.schedule)
    if own.online_only and not await online(request, target.id):
        eligible = False
    if not eligible:
        raise HTTPException(status_code=409, detail="Player no longer matches your search filters")
    direction = SwipeDirection(payload.direction)
    low, high = sorted((current_user.id, target.id))
    pair_lock = (low << 32) | high
    await session.execute(select(func.pg_advisory_xact_lock(pair_lock)))
    await session.execute(
        insert(Swipe)
        .values(from_user_id=current_user.id, to_user_id=target.id, direction=direction)
        .on_conflict_do_update(constraint="uq_swipe_pair", set_={"direction": direction})
    )
    matched = False
    new_match = False
    if direction == SwipeDirection.like:
        matched = bool(
            await session.scalar(
                select(Swipe.id).where(
                    Swipe.from_user_id == target.id,
                    Swipe.to_user_id == current_user.id,
                    Swipe.direction == SwipeDirection.like,
                )
            )
        )
        if matched:
            new_match = (
                await session.execute(
                    insert(Lobby)
                    .values(user_low_id=low, user_high_id=high)
                    .on_conflict_do_nothing(constraint="uq_lobby_pair")
                    .returning(Lobby.id)
                )
            ).scalar_one_or_none() is not None
    await session.commit()
    match_data = await details(request, target, target_profile) if matched else None
    if new_match:
        background_tasks.add_task(send_match_notifications, current_user, target)
    return SwipeResponse(matched=matched, new_match=new_match, match=match_data)


@router.get("/statistics/me", response_model=Statistics)
async def my_statistics(request: Request, current_user: CurrentUser, session: AsyncSession = Depends(get_session)):
    profile = await own_profile(current_user, session)
    extra = await FaceitService(request.app.state.redis, request.app.state.http).statistics(profile.faceit_player_id)
    return stats(profile, recent_form=extra["recent_form"], maps=extra["map_distribution"])
