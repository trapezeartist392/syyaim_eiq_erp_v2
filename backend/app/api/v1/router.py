from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, crm, purchase, material, hr, finance,
    agents, dashboard, public, billing, superadmin
)

api_router = APIRouter()

# Public — no auth, no tenant required
api_router.include_router(public.router,      prefix="/public",     tags=["Public Signup"])
api_router.include_router(billing.router,     prefix="/billing",    tags=["Billing"])
api_router.include_router(superadmin.router,  prefix="/superadmin", tags=["Super Admin"])

# Tenant-scoped — require tenant context + JWT
api_router.include_router(auth.router,        prefix="/auth",       tags=["Authentication"])
api_router.include_router(users.router,       prefix="/users",      tags=["Users"])
api_router.include_router(crm.router,         prefix="/crm",        tags=["CRM & Sales"])
api_router.include_router(purchase.router,    prefix="/purchase",   tags=["Purchase"])
api_router.include_router(material.router,    prefix="/material",   tags=["Material Management"])
api_router.include_router(hr.router,          prefix="/hr",         tags=["HR & Payroll"])
api_router.include_router(finance.router,     prefix="/finance",    tags=["Finance"])
api_router.include_router(agents.router,      prefix="/agents",     tags=["AI Agents"])
api_router.include_router(dashboard.router,   prefix="/dashboard",  tags=["Dashboard"])
