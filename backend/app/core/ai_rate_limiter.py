# backend/app/core/ai_rate_limiter.py
# Per-tenant AI call rate limiting using Redis
# Limits: 100 calls/day per tenant (configurable per plan)

import json
from datetime import datetime, date
from typing import Optional
import redis.asyncio as aioredis
from fastapi import HTTPException, status

# Plan limits (calls per day)
PLAN_LIMITS = {
    "basic":      50,
    "pro":       200,
    "enterprise": 1000,
    "unlimited":  99999,
    "trial":      20,
}

DEFAULT_PLAN  = "basic"
DEFAULT_LIMIT = PLAN_LIMITS[DEFAULT_PLAN]

redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url("redis://redis:6379", decode_responses=True)
    return redis_client


def _daily_key(tenant_slug: str) -> str:
    """Key resets every day automatically via TTL."""
    today = date.today().isoformat()
    return f"ai_calls:{tenant_slug}:{today}"


def _usage_key(tenant_slug: str) -> str:
    """Cumulative usage stats key (never expires)."""
    return f"ai_usage:{tenant_slug}"


async def check_and_increment(tenant_slug: str, plan: str = DEFAULT_PLAN) -> dict:
    """
    Check if tenant has remaining AI calls for today.
    Increments counter if allowed.
    Raises HTTP 429 if limit exceeded.
    Returns usage info dict.
    """
    r = await get_redis()
    limit = PLAN_LIMITS.get(plan, DEFAULT_LIMIT)
    key = _daily_key(tenant_slug)

    # Get current count
    current = await r.get(key)
    current = int(current) if current else 0

    if current >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "AI rate limit exceeded",
                "tenant": tenant_slug,
                "plan": plan,
                "limit": limit,
                "used": current,
                "remaining": 0,
                "resets_at": "midnight UTC",
                "upgrade_url": "https://syyaimeiq.com/billing"
            }
        )

    # Increment with 25-hour TTL (covers timezone differences)
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 90000)  # 25 hours
    await pipe.execute()

    # Update cumulative stats
    usage_key = _usage_key(tenant_slug)
    today = date.today().isoformat()
    await r.hset(usage_key, today, current + 1)

    return {
        "tenant": tenant_slug,
        "plan": plan,
        "limit": limit,
        "used": current + 1,
        "remaining": limit - (current + 1),
    }


async def get_usage(tenant_slug: str, plan: str = DEFAULT_PLAN) -> dict:
    """Get current usage stats for a tenant without incrementing."""
    r = await get_redis()
    limit = PLAN_LIMITS.get(plan, DEFAULT_LIMIT)
    key = _daily_key(tenant_slug)

    current = await r.get(key)
    current = int(current) if current else 0

    # Get last 7 days history
    history = {}
    for i in range(7):
        from datetime import timedelta
        d = (date.today() - timedelta(days=i)).isoformat()
        val = await r.hget(_usage_key(tenant_slug), d)
        history[d] = int(val) if val else 0

    return {
        "tenant": tenant_slug,
        "plan": plan,
        "limit": limit,
        "used_today": current,
        "remaining_today": max(0, limit - current),
        "last_7_days": history,
    }


async def get_all_tenants_usage() -> list:
    """Superadmin: get usage for all tenants today."""
    r = await get_redis()
    today = date.today().isoformat()
    pattern = f"ai_calls:*:{today}"
    keys = await r.keys(pattern)

    results = []
    for key in keys:
        parts = key.split(":")
        if len(parts) >= 2:
            tenant = parts[1]
            count = await r.get(key)
            results.append({
                "tenant": tenant,
                "used_today": int(count) if count else 0,
            })

    return sorted(results, key=lambda x: x["used_today"], reverse=True)
