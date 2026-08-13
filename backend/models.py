import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class SwipeDirection(str, enum.Enum):
    like = "like"
    dislike = "dislike"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped["CS2Profile | None"] = relationship(back_populates="user", cascade="all, delete-orphan")


class CS2Profile(Base):
    __tablename__ = "cs2_profiles"
    __table_args__ = (
        Index("ix_profiles_search_elo", "is_searching", "elo", "user_id"),
        Index("ix_profiles_search_role", "is_searching", "primary_role", "elo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    faceit_player_id: Mapped[str] = mapped_column(String(64), unique=True)
    faceit_nickname: Mapped[str] = mapped_column(String(64), index=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    elo: Mapped[int] = mapped_column(Integer, index=True)
    skill_level: Mapped[int] = mapped_column(Integer)
    kd_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    adr: Mapped[float | None] = mapped_column(Float, nullable=True)
    hs_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    win_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    matches_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    primary_role: Mapped[str] = mapped_column(String(32), default="Rifler")
    secondary_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    playstyle: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bio: Mapped[str] = mapped_column(String(500), default="")
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_maps: Mapped[list[str]] = mapped_column(JSON, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    microphone: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    schedule: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    filter_elo_min: Mapped[int] = mapped_column(Integer, default=0)
    filter_elo_max: Mapped[int] = mapped_column(Integer, default=4000)
    max_elo_difference: Mapped[int] = mapped_column(Integer, default=250)
    filter_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    filter_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    filter_schedule: Mapped[str | None] = mapped_column(String(80), nullable=True)
    online_only: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_swipe_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    direction: Mapped[SwipeDirection] = mapped_column(Enum(SwipeDirection, name="swipe_direction"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Lobby(Base):
    __tablename__ = "lobbies"
    __table_args__ = (UniqueConstraint("user_low_id", "user_high_id", name="uq_lobby_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_low_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user_high_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    low_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    high_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GameId(str, enum.Enum):
    cs2 = "cs2"
    valorant = "valorant"
    standoff2 = "standoff2"


class PartyStatus(str, enum.Enum):
    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class PartyMemberRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class PartyRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    bio: Mapped[str] = mapped_column(String(500), default="")
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    microphone: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    playstyle: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_schedule: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GameProfile(Base):
    __tablename__ = "game_profiles"
    __table_args__ = (UniqueConstraint("user_id", "game", name="uq_game_profile_user_game"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    game: Mapped[GameId] = mapped_column(Enum(GameId, name="game_id"), index=True)
    nickname: Mapped[str] = mapped_column(String(64))
    primary_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    secondary_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rank_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rank_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Party(Base):
    __tablename__ = "parties"
    __table_args__ = (Index("ix_parties_discover", "game", "status", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    game: Mapped[GameId] = mapped_column(Enum(GameId, name="game_id"), index=True)
    title: Mapped[str] = mapped_column(String(80))
    mode: Mapped[str] = mapped_column(String(32), index=True)
    capacity: Mapped[int] = mapped_column(Integer)
    vibe: Mapped[int] = mapped_column(Integer, default=50)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    mic_required: Mapped[bool] = mapped_column(Boolean, default=False)
    rank_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[PartyStatus] = mapped_column(
        Enum(PartyStatus, name="party_status"), default=PartyStatus.OPEN, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    members: Mapped[list["PartyMember"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class PartyMember(Base):
    __tablename__ = "party_members"
    __table_args__ = (UniqueConstraint("party_id", "user_id", name="uq_party_member"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[PartyMemberRole] = mapped_column(Enum(PartyMemberRole, name="party_member_role"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship(lazy="joined")


class PartyRequest(Base):
    __tablename__ = "party_requests"
    __table_args__ = (UniqueConstraint("party_id", "requester_user_id", name="uq_party_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    requester_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[PartyRequestStatus] = mapped_column(
        Enum(PartyRequestStatus, name="party_request_status"), default=PartyRequestStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    party: Mapped[Party] = relationship(lazy="joined")
    requester: Mapped[User] = relationship(lazy="joined")
