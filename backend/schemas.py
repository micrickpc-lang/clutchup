from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Role = Literal["Rifler", "AWPer", "IGL", "Support", "Lurker", "Entry"]
Direction = Literal["like", "dislike"]
ALLOWED_MAPS = {"Mirage", "Inferno", "Anubis", "Ancient", "Nuke", "Dust2", "Vertigo", "Overpass"}


class Statistics(BaseModel):
    elo: int = Field(ge=0, le=5000)
    skill_level: int = Field(ge=0, le=10)
    kd_ratio: float | None = None
    adr: float | None = None
    hs_percent: float | None = None
    win_rate: float | None = None
    matches: int | None = None
    recent_form: list[Literal["W", "L"]] = Field(default_factory=list, max_length=20)
    map_distribution: dict[str, int] = Field(default_factory=dict)


class PlayerSummary(BaseModel):
    user_id: int
    telegram_username: str | None
    display_name: str
    faceit_nickname: str
    avatar_url: str | None
    country_code: str | None
    birth_year: int | None
    primary_role: str
    is_online: bool
    is_new_match: bool = False
    statistics: Statistics


class PlayerDetails(PlayerSummary):
    bio: str
    secondary_role: str | None
    playstyle: str | None
    preferred_maps: list[str]
    languages: list[str]
    microphone: bool | None
    schedule: str | None


class SearchPreferences(BaseModel):
    elo_min: int = Field(default=0, ge=0, le=5000)
    elo_max: int = Field(default=4000, ge=0, le=5000)
    max_elo_difference: int = Field(default=250, ge=50, le=1500)
    roles: list[Role] = Field(default_factory=list, max_length=6)
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    schedule: str | None = Field(default=None, max_length=80)
    online_only: bool = False

    @field_validator("elo_max")
    @classmethod
    def elo_order(cls, value: int, info):
        if value < info.data.get("elo_min", 0):
            raise ValueError("elo_max must be greater than or equal to elo_min")
        return value


class ProfileUpdate(BaseModel):
    bio: str = Field(default="", max_length=500)
    primary_role: Role = "Rifler"
    secondary_role: Role | None = None
    playstyle: Literal["Агрессивный", "Сбалансированный", "Тактический"] | None = None
    preferred_maps: list[str] = Field(default_factory=list, max_length=8)
    languages: list[str] = Field(default_factory=list, max_length=6)
    microphone: bool | None = None
    schedule: str | None = Field(default=None, max_length=80)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    birth_year: int | None = Field(default=None, ge=1940, le=datetime.now().year - 13)
    is_searching: bool = True

    @field_validator("preferred_maps")
    @classmethod
    def valid_maps(cls, value: list[str]) -> list[str]:
        if any(item not in ALLOWED_MAPS for item in value):
            raise ValueError("Unsupported map")
        return list(dict.fromkeys(value))

    @field_validator("languages")
    @classmethod
    def valid_languages(cls, value: list[str]) -> list[str]:
        clean = [item.strip().lower() for item in value]
        if any(not 2 <= len(item) <= 16 for item in clean):
            raise ValueError("Invalid language")
        return list(dict.fromkeys(clean))


class ProfileResponse(PlayerDetails):
    is_searching: bool
    preferences: SearchPreferences


class SwipeRequest(BaseModel):
    target_user_id: int = Field(gt=0)
    direction: Direction


class SwipeResponse(BaseModel):
    matched: bool
    new_match: bool
    match: PlayerDetails | None = None


class MatchItem(PlayerSummary):
    matched_at: datetime


class MatchPage(BaseModel):
    items: list[MatchItem]
    page: int
    page_size: int
    total: int


class OAuthStartResponse(BaseModel):
    authorization_url: str


GameName = Literal["cs2", "valorant", "standoff2"]


class UserProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    avatar_url: str | None = Field(default=None, max_length=2048)
    birth_year: int | None = Field(default=None, ge=1940, le=datetime.now().year - 13)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    bio: str = Field(default="", max_length=500)
    languages: list[str] = Field(default_factory=list, max_length=6)
    microphone: bool | None = None
    playstyle: str | None = Field(default=None, max_length=32)
    preferred_schedule: str | None = Field(default=None, max_length=80)


class UserProfileResponse(UserProfileUpdate):
    id: int
    user_id: int
    faceit_connected: bool = False


class GameProfileUpsert(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    primary_role: str | None = Field(default=None, max_length=32)
    secondary_role: str | None = Field(default=None, max_length=32)
    rank_label: str | None = Field(default=None, max_length=64)
    rank_value: int | None = Field(default=None, ge=0, le=100000)
    region: str | None = Field(default=None, max_length=32)
    is_active: bool = True


class GameProfileResponse(GameProfileUpsert):
    id: int
    game: GameName


class PartyCreate(BaseModel):
    game: GameName
    title: str = Field(min_length=2, max_length=80)
    mode: str = Field(min_length=1, max_length=32)
    capacity: int = Field(ge=2, le=10)
    vibe: int = Field(default=50, ge=0, le=100)
    language: str | None = Field(default=None, max_length=16)
    mic_required: bool = False
    rank_min: int | None = Field(default=None, ge=0)
    rank_max: int | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=500)

    @field_validator("rank_max")
    @classmethod
    def valid_rank_range(cls, value: int | None, info):
        minimum = info.data.get("rank_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("rank_max must be greater than or equal to rank_min")
        return value


class PartyMemberResponse(BaseModel):
    user_id: int
    display_name: str
    avatar_url: str | None
    role: Literal["OWNER", "MEMBER"]


class PartyResponse(BaseModel):
    id: int
    owner_user_id: int
    game: GameName
    title: str
    mode: str
    capacity: int
    current_members: int
    free_slots: int
    vibe: int
    language: str | None
    mic_required: bool
    rank_min: int | None
    rank_max: int | None
    description: str
    status: Literal["OPEN", "FULL", "CLOSED", "EXPIRED"]
    created_at: datetime
    expires_at: datetime
    members: list[PartyMemberResponse]
    request_status: Literal["PENDING", "ACCEPTED", "REJECTED", "CANCELLED"] | None = None


class PartyPage(BaseModel):
    items: list[PartyResponse]


class PartyRequestResponse(BaseModel):
    id: int
    party_id: int
    party_title: str
    requester_user_id: int
    requester_name: str
    status: Literal["PENDING", "ACCEPTED", "REJECTED", "CANCELLED"]
    created_at: datetime
