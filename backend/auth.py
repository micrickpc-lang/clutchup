import hashlib
import hmac
import json
import time
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_session
from models import User


def validate_init_data(init_data: str) -> dict:
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram hash is missing")

    auth_date_raw = values.get("auth_date")
    try:
        auth_date = int(auth_date_raw or "0")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid auth_date") from exc
    if abs(int(time.time()) - auth_date) > settings.auth_max_age_seconds:
        raise HTTPException(status_code=401, detail="Telegram initData has expired")

    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    try:
        user_data = json.loads(values["user"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Telegram user data is invalid") from exc
    return user_data


async def get_current_user(
    x_telegram_init_data: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="X-Telegram-Init-Data header is required")
    data = validate_init_data(x_telegram_init_data)
    telegram_id = int(data["id"])
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=data.get("username"),
            first_name=data.get("first_name") or "Player",
            last_name=data.get("last_name"),
            photo_url=data.get("photo_url"),
        )
        session.add(user)
    else:
        user.username = data.get("username")
        user.first_name = data.get("first_name") or user.first_name
        user.last_name = data.get("last_name")
        user.photo_url = data.get("photo_url")
    await session.commit()
    await session.refresh(user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

