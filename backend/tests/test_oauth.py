import asyncio
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from routers.faceit_oauth import (
    CLAIM_SCRIPT,
    FINISH_SCRIPT,
    RELEASE_SCRIPT,
    OAuthFlowError,
    authorization_url,
    exchange_token,
    fetch_userinfo,
    oauth_callback,
    pkce_challenge,
    start_oauth,
)
from schemas import OAuthStartResponse


class FakeRedis:
    def __init__(self, state: str | None = None):
        self.values = {}
        self.ttls = {}
        if state is not None:
            self.values["faceit_oauth:state"] = state

    async def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    async def expire(self, key, ttl):
        self.ttls[key] = ttl

    async def set(self, key, value, *, ex=None, nx=False):
        if nx and key in self.values:
            return False
        self.values[key], self.ttls[key] = value, ex
        return True

    async def delete(self, key):
        self.values.pop(key, None)

    async def eval(self, script, count, *args):
        keys, argv = args[:count], args[count:]
        if script == CLAIM_SCRIPT:
            session, lock, used = keys
            if used in self.values:
                return [-2, ""]
            if session not in self.values:
                return [0, ""]
            if lock in self.values:
                return [-1, ""]
            self.values[lock] = argv[0]
            return [1, self.values[session]]
        if script == RELEASE_SCRIPT:
            if self.values.get(keys[0]) == argv[0]:
                self.values.pop(keys[0], None)
                return 1
            return 0
        if script == FINISH_SCRIPT:
            if self.values.get(keys[1]) != argv[0]:
                return 0
            self.values.pop(keys[0], None)
            self.values.pop(keys[1], None)
            self.values[keys[2]] = "1"
            return 1
        raise AssertionError("Unexpected Redis script")


def oauth_payload(user_id=1):
    return json.dumps({"user_id": user_id, "code_verifier": "v" * 64, "created_at": int(time.time())})


def response(status=200, payload=None, text=None):
    request = httpx.Request("POST", "https://api.faceit.test")
    if text is not None:
        return httpx.Response(status, text=text, request=request)
    return httpx.Response(status, json=payload, request=request)


def request(redis=None, post=None, get=None):
    client = AsyncMock()
    client.post.return_value = post or response(payload={"access_token": "token"})
    client.get.return_value = get or response(payload={"guid": "faceit-id", "nickname": "Player"})
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=redis or FakeRedis(), http=client)))


def profile_data():
    return {
        "player_id": "faceit-id",
        "nickname": "Player",
        "avatar": None,
        "country_code": None,
        "elo": 2000,
        "skill_level": 9,
        "kd_ratio": 1.1,
        "adr": None,
        "hs_percent": None,
        "win_rate": None,
        "matches_count": 50,
    }


@pytest.mark.asyncio
async def test_oauth_start_creates_state_and_ttl():
    redis = FakeRedis()
    result = await start_oauth(request(redis), SimpleNamespace(id=7))
    assert isinstance(result, OAuthStartResponse)
    key = next(key for key in redis.values if key.startswith("faceit_oauth:"))
    stored = json.loads(redis.values[key])
    assert stored["user_id"] == 7 and "code_verifier" in stored and "created_at" in stored
    assert redis.ttls[key] == 600


def test_pkce_challenge_and_authorize_contract():
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert pkce_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    url = authorization_url("state", verifier)
    assert "code_challenge_method=S256" in url and "response_type=code" in url
    assert "redirect_popup" not in url


@pytest.mark.asyncio
async def test_callback_missing_state():
    result = await oauth_callback(
        request(), code="code", state=None, error=None, error_description=None, session=AsyncMock()
    )
    assert result.status_code == 400


@pytest.mark.asyncio
async def test_callback_invalid_or_expired_state():
    result = await oauth_callback(
        request(), code="code", state="state", error=None, error_description=None, session=AsyncMock()
    )
    assert result.status_code == 400 and "устарела" in result.body.decode()


@pytest.mark.asyncio
async def test_callback_faceit_denied_access():
    redis = FakeRedis(oauth_payload())
    result = await oauth_callback(
        request(redis), code=None, state="state", error="access_denied", error_description="Denied", session=AsyncMock()
    )
    assert result.status_code == 400 and "отменён" in result.body.decode()


