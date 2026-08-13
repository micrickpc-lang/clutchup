import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from config import settings
from database import engine
from routers.faceit_oauth import router as faceit_oauth_router
from routers.matching import router as matching_router
from services.bot import bot

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "FACEIT OAuth configuration client_id=yes client_secret=yes redirect_uri=%s proxy_enabled=%s",
        settings.faceit_redirect_uri,
        bool(settings.faceit_proxy_url),
    )
    app.state.settings = settings
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=4.0, read=12.0, write=8.0, pool=4.0),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20, keepalive_expiry=30),
        follow_redirects=False,
        headers={"User-Agent": "ClutchUp/2.0"},
    )
    await app.state.redis.ping()
    yield
    await app.state.http.aclose()
    await app.state.redis.aclose()
    await bot.session.close()
    await engine.dispose()


app = FastAPI(
    title="ClutchUp API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data"],
)


@app.middleware("http")
async def security_and_size(request: Request, call_next):
    size = request.headers.get("content-length")
    if size:
        try:
            if int(size) > 64 * 1024:
                return JSONResponse({"detail": "Request body is too large"}, status_code=413)
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if "Content-Security-Policy" not in response.headers:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors https://web.telegram.org https://*.telegram.org"
        )
    return response


app.include_router(matching_router, prefix="/api", tags=["matching"])
app.include_router(faceit_oauth_router, prefix="/api", tags=["faceit-oauth"])


@app.get("/health")
async def health(request: Request) -> dict[str, str]:
    await request.app.state.redis.ping()
    return {"status": "ok"}
