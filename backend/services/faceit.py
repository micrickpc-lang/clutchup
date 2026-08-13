import asyncio
import json
from typing import Any

import httpx
from fastapi import HTTPException
from redis.asyncio import Redis

from config import settings

BASE_URL = (
    f"{settings.faceit_proxy_url.rstrip('/')}/data/v4"
    if settings.faceit_proxy_url
    else "https://open.faceit.com/data/v4"
)


def number(value: Any, *, integer: bool = False) -> int | float | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value)) if integer else float(value)
    except (TypeError, ValueError):
        return None


class FaceitService:
    def __init__(self, redis: Redis, client: httpx.AsyncClient):
        self.redis = redis
        self.client = client

    async def _get(self, path: str, params: dict[str, str] | None = None, ttl: int | None = None) -> dict[str, Any]:
        cache_key = f"faceit:{path}:{json.dumps(params or {}, sort_keys=True)}"
        cached = await self.redis.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                await self.redis.delete(cache_key)
        headers = {"Authorization": f"Bearer {settings.faceit_api_key}"}
        if settings.faceit_proxy_secret:
            headers["X-ClutchUp-Proxy-Secret"] = settings.faceit_proxy_secret
        response: httpx.Response | None = None
        for attempt in range(2):
            try:
                response = await self.client.get(f"{BASE_URL}{path}", params=params, headers=headers)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == 0:
                    await asyncio.sleep(0.15)
                    continue
                raise HTTPException(status_code=503, detail="FACEIT API is unavailable") from exc
            if response.status_code not in {429, 502, 503, 504} or attempt:
                break
            await asyncio.sleep(0.2)
        assert response is not None
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="FACEIT player not found")
        if response.status_code == 429:
            raise HTTPException(status_code=503, detail="FACEIT rate limit reached")
        if response.is_error:
            raise HTTPException(status_code=502, detail="FACEIT API returned an error")
        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="FACEIT returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise HTTPException(status_code=502, detail="FACEIT returned an invalid response")
        await self.redis.setex(cache_key, ttl or settings.faceit_cache_ttl_seconds, json.dumps(data))
        return data

    async def _normalize_player(self, player: dict[str, Any]) -> dict[str, Any]:
        player_id = str(player.get("player_id") or "")
        if not player_id:
            raise HTTPException(status_code=502, detail="FACEIT player id is missing")
        stats = await self._get(f"/players/{player_id}/stats/cs2")
        lifetime = stats.get("lifetime") if isinstance(stats.get("lifetime"), dict) else {}
        games = player.get("games") if isinstance(player.get("games"), dict) else {}
        cs2 = games.get("cs2") if isinstance(games.get("cs2"), dict) else {}
        return {
            "player_id": player_id,
            "nickname": str(player.get("nickname") or "Unknown")[:64],
            "avatar": player.get("avatar") or None,
            "country_code": str(player.get("country") or "").upper()[:2] or None,
            "elo": number(cs2.get("faceit_elo"), integer=True) or 0,
            "skill_level": number(cs2.get("skill_level"), integer=True) or 0,
            "kd_ratio": number(lifetime.get("Average K/D Ratio")),
            "adr": number(lifetime.get("ADR") or lifetime.get("Average ADR")),
            "hs_percent": number(lifetime.get("Average Headshots %")),
            "win_rate": number(lifetime.get("Win Rate %")),
            "matches_count": number(lifetime.get("Matches"), integer=True),
        }

    async def get_player_profile(self, nickname: str) -> dict[str, Any]:
        return await self._normalize_player(await self._get("/players", {"nickname": nickname, "game": "cs2"}))

    async def get_player_profile_by_id(self, player_id: str) -> dict[str, Any]:
        return await self._normalize_player(await self._get(f"/players/{player_id}"))

    async def statistics(self, player_id: str) -> dict[str, Any]:
        history = await self._get(
            f"/players/{player_id}/history", {"game": "cs2", "offset": "0", "limit": "20"}, ttl=180
        )
        items = history.get("items") if isinstance(history.get("items"), list) else []
        recent_form: list[str] = []
        for item in items[:20]:
            result = item.get("results") if isinstance(item, dict) and isinstance(item.get("results"), dict) else {}
            winner = result.get("winner")
            faction = item.get("faction") if isinstance(item, dict) else None
            if winner in {"faction1", "faction2"} and faction in {"faction1", "faction2"}:
                recent_form.append("W" if winner == faction else "L")
        return {"recent_form": recent_form, "map_distribution": {}, "recent_matches": items[:20]}
