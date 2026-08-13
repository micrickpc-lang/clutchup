from fastapi import HTTPException, Request


async def rate_limit(request: Request, key: str, limit: int, window: int) -> None:
    redis_key = f"ratelimit:{key}"
    count = await request.app.state.redis.incr(redis_key)
    if count == 1:
        await request.app.state.redis.expire(redis_key, window)
    if count > limit:
        raise HTTPException(status_code=429, detail="Too many requests")
