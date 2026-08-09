from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    faceit_nickname: str = Field(min_length=2, max_length=64)
    role: Literal["Rifler", "AWPer", "IGL", "Support", "Lurker", "Entry"]
    bio: str = Field(default="", max_length=500)
    is_searching: bool = True


class ProfilePreferences(BaseModel):
    role: Literal["Rifler", "AWPer", "IGL", "Support", "Lurker", "Entry"]
    bio: str = Field(default="", max_length=500)
    is_searching: bool = True


class PlayerCard(BaseModel):
    user_id: int
    telegram_username: str | None
    display_name: str
    faceit_nickname: str
    avatar_url: str | None
    elo: int
    skill_level: int
    kd_ratio: float
    role: str
    bio: str


class SwipeRequest(BaseModel):
    target_user_id: int
    direction: Literal["like", "dislike"]


class SwipeResponse(BaseModel):
    matched: bool
    message: str


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faceit_nickname: str
    avatar_url: str | None
    elo: int
    skill_level: int
    kd_ratio: float
    role: str
    bio: str
    is_searching: bool
