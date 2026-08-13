import base64
import hashlib
import json
import logging
import secrets
import time
import uuid
from html import escape
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from config import settings
from database import get_session
from models import CS2Profile
from schemas import OAuthStartResponse
from services.faceit import FaceitService
from services.rate_limit import rate_limit

router = APIRouter(prefix="/faceit/oauth")
logger = logging.getLogger(__name__)

# Official FACEIT OIDC discovery: https://api.faceit.com/auth/v1/openid_configuration
AUTHORIZE_URL = "https://accounts.faceit.com"
OAUTH_API_ORIGIN = settings.faceit_proxy_url.rstrip("/") if settings.faceit_proxy_url else "https://api.faceit.com"
TOKEN_URL = f"{OAUTH_API_ORIGIN}/auth/v1/oauth/token"
USERINFO_URL = f"{OAUTH_API_ORIGIN}/auth/v1/resources/userinfo"
STATE_PREFIX = "faceit_oauth:"
LOCK_PREFIX = "faceit_oauth_processing:"
USED_PREFIX = "faceit_oauth_used:"

CLAIM_SCRIPT = """
if redis.call('EXISTS', KEYS[3]) == 1 then return {-2, ''} end
local value = redis.call('GET', KEYS[1])
if not value then return {0, ''} end
if not redis.call('SET', KEYS[2], ARGV[1], 'NX', 'EX', ARGV[2]) then return {-1, ''} end
return {1, value}
"""
RELEASE_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end
return 0
"""
FINISH_SCRIPT = """
if redis.call('GET', KEYS[2]) ~= ARGV[1] then return 0 end
redis.call('DEL', KEYS[1], KEYS[2])
redis.call('SET', KEYS[3], '1', 'EX', ARGV[2])
return 1
"""


class OAuthFlowError(Exception):
    def __init__(self, stage: str, user_message: str, status_code: int = 502):
        super().__init__(stage)
        self.stage = stage
        self.user_message = user_message
        self.status_code = status_code


def proxy_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if settings.faceit_proxy_url and settings.faceit_proxy_secret:
        headers["X-ClutchUp-Proxy-Secret"] = settings.faceit_proxy_secret
    return headers


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def pkce_challenge(verifier: str) -> str:
    return b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def authorization_url(state: str, verifier: str) -> str:
    query = urlencode(
        {
            "client_id": settings.faceit_client_id,
            "redirect_uri": settings.faceit_redirect_uri,
            "response_type": "code",
            "scope": "openid profile",
            "state": state,
            "code_challenge": pkce_challenge(verifier),
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def safe_error(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    fields: dict[str, Any] = {}
    try:
        body = response.json()
        if isinstance(body, dict):
            for key in ("error", "error_description", "message", "code"):
                value = body.get(key)
                if isinstance(value, str | int | float | bool):
                    fields[key] = str(value)[:160]
    except ValueError:
        pass
    return f"content_type={content_type or 'unknown'} fields={fields or 'none'}"


async def exchange_token(client: httpx.AsyncClient, code: str, verifier: str, request_id: str) -> str:
    logger.info("oauth.token.request request_id=%s", request_id)
    try:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.faceit_redirect_uri,
                "code_verifier": verifier,
            },
            auth=httpx.BasicAuth(settings.faceit_client_id, settings.faceit_client_secret),
            headers=proxy_headers(),
        )
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.warning("oauth.token.failed network_error=%s request_id=%s", type(exc).__name__, request_id)
        raise OAuthFlowError("token", "FACEIT временно недоступен. Попробуйте снова.", 503) from exc
    if response.is_error:
        logger.warning(
            "oauth.token.failed status=%s %s request_id=%s",
            response.status_code,
            safe_error(response),
            request_id,
        )
        status = 503 if response.status_code in {429, 500, 502, 503, 504} else 400
        raise OAuthFlowError("token", "Не удалось подключить FACEIT. Начните вход заново.", status)
    try:
        payload = response.json()
    except ValueError as exc:
        logger.warning("oauth.token.invalid_json status=%s request_id=%s", response.status_code, request_id)
        raise OAuthFlowError("token", "FACEIT вернул некорректный ответ.") from exc
    access_token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access_token, str) or not access_token:
        logger.warning("oauth.token.missing_access_token request_id=%s", request_id)
        raise OAuthFlowError("token", "FACEIT не выдал токен доступа.")
    logger.info("oauth.token.success request_id=%s", request_id)
    return access_token


async def fetch_userinfo(client: httpx.AsyncClient, access_token: str, request_id: str) -> dict[str, Any]:
    try:
        response = await client.get(
            USERINFO_URL,
            headers={**proxy_headers(), "Authorization": f"Bearer {access_token}"},
        )
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.warning("oauth.userinfo.failed network_error=%s request_id=%s", type(exc).__name__, request_id)
        raise OAuthFlowError("userinfo", "Не удалось получить профиль FACEIT.", 503) from exc
    if response.is_error:
        logger.warning(
            "oauth.userinfo.failed status=%s %s request_id=%s",
            response.status_code,
            safe_error(response),
            request_id,
        )
        raise OAuthFlowError("userinfo", "Не удалось получить профиль FACEIT.")
    try:
        identity = response.json()
    except ValueError as exc:
        raise OAuthFlowError("userinfo", "FACEIT вернул некорректный профиль.") from exc
    if not isinstance(identity, dict):
        raise OAuthFlowError("userinfo", "FACEIT вернул некорректный профиль.")
    logger.info("oauth.userinfo.success request_id=%s", request_id)
    return identity


async def claim_state(redis: Any, state: str, request_id: str) -> tuple[int, str]:
    result = await redis.eval(
        CLAIM_SCRIPT,
        3,
        f"{STATE_PREFIX}{state}",
        f"{LOCK_PREFIX}{state}",
        f"{USED_PREFIX}{state}",
        request_id,
        90,
    )
    return int(result[0]), str(result[1] or "")


async def release_state(redis: Any, state: str, request_id: str) -> None:
    await redis.eval(RELEASE_SCRIPT, 1, f"{LOCK_PREFIX}{state}", request_id)


async def finish_state(redis: Any, state: str, request_id: str) -> None:
    completed = await redis.eval(
        FINISH_SCRIPT,
        3,
        f"{STATE_PREFIX}{state}",
        f"{LOCK_PREFIX}{state}",
        f"{USED_PREFIX}{state}",
        request_id,
        settings.oauth_state_ttl_seconds,
    )
    if not completed:
        raise OAuthFlowError("state", "Не удалось завершить OAuth-сессию.", 409)


@router.post("/start", response_model=OAuthStartResponse)
async def start_oauth(request: Request, current_user: CurrentUser) -> OAuthStartResponse:
    if settings.environment == "production" and not all(
        (settings.faceit_client_id, settings.faceit_client_secret, settings.faceit_redirect_uri)
    ):
        raise HTTPException(status_code=503, detail="FACEIT integration is not configured")
    await rate_limit(request, f"oauth:{current_user.id}", 6, 600)
    request_id = uuid.uuid4().hex
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    payload = {"user_id": current_user.id, "code_verifier": verifier, "created_at": int(time.time())}
    await request.app.state.redis.set(
        f"{STATE_PREFIX}{state}", json.dumps(payload), ex=settings.oauth_state_ttl_seconds, nx=True
    )
    logger.info("oauth.start user_id=%s request_id=%s", current_user.id, request_id)
    return OAuthStartResponse(authorization_url=authorization_url(state, verifier))


def telegram_return_url() -> str:
    base = f"https://t.me/{settings.telegram_bot_username}"
    if settings.telegram_mini_app_short_name:
        base += f"/{settings.telegram_mini_app_short_name}"
    return f"{base}?startapp=faceit_connected"


def result_page(title: str, message: str, *, success: bool, status_code: int = 200) -> HTMLResponse:
    origin_json = json.dumps(settings.frontend_url)
    signal = "clutchup-faceit-connected" if success else "clutchup-faceit-error"
    return HTMLResponse(
        f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>body{{margin:0;display:grid;min-height:100dvh;place-items:center;background:#070b10;color:#f4f4f5;font:16px Inter,system-ui;text-align:center}}main{{width:min(420px,calc(100% - 32px));padding:32px}}p{{color:#a1a1aa;line-height:1.55}}a{{display:block;margin-top:24px;padding:14px;border-radius:12px;background:#7c3aed;color:white;text-decoration:none;font-weight:700}}</style></head><body><main><h1>{escape(title)}</h1><p>{escape(message)}</p><a href="{escape(telegram_return_url())}">Вернуться в ClutchUp</a></main><script>try{{if(window.opener&&!window.opener.closed){{window.opener.postMessage({{type:'{signal}'}},{origin_json})}}}}catch(e){{}}</script></body></html>""",
        status_code=status_code,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'",
        },
    )


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = Query(None, max_length=100),
    error_description: str | None = Query(None, max_length=300),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    request_id = uuid.uuid4().hex
    logger.info("oauth.callback.received has_state=%s has_code=%s request_id=%s", bool(state), bool(code), request_id)
    if error:
        logger.warning(
            "oauth.callback.denied error=%s description=%s request_id=%s",
            error[:80],
            (error_description or "")[:120],
            request_id,
        )
        if state:
            await request.app.state.redis.delete(f"{STATE_PREFIX}{state}")
        return result_page(
            "FACEIT не подключён",
            "Доступ был отменён или отклонён. Вернитесь в ClutchUp и попробуйте снова.",
            success=False,
            status_code=400,
        )
    if not state:
        return result_page(
            "Некорректный ответ FACEIT",
            "В ответе отсутствует OAuth state. Начните вход заново.",
            success=False,
            status_code=400,
        )
    claim, stored = await claim_state(request.app.state.redis, state, request_id)
    if claim == 0:
        return result_page(
            "Сессия FACEIT устарела", "Вернитесь в ClutchUp и попробуйте снова.", success=False, status_code=400
        )
    if claim in {-1, -2}:
        return result_page(
            "Сессия уже обрабатывается",
            "Этот ответ FACEIT уже был использован. Вернитесь в ClutchUp.",
            success=False,
            status_code=409,
        )
    try:
        oauth = json.loads(stored)
        verifier = oauth["code_verifier"]
        user_id = int(oauth["user_id"])
        created_at = int(oauth["created_at"])
        if not isinstance(verifier, str) or not 43 <= len(verifier) <= 128:
            raise ValueError("invalid verifier")
        if int(time.time()) - created_at > settings.oauth_state_ttl_seconds + 5:
            raise ValueError("expired payload")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        await release_state(request.app.state.redis, state, request_id)
        return result_page(
            "OAuth-сессия повреждена", "Вернитесь в ClutchUp и начните вход заново.", success=False, status_code=400
        )
    logger.info("oauth.state.validated user_id=%s request_id=%s", user_id, request_id)
    if not code:
        await release_state(request.app.state.redis, state, request_id)
        return result_page(
            "Некорректный ответ FACEIT", "FACEIT не вернул authorization code.", success=False, status_code=400
        )
    client: httpx.AsyncClient = request.app.state.http
    try:
        access_token = await exchange_token(client, code, verifier, request_id)
        identity = await fetch_userinfo(client, access_token, request_id)
        player_id = identity.get("guid") or identity.get("sub")
        if not isinstance(player_id, str) or not player_id:
            logger.warning(
                "oauth.userinfo.missing_player_id claim_keys=%s request_id=%s", sorted(identity.keys()), request_id
            )
            raise OAuthFlowError("userinfo", "FACEIT не вернул идентификатор игрока.")
        logger.info("oauth.profile.fetch request_id=%s", request_id)
        try:
            faceit = await FaceitService(request.app.state.redis, client).get_player_profile_by_id(player_id)
        except HTTPException as exc:
            logger.warning("oauth.profile.partial status=%s request_id=%s", exc.status_code, request_id)
            nickname = (
                identity.get("nickname")
                or identity.get("preferred_username")
                or identity.get("given_name")
                or "FACEIT Player"
            )
            faceit = {
                "player_id": player_id,
                "nickname": str(nickname)[:64],
                "avatar": identity.get("picture") if isinstance(identity.get("picture"), str) else None,
                "country_code": None,
                "elo": 0,
                "skill_level": 0,
                "kd_ratio": None,
                "adr": None,
                "hs_percent": None,
                "win_rate": None,
                "matches_count": None,
            }
        owner = await session.scalar(
            select(CS2Profile.user_id).where(CS2Profile.faceit_player_id == player_id, CS2Profile.user_id != user_id)
        )
        if owner:
            await finish_state(request.app.state.redis, state, request_id)
            return result_page(
                "Аккаунт уже используется",
                "Этот FACEIT аккаунт подключён к другому профилю ClutchUp.",
                success=False,
                status_code=409,
            )
        profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == user_id))
        values = {
            "faceit_player_id": faceit["player_id"],
            "faceit_nickname": faceit["nickname"],
            "avatar_url": faceit["avatar"],
            "country_code": faceit["country_code"],
            "elo": faceit["elo"],
            "skill_level": faceit["skill_level"],
            "kd_ratio": faceit["kd_ratio"],
            "adr": faceit["adr"],
            "hs_percent": faceit["hs_percent"],
            "win_rate": faceit["win_rate"],
            "matches_count": faceit["matches_count"],
        }
        if profile is None:
            session.add(CS2Profile(user_id=user_id, primary_role="Rifler", is_searching=True, **values))
        else:
            for name, value in values.items():
                setattr(profile, name, value)
        await session.commit()
        logger.info("oauth.db.link user_id=%s request_id=%s", user_id, request_id)
        await finish_state(request.app.state.redis, state, request_id)
    except IntegrityError:
        await session.rollback()
        await finish_state(request.app.state.redis, state, request_id)
        logger.warning("oauth.db.duplicate user_id=%s request_id=%s", user_id, request_id)
        return result_page(
            "Аккаунт уже используется", "Этот FACEIT аккаунт уже подключён.", success=False, status_code=409
        )
    except OAuthFlowError as exc:
        await session.rollback()
        await release_state(request.app.state.redis, state, request_id)
        logger.warning("oauth.failed stage=%s request_id=%s", exc.stage, request_id)
        return result_page("Не удалось подключить FACEIT", exc.user_message, success=False, status_code=exc.status_code)
    logger.info("oauth.completed user_id=%s request_id=%s", user_id, request_id)
    return result_page(
        "FACEIT подключён", "Профиль сохранён. Вернитесь в ClutchUp — приложение обновится автоматически.", success=True
    )
