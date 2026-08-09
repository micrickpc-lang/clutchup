import base64
import hashlib
import json
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from config import settings
from database import get_session
from models import CS2Profile
from services.faceit import FaceitService


router = APIRouter(prefix="/faceit/oauth")
AUTHORIZE_URL = "https://accounts.faceit.com"
AUTH_API_BASE = settings.faceit_proxy_url.rstrip("/") if settings.faceit_proxy_url else "https://api.faceit.com"
TOKEN_URL = f"{AUTH_API_BASE}/auth/v1/oauth/token"
USERINFO_URL = f"{AUTH_API_BASE}/auth/v1/resources/userinfo"


def proxy_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if settings.faceit_proxy_secret:
        headers["X-ClutchUp-Proxy-Secret"] = settings.faceit_proxy_secret
    return headers


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def authorization_url(state: str, verifier: str) -> str:
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    query = urlencode(
        {
            "client_id": settings.faceit_client_id,
            "redirect_uri": settings.faceit_redirect_uri,
            "response_type": "code",
            "scope": "openid profile",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "redirect_popup": "true",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


@router.post("/start")
async def start_oauth(request: Request, current_user: CurrentUser) -> dict[str, str]:
    if not settings.faceit_client_id or not settings.faceit_client_secret:
        raise HTTPException(status_code=503, detail="FACEIT OAuth is not configured")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    await request.app.state.redis.setex(
        f"faceit_oauth:{state}",
        600,
        json.dumps({"user_id": current_user.id, "verifier": verifier}),
    )
    return {
        "authorization_url": authorization_url(state, verifier),
        "launch_url": f"{settings.frontend_url}/api/faceit/oauth/launch?state={state}",
    }


@router.get("/launch", response_class=HTMLResponse)
async def oauth_launch(request: Request, state: str):
    stored = await request.app.state.redis.get(f"faceit_oauth:{state}")
    if not stored:
        raise HTTPException(status_code=400, detail="OAuth session expired or invalid")
    verifier = json.loads(stored)["verifier"]
    url_json = json.dumps(authorization_url(state, verifier))
    return HTMLResponse(
        f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Подключение FACEIT</title><style>body{{margin:0;display:grid;min-height:100vh;place-items:center;background:#07101c;color:white;font:16px system-ui;text-align:center}}main{{width:min(420px,calc(100% - 32px));padding:32px;border:1px solid #263548;border-radius:20px;background:#0d1724}}button,a{{display:block;width:100%;box-sizing:border-box;margin-top:20px;padding:15px;border:0;border-radius:12px;background:#ff5500;color:white;font-weight:700;text-decoration:none;cursor:pointer}}</style></head><body><main><h1>Подключить FACEIT</h1><p>Вход откроется на официальном сайте accounts.faceit.com.</p><button id="connect">Продолжить через FACEIT</button><a href="https://t.me/ClutchUp_bot" style="background:#273548">Вернуться в Telegram</a></main><script>const authUrl={url_json};document.getElementById('connect').onclick=()=>{{const popup=window.open(authUrl,'clutchup-faceit','width=750,height=825,resizable=yes,scrollbars=yes');if(!popup)location.href=authUrl}};window.addEventListener('message',event=>{{if(event.origin===location.origin&&event.data?.type==='clutchup-faceit-connected'){{location.href='https://t.me/ClutchUp_bot?startapp=faceit_connected'}}}});</script></body></html>"""
    )


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
):
    key = f"faceit_oauth:{state}"
    stored = await request.app.state.redis.get(key)
    if not stored:
        raise HTTPException(status_code=400, detail="OAuth session expired or invalid")
    await request.app.state.redis.delete(key)
    oauth = json.loads(stored)
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.faceit_redirect_uri,
                "code_verifier": oauth["verifier"],
            },
            auth=(settings.faceit_client_id, settings.faceit_client_secret),
            headers=proxy_headers(),
        )
        if token_response.is_error:
            raise HTTPException(status_code=502, detail="FACEIT token exchange failed")
        access_token = token_response.json()["access_token"]
        user_response = await client.get(
            USERINFO_URL,
            headers={**proxy_headers(), "Authorization": f"Bearer {access_token}"},
        )
        if user_response.is_error:
            raise HTTPException(status_code=502, detail="FACEIT user profile request failed")
    identity = user_response.json()
    player_id = identity.get("sub") or identity.get("guid")
    if not player_id:
        raise HTTPException(status_code=502, detail="FACEIT did not return a player id")
    faceit_data = await FaceitService(request.app.state.redis).get_player_profile_by_id(player_id)
    owner = await session.scalar(
        select(CS2Profile).where(
            CS2Profile.faceit_player_id == faceit_data["player_id"],
            CS2Profile.user_id != oauth["user_id"],
        )
    )
    if owner:
        raise HTTPException(status_code=409, detail="This FACEIT account is already linked")
    profile = await session.scalar(select(CS2Profile).where(CS2Profile.user_id == oauth["user_id"]))
    values = dict(
        faceit_player_id=faceit_data["player_id"],
        faceit_nickname=faceit_data["nickname"],
        avatar_url=faceit_data["avatar"],
        elo=faceit_data["elo"],
        skill_level=faceit_data["skill_level"],
        kd_ratio=faceit_data["kd_ratio"],
        role=profile.role if profile else "Rifler",
        bio=profile.bio if profile else "",
        is_searching=True,
    )
    if profile is None:
        session.add(CS2Profile(user_id=oauth["user_id"], **values))
    else:
        for name, value in values.items():
            setattr(profile, name, value)
    await session.commit()
    return HTMLResponse(
        """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FACEIT подключён</title><style>body{margin:0;display:grid;min-height:100vh;place-items:center;background:#07101c;color:white;font:16px system-ui;text-align:center}a{color:#ff7733}</style></head><body><main><h1>FACEIT подключён</h1><p>Окно закроется автоматически.</p><a href="https://t.me/ClutchUp_bot?startapp=faceit_connected">Вернуться в ClutchUp</a></main><script>if(window.opener){window.opener.postMessage({type:'clutchup-faceit-connected'},'https://clutchup.tech');setTimeout(()=>window.close(),250)}else{setTimeout(()=>location.href='https://t.me/ClutchUp_bot?startapp=faceit_connected',800)}</script></body></html>"""
    )
