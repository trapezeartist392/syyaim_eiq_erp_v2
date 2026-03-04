"""
Tenant middleware.

Extracts tenant slug from:
  1. Subdomain: acme.syyaimeiq.com -> slug = "acme"
  2. Header X-Tenant-Slug (for API clients / local dev)

Validates the tenant is active, stores it in request.state.tenant_slug
so downstream dependencies can set the correct DB search_path.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant, TenantStatus
from app.core.config import settings
import re


# Paths that don't need a tenant (public signup, webhooks, health)
PUBLIC_PATHS = {
    "/api/health",
    "/api/v1/public/signup",
    "/api/v1/public/check-slug",
    "/api/v1/billing/webhook",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/v1/superadmin",
}


class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Skip tenant resolution for public paths
        path = request.url.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            request.state.tenant_slug = None
            return await call_next(request)

        # Resolve slug from subdomain or header
        slug = self._extract_slug(request)

        if not slug:
            # No tenant context — allow through (will fail at auth if protected)
            request.state.tenant_slug = None
            return await call_next(request)

        # Validate tenant exists and is active
        try:
            tenant = await self._get_tenant(slug)
        except Exception:
            return self._error(503, "Service temporarily unavailable")

        if not tenant:
            return self._error(404, f"Tenant '{slug}' not found")

        if tenant.status == TenantStatus.SUSPENDED:
            return self._error(402, "Account suspended. Please contact support.")

        if tenant.status == TenantStatus.CANCELLED:
            return self._error(410, "Account cancelled.")

        request.state.tenant_slug = tenant.slug
        request.state.tenant = tenant
        return await call_next(request)

    def _extract_slug(self, request: Request) -> str | None:
        # 1. Check X-Tenant-Slug header (dev/API use)
        header_slug = request.headers.get("X-Tenant-Slug")
        if header_slug:
            return header_slug.lower().strip()

        # 2. Extract from subdomain
        host = request.headers.get("host", "")
        # Remove port if present
        host = host.split(":")[0]
        base = settings.BASE_DOMAIN

        if host.endswith(f".{base}"):
            subdomain = host[: -(len(base) + 1)]
            # Ignore www, api, admin etc.
            if subdomain and subdomain not in ("www", "api", "admin", "app"):
                return subdomain.lower()

        return None

    async def _get_tenant(self, slug: str) -> Tenant | None:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SET search_path TO public"))
            result = await session.execute(
                select(Tenant).where(Tenant.slug == slug)
            )
            return result.scalar_one_or_none()

    def _error(self, code: int, message: str):
        from starlette.responses import JSONResponse
        return JSONResponse(status_code=code, content={"detail": message})
