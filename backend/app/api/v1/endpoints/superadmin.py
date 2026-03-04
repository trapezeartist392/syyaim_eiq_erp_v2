"""
Super Admin endpoints — internal use only.

Secured by SUPERADMIN_SECRET header (set in .env).
Accessible at /api/v1/superadmin/...

Endpoints:
GET  /tenants        — list all tenants
GET  /tenants/{slug} — tenant detail
POST /tenants/{slug}/suspend
POST /tenants/{slug}/activate
DELETE /tenants/{slug}
GET  /metrics        — MRR, churn, active tenants
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.core.database import get_public_db, drop_tenant_schema
from app.models.tenant import Tenant, TenantStatus
from app.core.config import settings
from datetime import datetime, timezone

router = APIRouter()


async def verify_superadmin(x_superadmin_secret: str = Header(..., alias="X-Superadmin-Secret")):
    """Simple header-based auth for super admin API."""
    if x_superadmin_secret != settings.SUPERADMIN_SECRET:
        raise HTTPException(403, "Invalid superadmin secret")


@router.get("/tenants")
async def list_tenants(
    status: str = None,
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    await db.execute(text("SET search_path TO public"))
    query = select(Tenant).order_by(Tenant.created_at.desc())
    if status:
        query = query.where(Tenant.status == status)
    result = await db.execute(query)
    tenants = result.scalars().all()
    return [_tenant_dict(t) for t in tenants]


@router.get("/tenants/{slug}")
async def get_tenant(
    slug: str,
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    await db.execute(text("SET search_path TO public"))
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, f"Tenant '{slug}' not found")
    return _tenant_dict(tenant)


@router.post("/tenants/{slug}/suspend")
async def suspend_tenant(
    slug: str,
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    tenant = await _get_or_404(slug, db)
    tenant.status = TenantStatus.SUSPENDED
    await db.commit()
    return {"message": f"Tenant '{slug}' suspended"}


@router.post("/tenants/{slug}/activate")
async def activate_tenant(
    slug: str,
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    tenant = await _get_or_404(slug, db)
    tenant.status = TenantStatus.ACTIVE
    await db.commit()
    return {"message": f"Tenant '{slug}' activated"}


@router.delete("/tenants/{slug}")
async def delete_tenant(
    slug: str,
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    tenant = await _get_or_404(slug, db)
    # Drop the tenant's schema
    await drop_tenant_schema(slug)
    # Delete the tenant record
    await db.delete(tenant)
    await db.commit()
    return {"message": f"Tenant '{slug}' deleted permanently"}


@router.get("/metrics")
async def metrics(
    db: AsyncSession = Depends(get_public_db),
    _=Depends(verify_superadmin),
):
    """Key business metrics."""
    await db.execute(text("SET search_path TO public"))

    total = await db.scalar(select(func.count(Tenant.id)))
    active = await db.scalar(
        select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.ACTIVE)
    )
    trial = await db.scalar(
        select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.TRIAL)
    )
    suspended = await db.scalar(
        select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.SUSPENDED)
    )
    cancelled = await db.scalar(
        select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.CANCELLED)
    )

    # MRR = active subscribers × ₹12,999
    mrr = (active or 0) * 12999

    # Trial conversion rate (active / (active + cancelled) if any conversions)
    total_converted_or_lost = (active or 0) + (cancelled or 0)
    conversion_rate = round(
        ((active or 0) / total_converted_or_lost * 100) if total_converted_or_lost > 0 else 0, 1
    )

    return {
        "total_tenants": total,
        "active": active,
        "trial": trial,
        "suspended": suspended,
        "cancelled": cancelled,
        "mrr_inr": mrr,
        "mrr_display": f"₹{mrr:,}",
        "trial_to_paid_rate": f"{conversion_rate}%",
        "arr_inr": mrr * 12,
        "arr_display": f"₹{mrr * 12:,}",
    }


def _tenant_dict(t: Tenant) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "slug": t.slug,
        "email": t.email,
        "phone": t.phone,
        "status": t.status,
        "plan": t.plan,
        "trial_ends_at": t.trial_ends_at,
        "subscription_ends_at": t.subscription_ends_at,
        "stripe_customer_id": t.stripe_customer_id,
        "stripe_subscription_id": t.stripe_subscription_id,
        "ai_actions_used": t.ai_actions_used,
        "ai_actions_limit": t.ai_actions_limit,
        "schema_created": t.schema_created,
        "created_at": t.created_at,
        "erp_url": f"https://{t.slug}.{settings.BASE_DOMAIN}",
    }


async def _get_or_404(slug: str, db: AsyncSession) -> Tenant:
    await db.execute(text("SET search_path TO public"))
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(404, f"Tenant '{slug}' not found")
    return tenant
