"""
Razorpay billing service.

Handles:
- Creating Razorpay customers on signup
- Creating payment links / subscriptions (Growth plan Rs.12,999/mo)
- Webhook event processing
- Trial management
"""
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.config import settings
from app.models.tenant import Tenant, TenantStatus
import logging

logger = logging.getLogger(__name__)

RAZORPAY_API = "https://api.razorpay.com/v1"


def _auth():
    return (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)


class BillingService:

    @staticmethod
    async def create_customer(tenant: Tenant) -> str:
        """Create a Razorpay customer. Returns customer_id."""
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{RAZORPAY_API}/customers",
                auth=_auth(),
                json={k: v for k, v in {
                    "name": tenant.name,
                    "email": tenant.email,
                    "contact": tenant.phone if tenant.phone else None,
                    "notes": {
                        "tenant_slug": tenant.slug,
                        "tenant_id": str(tenant.id),
                    },
                }.items() if v is not None},
            )
            r.raise_for_status()
            return r.json()["id"]

    @staticmethod
    async def create_checkout_session(tenant: Tenant, success_url: str, cancel_url: str) -> str:
        """
        Create a Razorpay Payment Link for the Growth plan (Rs.12,999/month).
        Returns the short payment URL to redirect the user to.
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{RAZORPAY_API}/payment_links",
                auth=_auth(),
                json={
                    "amount": 1299900,
                    "currency": "INR",
                    "accept_partial": False,
                    "description": "Syyaim EIQ ERP — Growth Plan (Monthly)",
                    "customer": {
                        "name": tenant.name,
                        "email": tenant.email,
                    },
                    "notify": {"sms": False, "email": True},
                    "reminder_enable": True,
                    "notes": {
                        "tenant_slug": tenant.slug,
                        "tenant_id": str(tenant.id),
                    },
                    "callback_url": success_url,
                    "callback_method": "get",
                },
            )
            r.raise_for_status()
            return r.json()["short_url"]

    @staticmethod
    async def create_subscription(tenant: Tenant, success_url: str) -> str:
        """
        Create a Razorpay Subscription for recurring monthly billing.
        Requires RAZORPAY_PLAN_ID to be set in .env.
        Returns hosted subscription page URL.
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{RAZORPAY_API}/subscriptions",
                auth=_auth(),
                json={
                    "plan_id": settings.RAZORPAY_PLAN_ID,
                    "customer_notify": 1,
                    "quantity": 1,
                    "total_count": 120,
                    "notes": {
                        "tenant_slug": tenant.slug,
                        "tenant_id": str(tenant.id),
                    },
                },
            )
            r.raise_for_status()
            data = r.json()
            # Return hosted page if available, else short_url
            return data.get("short_url") or success_url

    @staticmethod
    async def create_billing_portal_session(tenant: Tenant, return_url: str) -> str:
        """
        Razorpay has no hosted billing portal.
        Returns a new payment link so customer can make a payment.
        """
        return await BillingService.create_checkout_session(
            tenant,
            success_url=return_url,
            cancel_url=return_url,
        )

    @staticmethod
    async def handle_webhook(payload: bytes, signature: str, db: AsyncSession) -> dict:
        """
        Process Razorpay webhook events.
        Razorpay signs using HMAC-SHA256 of the raw payload with webhook secret.

        Events handled:
        - payment.captured          -> one-time payment succeeded
        - payment_link.paid         -> payment link paid
        - subscription.activated    -> subscription started
        - subscription.charged      -> monthly charge succeeded
        - subscription.halted       -> payment failed, suspended
        - subscription.cancelled    -> cancelled
        """
        # Verify signature
        if settings.RAZORPAY_WEBHOOK_SECRET:
            expected = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                raise ValueError("Invalid webhook signature")

        event = json.loads(payload)
        event_type = event.get("event")
        entity = event.get("payload", {})

        logger.info(f"Razorpay webhook: {event_type}")

        if event_type == "payment.captured":
            data = entity.get("payment", {}).get("entity", {})
            await BillingService._on_payment_captured(data, db)

        elif event_type == "payment_link.paid":
            data = entity.get("payment_link", {}).get("entity", {})
            await BillingService._on_payment_link_paid(data, db)

        elif event_type in ("subscription.activated", "subscription.charged"):
            data = entity.get("subscription", {}).get("entity", {})
            await BillingService._on_subscription_activated(data, db)

        elif event_type == "subscription.halted":
            data = entity.get("subscription", {}).get("entity", {})
            await BillingService._on_subscription_halted(data, db)

        elif event_type == "subscription.cancelled":
            data = entity.get("subscription", {}).get("entity", {})
            await BillingService._on_subscription_cancelled(data, db)

        return {"received": True, "event": event_type}

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    async def _get_tenant_by_slug(slug: str, db: AsyncSession):
        await db.execute(text("SET search_path TO public"))
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    # ── Event handlers ────────────────────────────────────────────────────────

    @staticmethod
    async def _on_payment_captured(data: dict, db: AsyncSession):
        slug = (data.get("notes") or {}).get("tenant_slug")
        if not slug:
            return
        tenant = await BillingService._get_tenant_by_slug(slug, db)
        if not tenant:
            return
        tenant.stripe_subscription_id = data.get("id")
        tenant.status = TenantStatus.ACTIVE
        tenant.subscription_ends_at = datetime.now(timezone.utc) + timedelta(days=30)
        await db.commit()
        logger.info(f"Tenant {slug} activated via payment capture")

    @staticmethod
    async def _on_payment_link_paid(data: dict, db: AsyncSession):
        slug = (data.get("notes") or {}).get("tenant_slug")
        if not slug:
            return
        tenant = await BillingService._get_tenant_by_slug(slug, db)
        if not tenant:
            return
        tenant.stripe_subscription_id = data.get("id")
        tenant.status = TenantStatus.ACTIVE
        tenant.subscription_ends_at = datetime.now(timezone.utc) + timedelta(days=30)
        await db.commit()
        logger.info(f"Tenant {slug} activated via payment link")

    @staticmethod
    async def _on_subscription_activated(data: dict, db: AsyncSession):
        slug = (data.get("notes") or {}).get("tenant_slug")
        if not slug:
            return
        tenant = await BillingService._get_tenant_by_slug(slug, db)
        if not tenant:
            return
        tenant.stripe_subscription_id = data.get("id")
        tenant.status = TenantStatus.ACTIVE
        charge_at = data.get("charge_at")
        if charge_at:
            tenant.subscription_ends_at = datetime.fromtimestamp(charge_at, tz=timezone.utc)
        else:
            tenant.subscription_ends_at = datetime.now(timezone.utc) + timedelta(days=30)
        tenant.ai_actions_used = 0
        await db.commit()
        logger.info(f"Tenant {slug} subscription active/charged")

    @staticmethod
    async def _on_subscription_halted(data: dict, db: AsyncSession):
        slug = (data.get("notes") or {}).get("tenant_slug")
        if not slug:
            return
        tenant = await BillingService._get_tenant_by_slug(slug, db)
        if not tenant:
            return
        tenant.status = TenantStatus.SUSPENDED
        await db.commit()
        logger.warning(f"Tenant {slug} suspended — subscription halted")

    @staticmethod
    async def _on_subscription_cancelled(data: dict, db: AsyncSession):
        slug = (data.get("notes") or {}).get("tenant_slug")
        if not slug:
            return
        tenant = await BillingService._get_tenant_by_slug(slug, db)
        if not tenant:
            return
        tenant.status = TenantStatus.CANCELLED
        await db.commit()
        logger.info(f"Tenant {slug} subscription cancelled")
