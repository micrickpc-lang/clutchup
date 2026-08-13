import hashlib
import hmac
import json
import time
from typing import Annotated, Any
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_session
from models import User


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def validate_init_data(init_data: str, *, now: int | None = None) -> dict[str, Any]:
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise unauthorized("Malformed Telegram initData") from exc
    if len(pairs) != len({key for key, _ in pairs}):
        raise unauthorized("Duplicate Telegram initData fields")
    values = dict(pairs)
    received_hash = values.pop("hash", None)
    if not received_hash or len(received_hash) != 64:
        raise unauthorized("Telegram hash is missing or invalid")
    try:
        auth_date = int(values["auth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise unauthorized("Invalid auth_date") from exc
    current = int(time.time()) if now is None else now
    if auth_date > current + 30:
        raise unauthorized("Telegram initData timestamp is in the future")
    if current - auth_date > settings.auth_max_age_seconds:
        raise unauthorized("Telegram initData has expired")
    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise unauthorized("Invalid Telegram signature")
    try:
        user_data = json.loads(values["user"])
        telegram_id = int(user_data["id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise unauthorized("Telegram user data is invalid") from exc
    if telegram_id <= 0 or not isinstance(user_data, dict):
        raise unauthorized("Telegram user id is invalid")
    return user_data


async def get_current_user(
    x_telegram_init_data: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    if not x_telegram_init_data:
        raise unauthorized("X-Telegram-Init-Data header is required")
    data = validate_init_data(x_telegram_init_data)
    telegram_id = int(data["id"])
    values = {
        "telegram_id": telegram_id,
        "username": data.get("username"),
        "first_name": data.get("first_name") or "Player",
        "last_name": data.get("last_name"),
        "photo_url": data.get("photo_url"),
    }
    stmt = insert(User).values(**values).on_conflict_do_nothing(index_elements=[User.telegram_id])
    result = await session.execute(stmt.returning(User.id))
    created_id = result.scalar_one_or_none()
    if created_id is not None:
        await session.commit()
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        raise HTTPException(status_code=500, detail="Could not create Telegram user")
    changed = False
    for key in ("username", "first_name", "last_name", "photo_url"):
        if getattr(user, key) != values[key]:
            setattr(user, key, values[key])
            changed = True
    if changed:
        await session.commit()
        await session.refresh(user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
