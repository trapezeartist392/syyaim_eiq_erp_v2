"""
Billing endpoints (Razorpay).

POST /api/v1/billing/webhook          — Razorpay webhook (public)
POST /api/v1/billing/create-checkout  — Create payment link (auth required)
POST /api/v1/billing/create-subscription — Create recurring subscription (auth required)
POST /api/v1/billing/portal           — Get new payment link for renewal (auth required)
GET  /api/v1/billing/status           — Current subscription status (auth required)
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_public_db
from app.core.deps import get_current_user, get_current_tenant
from app.models.user import User
from app.models.tenant import Tenant, TenantStatus
from app.services.billing import BillingService
from app.core.config import settings
from datetime import datetime, timezone

router = APIRouter()


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="x-razorpay-signature"),
    db: AsyncSession = Depends(get_public_db),
):
    """Razorpay sends events here. Must be public (no auth)."""
    payload = await request.body()
    if not x_razorpay_signature:
        raise HTTPException(400, "Missing Razorpay signature")

    try:
        result = await BillingService.handle_webhook(payload, x_razorpay_signature, db)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Webhook error: {str(e)}")


@router.post("/create-checkout")
async def create_checkout(
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_public_db),
):
    """Create a Razorpay Payment Link for the Growth plan (one-time or first payment)."""
    if not settings.RAZORPAY_KEY_ID:
        raise HTTPException(503, "Billing not configured")

    if tenant.status == TenantStatus.ACTIVE and tenant.stripe_subscription_id:
        raise HTTPException(400, "Already subscribed. Use the portal to manage your subscription.")

    # Create Razorpay customer if not exists
    if not tenant.stripe_customer_id:
        customer_id = await BillingService.create_customer(tenant)
        await db.execute(text("SET search_path TO public"))
        await db.execute(text(
            "UPDATE tenants SET stripe_customer_id = :cid WHERE id = :id"
        ), {"cid": customer_id, "id": tenant.id})
        await db.commit()
        tenant.stripe_customer_id = customer_id

    erp_url = f"https://{tenant.slug}.{settings.BASE_DOMAIN}"
    checkout_url = await BillingService.create_checkout_session(
        tenant,
        success_url=f"{erp_url}?subscribed=true",
        cancel_url=f"{erp_url}/billing",
    )
    return {"checkout_url": checkout_url}


@router.post("/create-subscription")
async def create_subscription(
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_public_db),
):
    """
    Create a Razorpay Subscription for recurring monthly billing.
    Requires RAZORPAY_PLAN_ID in .env.
    """
    if not settings.RAZORPAY_KEY_ID:
        raise HTTPException(503, "Billing not configured")

    if not settings.RAZORPAY_PLAN_ID:
        raise HTTPException(503, "Subscription plan not configured. Use /create-checkout for one-time payment.")

    erp_url = f"https://{tenant.slug}.{settings.BASE_DOMAIN}"
    subscription_url = await BillingService.create_subscription(
        tenant,
        success_url=f"{erp_url}?subscribed=true",
    )
    return {"checkout_url": subscription_url}


@router.post("/portal")
async def billing_portal(
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Razorpay has no hosted billing portal.
    Returns a new payment link so the customer can renew or update payment.
    """
    if not tenant.stripe_customer_id:
        raise HTTPException(400, "No billing account found. Please subscribe first.")

    return_url = f"https://{tenant.slug}.{settings.BASE_DOMAIN}/settings"
    portal_url = await BillingService.create_billing_portal_session(tenant, return_url)
    return {"portal_url": portal_url}


@router.get("/status")
async def billing_status(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Return current billing/subscription status for the tenant."""
    now = datetime.now(timezone.utc)

    trial_days_left = None
    if tenant.trial_ends_at and tenant.status == TenantStatus.TRIAL:
        delta = tenant.trial_ends_at - now
        trial_days_left = max(0, delta.days)

    return {
        "status": tenant.status,
        "plan": tenant.plan,
        "trial_days_left": trial_days_left,
        "subscription_ends_at": tenant.subscription_ends_at,
        "trial_ends_at": tenant.trial_ends_at,
        "ai_actions_used": tenant.ai_actions_used,
        "ai_actions_limit": tenant.ai_actions_limit,
        "ai_actions_remaining": max(0, tenant.ai_actions_limit - tenant.ai_actions_used),
        "has_payment_method": bool(tenant.stripe_customer_id),
    }
