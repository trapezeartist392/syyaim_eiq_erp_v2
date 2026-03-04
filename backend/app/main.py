from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal, Base
from app.api.v1.router import api_router
from app.middleware.tenant import TenantMiddleware
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure public schema has tenants table
    # Use raw connection to avoid asyncpg "multiple commands" error with SET + DDL
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text("SET search_path TO public"))
        await conn.execute(text(
            "CREATE TABLE IF NOT EXISTS tenants ("
            "id SERIAL PRIMARY KEY,"
            "name VARCHAR(255) NOT NULL,"
            "slug VARCHAR(63) UNIQUE NOT NULL,"
            "email VARCHAR(255) UNIQUE NOT NULL,"
            "phone VARCHAR(20),"
            "status VARCHAR(20) NOT NULL DEFAULT 'trial',"
            "plan VARCHAR(50) DEFAULT 'growth',"
            "trial_ends_at TIMESTAMPTZ,"
            "subscription_ends_at TIMESTAMPTZ,"
            "stripe_customer_id VARCHAR(100) UNIQUE,"
            "stripe_subscription_id VARCHAR(100) UNIQUE,"
            "ai_actions_used INTEGER DEFAULT 0,"
            "ai_actions_limit INTEGER DEFAULT 2500,"
            "schema_created BOOLEAN DEFAULT false,"
            "created_at TIMESTAMPTZ DEFAULT now(),"
            "updated_at TIMESTAMPTZ"
            ")"
        ))

    os.makedirs("media/attachments", exist_ok=True)
    os.makedirs("media/exports", exist_ok=True)
    yield


app = FastAPI(
    title="Syyaim EIQ ERP API",
    description="Agentic AI-Powered ERP for Manufacturing — SaaS Edition",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        f"https://{settings.BASE_DOMAIN}",
        f"https://*.{settings.BASE_DOMAIN}",
    ],
    allow_origin_regex=r"https://.*\.syyaimeiq\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant resolution middleware
app.add_middleware(TenantMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "app": "Syyaim EIQ ERP", "mode": "saas"}
