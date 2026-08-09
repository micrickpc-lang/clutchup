import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from config import settings
from database import Base, engine
from routers.matching import router as matching_router
from routers.faceit_oauth import router as faceit_oauth_router
from services.bot import bot


logging.basicConfig(level=settings.log_level.upper())


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await app.state.redis.ping()
    yield
    await app.state.redis.aclose()
    await bot.session.close()
    await engine.dispose()


app = FastAPI(title="CS2 Team Finder API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(matching_router, prefix="/api", tags=["matching"])
app.include_router(faceit_oauth_router, prefix="/api", tags=["faceit-oauth"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
