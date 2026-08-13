import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from auth import validate_init_data
from config import settings


def signed(*, now: int, user: object | None = None, auth_date: int | None = None) -> str:
    values = {
        "auth_date": str(now if auth_date is None else auth_date),
        "query_id": "test",
        "user": json.dumps(user if user is not None else {"id": 42, "first_name": "Test"}, separators=(",", ":")),
    }
    check = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


def test_valid_init_data():
    assert validate_init_data(signed(now=1_000), now=1_000)["id"] == 42


def test_invalid_signature():
    with pytest.raises(HTTPException, match="signature"):
        value = signed(now=1_000)
        validate_init_data(value[:-1] + ("0" if value[-1] != "0" else "1"), now=1_000)


def test_expired():
    with pytest.raises(HTTPException, match="expired"):
        validate_init_data(signed(now=1_000, auth_date=1), now=settings.auth_max_age_seconds + 2)


def test_future_timestamp():
    with pytest.raises(HTTPException, match="future"):
        validate_init_data(signed(now=2_000), now=1_000)


@pytest.mark.parametrize("user", [{}, {"id": None}, "invalid"])
def test_malformed_user(user):
    with pytest.raises(HTTPException, match="user data"):
        validate_init_data(signed(now=1_000, user=user), now=1_000)
