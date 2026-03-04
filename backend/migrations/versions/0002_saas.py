"""SaaS: add tenants table to public schema

Revision ID: 0002_saas
Revises: 0001
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_saas'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Each statement must be its own op.execute() call —
    # asyncpg does not allow multiple commands in a single prepared statement

    op.execute("SET search_path TO public")

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tenantStatus AS ENUM ('trial','active','suspended','cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(63) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            status VARCHAR(20) NOT NULL DEFAULT 'trial',
            plan VARCHAR(50) DEFAULT 'growth',
            trial_ends_at TIMESTAMPTZ,
            subscription_ends_at TIMESTAMPTZ,
            stripe_customer_id VARCHAR(100) UNIQUE,
            stripe_subscription_id VARCHAR(100) UNIQUE,
            ai_actions_used INTEGER DEFAULT 0,
            ai_actions_limit INTEGER DEFAULT 2500,
            schema_created BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tenants_stripe_customer ON tenants(stripe_customer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tenants_stripe_sub ON tenants(stripe_subscription_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.tenants CASCADE")
    op.execute("DROP TYPE IF EXISTS tenantStatus")
