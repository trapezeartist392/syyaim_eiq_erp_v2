# Syyaim EIQ ERP

AI-Powered ERP for Manufacturing — SaaS Edition

## What's included

**Backend (FastAPI + PostgreSQL)**
- 6 ERP modules: Finance, Purchase, Inventory/Material, HR & Payroll, CRM & Sales, AI Agents
- Multi-tenant SaaS architecture (schema-per-tenant)
- Tenant signup, trial management, Stripe billing
- 6 AI Agents powered by Claude (Anthropic)

**Frontend (React + Vite + Tailwind)**
- Full ERP dashboard
- Public signup page (creates new tenant + 14-day trial)
- Trial/billing banner
- Login page

## Quick start (Windows)

```bat
# 1. Copy env
copy .env.example .env
# Edit .env — fill in DATABASE_URL, ANTHROPIC_API_KEY, STRIPE keys

# 2. Run with Docker
deploy.bat
```

## Quick start (Linux / Mac)

```bash
cp .env.example .env
# Edit .env

chmod +x deploy.sh
./deploy.sh
```

## Local dev (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
VITE_TENANT_SLUG=demo npm run dev
```

Visit http://localhost:5173 (frontend) and http://localhost:8000/api/docs (API docs)

## Tenant resolution

In production, tenants are identified by subdomain: `acme.syyaimeiq.com`

In local dev, use the `VITE_TENANT_SLUG` env var or send the `X-Tenant-Slug` header.

## Environment variables

See `.env.example` for full list. Required to fill in:
- `SECRET_KEY` — generate with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_GROWTH_PRICE_ID` — from Stripe dashboard

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL 16 (schema-per-tenant) |
| AI | Anthropic Claude (claude-opus-4-6) |
| Billing | Stripe |
| Frontend | React 18, Vite, Tailwind CSS |
| Background jobs | Celery + Redis |
| Deployment | Docker Compose + Nginx |