@pytest.mark.asyncio
async def test_callback_missing_code_releases_lock():
    redis = FakeRedis(oauth_payload())
    result = await oauth_callback(
        request(redis), code=None, state="state", error=None, error_description=None, session=AsyncMock()
    )
    assert result.status_code == 400 and "faceit_oauth_processing:state" not in redis.values


@pytest.mark.asyncio
async def test_token_exchange_success_uses_basic_and_form():
    client = AsyncMock()
    client.post.return_value = response(payload={"access_token": "secret"})
    assert await exchange_token(client, "code", "v" * 64, "request") == "secret"
    kwargs = client.post.call_args.kwargs
    assert isinstance(kwargs["auth"], httpx.BasicAuth)
    assert kwargs["data"]["redirect_uri"].endswith("/api/faceit/oauth/callback")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 429])
async def test_token_exchange_http_errors(status):
    client = AsyncMock()
    client.post.return_value = response(status, {"error": "invalid_grant"})
    with pytest.raises(OAuthFlowError):
        await exchange_token(client, "code", "v" * 64, "request")


@pytest.mark.asyncio
async def test_token_exchange_timeout():
    client = AsyncMock()
    client.post.side_effect = httpx.ReadTimeout("timeout")
    with pytest.raises(OAuthFlowError, match="token"):
        await exchange_token(client, "code", "v" * 64, "request")


@pytest.mark.asyncio
@pytest.mark.parametrize("payload,text", [(None, "not-json"), ({"token_type": "Bearer"}, None)])
async def test_invalid_token_response(payload, text):
    client = AsyncMock()
    client.post.return_value = response(payload=payload, text=text)
    with pytest.raises(OAuthFlowError):
        await exchange_token(client, "code", "v" * 64, "request")


@pytest.mark.asyncio
async def test_userinfo_failure_and_missing_player_id():
    client = AsyncMock()
    client.get.return_value = response(401, {"error": "invalid_token"})
    with pytest.raises(OAuthFlowError):
        await fetch_userinfo(client, "token", "request")
    redis = FakeRedis(oauth_payload())
    req = request(redis, get=response(payload={"nickname": "Player"}))
    result = await oauth_callback(
        req, code="code", state="state", error=None, error_description=None, session=AsyncMock()
    )
    assert result.status_code == 502


@pytest.mark.asyncio
async def test_existing_faceit_account_returns_409():
    redis, session = FakeRedis(oauth_payload()), AsyncMock()
    session.scalar.return_value = 99
    with patch("routers.faceit_oauth.FaceitService.get_player_profile_by_id", AsyncMock(return_value=profile_data())):
        result = await oauth_callback(
            request(redis), code="code", state="state", error=None, error_description=None, session=session
        )
    assert result.status_code == 409


@pytest.mark.asyncio
async def test_successful_link_and_state_cannot_be_reused():
    redis, session = FakeRedis(oauth_payload()), AsyncMock()
    session.add = Mock()
    session.scalar.side_effect = [None, None]
    with patch("routers.faceit_oauth.FaceitService.get_player_profile_by_id", AsyncMock(return_value=profile_data())):
        first = await oauth_callback(
            request(redis), code="code", state="state", error=None, error_description=None, session=session
        )
        second = await oauth_callback(
            request(redis), code="code", state="state", error=None, error_description=None, session=AsyncMock()
        )
    assert first.status_code == 200 and session.commit.await_count == 1
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_parallel_callback_does_not_process_twice():
    redis = FakeRedis(oauth_payload())
    gate = asyncio.Event()
    client_request = request(redis)

    async def slow_post(*args, **kwargs):
        await gate.wait()
        return response(payload={"access_token": "token"})

    client_request.app.state.http.post.side_effect = slow_post
    session = AsyncMock()
    session.add = Mock()
    session.scalar.side_effect = [None, None]
    with patch("routers.faceit_oauth.FaceitService.get_player_profile_by_id", AsyncMock(return_value=profile_data())):
        first_task = asyncio.create_task(
            oauth_callback(
                client_request, code="code", state="state", error=None, error_description=None, session=session
            )
        )
        await asyncio.sleep(0)
        second = await oauth_callback(
            client_request, code="code", state="state", error=None, error_description=None, session=AsyncMock()
        )
        gate.set()
        first = await first_task
    assert first.status_code == 200 and second.status_code == 409
