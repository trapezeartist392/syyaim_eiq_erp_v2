# backend/app/api/v1/endpoints/agents.py
# AI Agents endpoint with per-tenant rate limiting

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import anthropic
import json

from app.core.database import get_tenant_session
from app.core.config import settings
from app.core.ai_rate_limiter import check_and_increment, get_usage

router = APIRouter()

# Tenant plan mapping — update as clients upgrade
# In future this should come from the tenants DB table
TENANT_PLANS = {
    "kingsway":          "basic",
    "wesben":            "basic",
    "syyaim-enterprise": "enterprise",
    "demo":              "trial",
}

def get_tenant_plan(tenant_slug: str) -> str:
    return TENANT_PLANS.get(tenant_slug, "basic")


class AgentRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    module: Optional[str] = None   # crm, hr, finance, material, purchase


class AgentResponse(BaseModel):
    response: str
    usage: dict
    tokens_used: Optional[int] = None


@router.post("/ask", response_model=AgentResponse)
async def ask_agent(
    body: AgentRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session),
):
    tenant_slug = getattr(request.state, "tenant_slug", "unknown")
    plan = get_tenant_plan(tenant_slug)

    # ── Rate limit check ────────────────────────────────────────────────────
    usage = await check_and_increment(tenant_slug, plan)

    # ── Build system prompt based on module ─────────────────────────────────
    module_context = {
        "crm":      "You are an ERP CRM assistant. Help analyze leads, suggest follow-ups, and identify sales opportunities.",
        "hr":       "You are an ERP HR assistant. Help with employee queries, payroll analysis, and HR recommendations.",
        "finance":  "You are an ERP Finance assistant. Help with GL accounts, journal entries, and financial analysis.",
        "material": "You are an ERP Materials assistant. Help with inventory, reorder points, and stock optimization.",
        "purchase": "You are an ERP Purchase assistant. Help with vendor selection, PR approvals, and cost optimization.",
    }.get(body.module or "", "You are a helpful ERP assistant for Syyaim EIQ.")

    system_prompt = f"""{module_context}
You are working within tenant: {tenant_slug}.
Be concise, data-driven, and actionable. Format responses clearly.
If the user asks for data, suggest they use the relevant ERP module.
"""

    # ── Call Anthropic API ──────────────────────────────────────────────────
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    messages = []
    if body.context:
        messages.append({"role": "user", "content": f"Context data:\n{body.context}"})
        messages.append({"role": "assistant", "content": "I have reviewed the context data. How can I help?"})

    messages.append({"role": "user", "content": body.prompt})

    ai_response = client.messages.create(
        model="claude-haiku-4-5-20251001",   # cheapest model for ERP queries
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    response_text = ai_response.content[0].text
    tokens = ai_response.usage.input_tokens + ai_response.usage.output_tokens

    # ── Log to agent_logs table ─────────────────────────────────────────────
    try:
        await db.execute(
            """INSERT INTO agent_logs (action, result, created_at)
               VALUES (:action, :result, NOW())""",
            {
                "action": f"[{body.module or 'general'}] {body.prompt[:200]}",
                "result": response_text[:500],
            }
        )
        await db.commit()
    except Exception:
        pass  # Don't fail the request if logging fails

    return AgentResponse(
        response=response_text,
        usage=usage,
        tokens_used=tokens,
    )


@router.get("/usage")
async def get_ai_usage(request: Request):
    """Get current tenant's AI usage for today."""
    tenant_slug = getattr(request.state, "tenant_slug", "unknown")
    plan = get_tenant_plan(tenant_slug)
    return await get_usage(tenant_slug, plan)


@router.get("/usage/all")
async def get_all_usage(request: Request):
    """Superadmin only: see all tenants usage."""
    from app.core.ai_rate_limiter import get_all_tenants_usage
    # In production add admin auth check here
    tenant_slug = getattr(request.state, "tenant_slug", "unknown")
    if tenant_slug != "syyaim-enterprise":
        raise HTTPException(status_code=403, detail="Superadmin only")
    return await get_all_tenants_usage()
