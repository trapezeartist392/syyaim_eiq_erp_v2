"""
Public endpoints — no authentication required.

POST /api/v1/public/signup    — register a new tenant
GET  /api/v1/public/check-slug — check if slug is available
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timezone, timedelta
import re

from app.core.database import get_public_db, create_tenant_schema
from app.core.config import settings
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus
from app.services.billing import BillingService
from app.services.email import send_welcome_email

router = APIRouter()


class SignupRequest(BaseModel):
    company_name: str
    slug: str           # becomes subdomain + schema name
    admin_email: str
    admin_name: str
    password: str
    phone: str = ""

    @validator("slug")
    def validate_slug(cls, v):
        v = v.lower().strip()
        if not re.match(r'^[a-z0-9][a-z0-9\-]{1,30}[a-z0-9]$', v):
            raise ValueError(
                "Slug must be 3-32 characters, lowercase letters, numbers, hyphens only. "
                "Cannot start or end with a hyphen."
            )
        reserved = {"www", "api", "admin", "app", "mail", "smtp", "ftp", "support",
                    "billing", "dashboard", "static", "cdn", "status", "blog"}
        if v in reserved:
            raise ValueError(f"'{v}' is a reserved name")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class SignupResponse(BaseModel):
    tenant_id: int
    slug: str
    erp_url: str
    checkout_url: str | None = None
    message: str


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(
    req: SignupRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_public_db),
):
    # Check slug availability
    existing = await db.execute(
        select(Tenant).where(Tenant.slug == req.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"'{req.slug}' is already taken. Try a different name.")

    # Check email uniqueness
    email_check = await db.execute(
        select(Tenant).where(Tenant.email == req.admin_email)
    )
    if email_check.scalar_one_or_none():
        raise HTTPException(400, "An account with this email already exists.")

    # Create tenant record
    trial_end = datetime.now(timezone.utc) + timedelta(days=settings.TRIAL_DAYS)
    tenant = Tenant(
        name=req.company_name,
        slug=req.slug,
        email=req.admin_email,
        phone=req.phone,
        status=TenantStatus.TRIAL,
        trial_ends_at=trial_end,
        schema_created=False,
    )
    db.add(tenant)
    await db.flush()  # get the id

    # Create Stripe customer
    checkout_url = None
    if settings.STRIPE_SECRET_KEY:
        try:
            customer_id = await BillingService.create_customer(tenant)
            tenant.stripe_customer_id = customer_id

            erp_url = f"https://{req.slug}.{settings.BASE_DOMAIN}"
            checkout_url = await BillingService.create_checkout_session(
                tenant,
                success_url=f"{erp_url}?subscribed=true",
                cancel_url=f"{erp_url}/billing",
            )
        except Exception as e:
            # Don't fail signup if Stripe is misconfigured
            pass

    await db.commit()
    await db.refresh(tenant)

    # Create tenant schema and tables (in background to keep response fast)
    background_tasks.add_task(_provision_tenant, tenant.slug, req)

    return SignupResponse(
        tenant_id=tenant.id,
        slug=req.slug,
        erp_url=f"https://{req.slug}.{settings.BASE_DOMAIN}",
        checkout_url=checkout_url,
        message=f"Account created! Your ERP is being provisioned at {req.slug}.{settings.BASE_DOMAIN}",
    )


async def _provision_tenant(slug: str, req: SignupRequest):
    """
    Background task: create schema + tables + seed admin user.
    Runs after the signup response is sent.
    """
    try:
        # Create schema and all tables
        await create_tenant_schema(slug)

        # Seed admin user in the new schema
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text(f'SET search_path TO "{slug}", public'))
            await session.execute(text("""
                INSERT INTO users (email, full_name, hashed_password, role, department, is_active)
                VALUES (:email, :name, :pwd, 'admin', 'Management', true)
            """), {
                "email": req.admin_email,
                "name": req.admin_name,
                "pwd": hash_password(req.password),
            })
            await session.commit()

        # Mark schema as ready
        async with AsyncSessionLocal() as session:
            await session.execute(text("SET search_path TO public"))
            await session.execute(text(
                "UPDATE tenants SET schema_created = true WHERE slug = :slug"
            ), {"slug": slug})
            await session.commit()

        # Send welcome email
        send_welcome_email(req.admin_email, req.company_name, slug, req.admin_email)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Tenant provisioning failed for {slug}: {e}")


@router.get("/check-slug")
async def check_slug(
    slug: str,
    db: AsyncSession = Depends(get_public_db),
):
    """Check if a slug is available for signup."""
    slug = slug.lower().strip()
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    taken = result.scalar_one_or_none() is not None
    return {
        "slug": slug,
        "available": not taken,
        "url": f"https://{slug}.{settings.BASE_DOMAIN}" if not taken else None,
    }
