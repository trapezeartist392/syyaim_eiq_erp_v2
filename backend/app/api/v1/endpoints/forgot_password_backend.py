# backend/app/api/v1/endpoints/forgot_password.py
# Add these endpoints to your auth.py or as a separate file

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from app.core.database import get_public_db
from app.core.security import hash_password

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token:        str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_public_db)
):
    """
    Generate a reset token and store it.
    In production: send email with token.
    For now: returns token in response for testing.
    """
    email = body.email.lower().strip()

    # Find which tenant this user belongs to
    result = await db.execute(text("""
        SELECT t.slug, t.schema_name
        FROM tenants t
        JOIN LATERAL (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = t.slug AND table_name = 'users'
        ) tables ON true
        WHERE EXISTS (
            SELECT 1 FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = t.slug AND c.relname = 'users'
        )
    """))
    tenants = result.fetchall()

    found_tenant = None
    for tenant in tenants:
        user_check = await db.execute(text(
            f'SELECT id FROM "{tenant.slug}".users WHERE email = :email'
        ), {"email": email})
        if user_check.fetchone():
            found_tenant = tenant.slug
            break

    # Always return success to prevent email enumeration
    if not found_tenant:
        return {"message": "If this email exists, a reset link has been sent."}

    # Generate secure token (6-digit for simplicity, use UUID in production)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Store token in public schema reset_tokens table
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255),
            tenant_slug VARCHAR(100),
            token VARCHAR(100) UNIQUE,
            expires_at TIMESTAMPTZ,
            used BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    # Delete old tokens for this email
    await db.execute(text(
        "DELETE FROM password_reset_tokens WHERE email = :email"
    ), {"email": email})

    # Insert new token
    await db.execute(text("""
        INSERT INTO password_reset_tokens (email, tenant_slug, token, expires_at)
        VALUES (:email, :tenant, :token, :expires)
    """), {"email": email, "tenant": found_tenant, "token": token, "expires": expires_at})
    await db.commit()

    # TODO: Send email in production
    # For now return token directly (remove in production, use email service instead)
    return {
        "message": "If this email exists, a reset link has been sent.",
        "debug_token": token,  # REMOVE IN PRODUCTION
        "expires_in": "1 hour"
    }


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_public_db)
):
    if len(body.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")

    # Find token
    result = await db.execute(text("""
        SELECT * FROM password_reset_tokens
        WHERE token = :token AND used = false AND expires_at > NOW()
    """), {"token": body.token})
    reset = result.fetchone()

    if not reset:
        raise HTTPException(400, "Invalid or expired reset token")

    # Update password in tenant schema
    new_hash = hash_password(body.new_password)
    await db.execute(text(
        f'UPDATE "{reset.tenant_slug}".users SET password_hash = :hash WHERE email = :email'
    ), {"hash": new_hash, "email": reset.email})

    # Mark token as used
    await db.execute(text(
        "UPDATE password_reset_tokens SET used = true WHERE token = :token"
    ), {"token": body.token})

    await db.commit()
    return {"message": "Password reset successfully. You can now log in."}
