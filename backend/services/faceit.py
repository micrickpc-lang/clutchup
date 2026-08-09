import json

import httpx
from fastapi import HTTPException
from redis.asyncio import Redis

from config import settings


BASE_URL = (
    f"{settings.faceit_proxy_url.rstrip('/')}/data/v4"
    if settings.faceit_proxy_url
    else "https://open.faceit.com/data/v4"
)


class FaceitService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict:
        cache_key = f"faceit:{path}:{json.dumps(params or {}, sort_keys=True)}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {settings.faceit_api_key}"}
            if settings.faceit_proxy_secret:
                headers["X-ClutchUp-Proxy-Secret"] = settings.faceit_proxy_secret
            response = await client.get(
                f"{BASE_URL}{path}",
                params=params,
                headers=headers,
            )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="FACEIT player not found")
        if response.is_error:
            raise HTTPException(status_code=502, detail="FACEIT API is temporarily unavailable")
        data = response.json()
        await self.redis.setex(cache_key, 300, json.dumps(data))
        return data

    async def get_player_profile(self, nickname: str) -> dict:
        player = await self._get("/players", {"nickname": nickname, "game": "cs2"})
        stats = await self._get(f"/players/{player['player_id']}/stats/cs2")
        cs2 = player.get("games", {}).get("cs2", {})
        lifetime = stats.get("lifetime", {})
        return {
            "player_id": player["player_id"],
            "nickname": player.get("nickname", nickname),
            "avatar": player.get("avatar") or None,
            "elo": int(cs2.get("faceit_elo", 0)),
            "skill_level": int(cs2.get("skill_level", 0)),
            "kd_ratio": float(lifetime.get("Average K/D Ratio", 0) or 0),
        }

    async def get_player_profile_by_id(self, player_id: str) -> dict:
        player = await self._get(f"/players/{player_id}")
        return await self.get_player_profile(player["nickname"])
