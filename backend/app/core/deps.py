"""
FastAPI dependencies.

get_current_user now:
1. Reads tenant_slug from request.state (set by TenantMiddleware)
2. Sets DB search_path to that tenant's schema
3. Validates the user exists in that schema
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal, get_tenant_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from typing import AsyncGenerator

bearer = HTTPBearer()


async def get_tenant_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Provides a DB session scoped to the current tenant's schema."""
    slug = getattr(request.state, "tenant_slug", None)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context. Use subdomain or X-Tenant-Slug header."
        )
    async for session in get_tenant_db(slug)():
        yield session


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_tenant_session),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    tenant_slug = payload.get("tenant")

    # Verify token's tenant matches request's tenant
    request_tenant = getattr(request.state, "tenant_slug", None)
    if tenant_slug and request_tenant and tenant_slug != request_tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tenant mismatch")

    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker


async def get_current_tenant(request: Request) -> Tenant:
    """Returns the Tenant object for the current request."""
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        raise HTTPException(status_code=400, detail="No tenant context")
    return tenant
