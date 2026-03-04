"""
Multi-tenant database layer.

Architecture:
- public schema: tenants table (one row per customer)
- {slug} schema: full ERP tables per tenant (users, leads, items, etc.)

Connection routing:
- Public DB: used for tenant lookup, signup, billing webhooks
- Tenant DB: set search_path = {slug} before every query
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, event
from app.core.config import settings
from typing import AsyncGenerator
import re


# ── Base engine (public schema) ──────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Public schema session (for tenant management) ────────────────────────────
async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("SET search_path TO public"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Tenant-scoped session ─────────────────────────────────────────────────────
def get_tenant_db(tenant_slug: str):
    """
    Returns a FastAPI dependency that provides a session
    with search_path set to the tenant's schema.
    """
    # Validate slug — only alphanumeric + hyphens, no SQL injection
    if not re.match(r'^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$', tenant_slug):
        raise ValueError(f"Invalid tenant slug: {tenant_slug}")

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            try:
                # Set schema search path for this session
                await session.execute(
                    text(f"SET search_path TO {tenant_slug}, public")
                )
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    return _get_db


# ── Backward compat: default get_db uses public schema ───────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_public_db():
        yield session


# ── Schema management ─────────────────────────────────────────────────────────
async def create_tenant_schema(slug: str) -> None:
    """
    Create a new PostgreSQL schema for a tenant and
    run all ERP table DDL inside it.
    """
    async with AsyncSessionLocal() as session:
        await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{slug}"'))
        await session.execute(text(f'SET search_path TO "{slug}", public'))
        await _create_tenant_tables(session, slug)
        await session.commit()


async def drop_tenant_schema(slug: str) -> None:
    """Drop a tenant schema and all its tables (for cancellation/cleanup)."""
    async with AsyncSessionLocal() as session:
        await session.execute(text(f'DROP SCHEMA IF EXISTS "{slug}" CASCADE'))
        await session.commit()


async def _create_tenant_tables(session: AsyncSession, slug: str) -> None:
    """Create all ERP tables in the tenant schema."""

    # Enums must be created in each schema separately
    enums = [
        ("userrole", ['super_admin','admin','manager','accountant','hr_manager',
                      'purchase_manager','sales_manager','warehouse_manager','viewer']),
        ("leadstatus", ['new','contacted','qualified','proposal','negotiation','won','lost']),
        ("prstatus", ['draft','pending_approval','approved','rejected','po_created']),
        ("postatus", ['draft','sent','acknowledged','partially_received','received',
                      'invoiced','paid','cancelled']),
        ("itemcategory", ['raw_material','wip','finished_goods','consumables','spares']),
        ("employmenttype", ['full_time','part_time','contract']),
        ("transactiontype", ['debit','credit']),
        ("accounttype", ['asset','liability','equity','income','expense']),
    ]

    for name, values in enums:
        vals = ", ".join(f"'{v}'" for v in values)
        await session.execute(text(f"""
            DO $$ BEGIN
                CREATE TYPE "{slug}".{name} AS ENUM ({vals});
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))

    # All ERP tables
    ddl = f"""
        SET search_path TO "{slug}", public;

        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role userrole NOT NULL DEFAULT 'viewer',
            department VARCHAR(100),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            contact_name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            source VARCHAR(100),
            status leadstatus DEFAULT 'new',
            value FLOAT DEFAULT 0,
            ai_score INTEGER DEFAULT 0,
            ai_notes TEXT,
            assigned_to INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS sales_orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE,
            customer_name VARCHAR(255) NOT NULL,
            customer_email VARCHAR(255),
            total_amount FLOAT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'draft',
            lead_id INTEGER REFERENCES leads(id),
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS vendors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            code VARCHAR(50) UNIQUE,
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            gstin VARCHAR(15),
            payment_terms INTEGER DEFAULT 30,
            rating FLOAT DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS purchase_requisitions (
            id SERIAL PRIMARY KEY,
            pr_number VARCHAR(50) UNIQUE,
            item_description TEXT NOT NULL,
            quantity FLOAT NOT NULL,
            unit VARCHAR(20) DEFAULT 'pcs',
            estimated_cost FLOAT,
            department VARCHAR(100),
            required_by TIMESTAMPTZ,
            status prstatus DEFAULT 'draft',
            ai_recommendation TEXT,
            requested_by INTEGER REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id SERIAL PRIMARY KEY,
            po_number VARCHAR(50) UNIQUE,
            vendor_id INTEGER REFERENCES vendors(id) NOT NULL,
            pr_id INTEGER REFERENCES purchase_requisitions(id),
            total_amount FLOAT DEFAULT 0,
            tax_amount FLOAT DEFAULT 0,
            status postatus DEFAULT 'draft',
            delivery_date TIMESTAMPTZ,
            terms TEXT,
            three_way_match_status VARCHAR(50) DEFAULT 'pending',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE,
            name VARCHAR(255) NOT NULL,
            category itemcategory DEFAULT 'raw_material',
            unit VARCHAR(20) DEFAULT 'pcs',
            current_stock FLOAT DEFAULT 0,
            reorder_point FLOAT DEFAULT 0,
            reorder_qty FLOAT DEFAULT 0,
            unit_cost FLOAT DEFAULT 0,
            location VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            ai_forecast_qty FLOAT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id SERIAL PRIMARY KEY,
            item_id INTEGER REFERENCES items(id) NOT NULL,
            movement_type VARCHAR(20),
            quantity FLOAT NOT NULL,
            reference VARCHAR(100),
            notes TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            employee_id VARCHAR(50) UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(20),
            department VARCHAR(100),
            designation VARCHAR(100),
            employment_type employmenttype DEFAULT 'full_time',
            date_of_joining DATE,
            date_of_birth DATE,
            pan VARCHAR(10),
            aadhaar VARCHAR(12),
            bank_account VARCHAR(20),
            ifsc_code VARCHAR(11),
            basic_salary FLOAT DEFAULT 0,
            hra FLOAT DEFAULT 0,
            allowances FLOAT DEFAULT 0,
            pf_applicable BOOLEAN DEFAULT true,
            esi_applicable BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS payrolls (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES employees(id) NOT NULL,
            month INTEGER,
            year INTEGER,
            working_days FLOAT DEFAULT 26,
            present_days FLOAT DEFAULT 26,
            basic FLOAT DEFAULT 0,
            hra FLOAT DEFAULT 0,
            allowances FLOAT DEFAULT 0,
            gross_salary FLOAT DEFAULT 0,
            pf_employee FLOAT DEFAULT 0,
            pf_employer FLOAT DEFAULT 0,
            esi_employee FLOAT DEFAULT 0,
            esi_employer FLOAT DEFAULT 0,
            tds FLOAT DEFAULT 0,
            net_salary FLOAT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            processed_at TIMESTAMPTZ,
            ai_anomaly_flag BOOLEAN DEFAULT false,
            ai_anomaly_notes TEXT
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE,
            name VARCHAR(255) NOT NULL,
            account_type accounttype,
            parent_id INTEGER REFERENCES accounts(id),
            balance FLOAT DEFAULT 0,
            is_active BOOLEAN DEFAULT true
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id SERIAL PRIMARY KEY,
            entry_number VARCHAR(50) UNIQUE,
            date DATE NOT NULL,
            description TEXT,
            reference VARCHAR(100),
            total_debit FLOAT DEFAULT 0,
            total_credit FLOAT DEFAULT 0,
            is_balanced BOOLEAN DEFAULT false,
            ai_generated BOOLEAN DEFAULT false,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS journal_lines (
            id SERIAL PRIMARY KEY,
            entry_id INTEGER REFERENCES journal_entries(id) NOT NULL,
            account_id INTEGER REFERENCES accounts(id) NOT NULL,
            transaction_type transactiontype,
            amount FLOAT NOT NULL,
            narration TEXT
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id SERIAL PRIMARY KEY,
            agent_name VARCHAR(100) NOT NULL,
            action VARCHAR(255) NOT NULL,
            module VARCHAR(50),
            entity_type VARCHAR(50),
            entity_id INTEGER,
            input_data TEXT,
            output_data TEXT,
            tokens_used INTEGER DEFAULT 0,
            duration_ms FLOAT DEFAULT 0,
            success BOOLEAN DEFAULT true,
            error_message TEXT,
            triggered_by INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """
    await session.execute(text(ddl))
