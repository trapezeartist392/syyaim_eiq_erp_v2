"""
Syyaim EIQ ERP — AI Agent Orchestration Engine
Supports: Anthropic Claude (primary), with extension points for other providers.
"""
import json
import time
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.agent_log import AgentLog

log = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client — currently uses Anthropic Claude via httpx."""

    async def chat(self, system: str, user: str, max_tokens: int = 1000) -> str:
        return await self._anthropic(system, user, max_tokens)

    async def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]


llm = LLMClient()


class EngineBaseAgent:
    """Base class for engine-defined AI agents (used by Celery tasks and registry)."""

    name: str = "BaseAgent"
    module: str = "system"

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def run(self, **kwargs) -> dict:
        raise NotImplementedError

    async def _ask_llm(self, system: str, prompt: str, max_tokens: int = 800) -> str:
        return await llm.chat(system, prompt, max_tokens)

    async def _parse_json_response(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
        return {"raw": text}

    async def _log_action(self, action: str, status: str,
                          input_data: dict = None, output_data: dict = None,
                          duration_ms: int = 0):
        if self.db:
            entry = AgentLog(
                agent_name=self.name,
                module=self.module,
                action=action,
                entity_type=status,
                input_data=json.dumps(input_data) if input_data else None,
                output_data=json.dumps(output_data) if output_data else None,
                duration_ms=duration_ms,
                success=status != "error",
            )
            self.db.add(entry)
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()


# ══════════════════════════════════════════════════════════════
# CRM AGENTS
# ══════════════════════════════════════════════════════════════
class LeadScoringAgent(EngineBaseAgent):
    name = "LeadScoringAgent"
    module = "crm"

    async def run(self, lead_data: dict = None, **kwargs) -> dict:
        if lead_data is None:
            lead_data = kwargs
        t0 = time.time()
        system = """You are an expert B2B sales AI for a manufacturing ERP software company.
Score incoming leads from 0-100 based on fit, intent, and conversion probability.
Return ONLY valid JSON with keys: score (int), grade (A/B/C/D), reason (str), recommended_action (str), next_followup_days (int)."""

        prompt = f"""Score this lead:
Company: {lead_data.get('company_name', 'Unknown')}
Contact: {lead_data.get('contact_name', '')}
Source: {lead_data.get('source', 'manual')}
Estimated Value: {lead_data.get('estimated_value', lead_data.get('value', 0))}
Industry: Manufacturing
Notes: {lead_data.get('notes', 'None')}"""

        try:
            response = await self._ask_llm(system, prompt)
            result = await self._parse_json_response(response)
            result["agent"] = self.name
            await self._log_action("score_lead", "success", lead_data, result,
                                   int((time.time() - t0) * 1000))
            return result
        except Exception as e:
            log.error("Lead scoring failed: %s", str(e))
            return {"score": 50, "grade": "B", "reason": "AI scoring unavailable", "recommended_action": "Manual review"}


class ChurnPredictionAgent(EngineBaseAgent):
    name = "ChurnPredictionAgent"
    module = "crm"

    async def run(self, customer_data: dict = None, **kwargs) -> dict:
        if customer_data is None:
            customer_data = kwargs
        t0 = time.time()
        system = """You are a customer success AI for a manufacturing ERP. Predict churn risk for B2B customers.
Return ONLY valid JSON with keys: churn_risk (0.0-1.0), risk_level (low/medium/high/critical), 
reasons (list of strings), recommended_actions (list of strings)."""

        prompt = f"""Analyze customer churn risk:
Customer: {customer_data.get('name')}
Last Order Days Ago: {customer_data.get('days_since_last_order', 'Unknown')}
Total Orders (12 months): {customer_data.get('orders_12m', 0)}
Order Value Trend: {customer_data.get('value_trend', 'unknown')}
Open Complaints: {customer_data.get('open_complaints', 0)}
Credit Overdue: {customer_data.get('credit_overdue', False)}"""

        response = await self._ask_llm(system, prompt)
        result = await self._parse_json_response(response)
        await self._log_action("predict_churn", "success", customer_data, result,
                               int((time.time() - t0) * 1000))
        return result


# ══════════════════════════════════════════════════════════════
# PURCHASE AGENTS
# ══════════════════════════════════════════════════════════════
class PRApprovalAgent(EngineBaseAgent):
    name = "PRApprovalAgent"
    module = "purchase"

    async def run(self, pr_data: dict = None, **kwargs) -> dict:
        if pr_data is None:
            pr_data = kwargs
        t0 = time.time()
        system = """You are a procurement AI agent for a manufacturing company. 
Evaluate purchase requisitions for auto-approval based on policy.
Return ONLY valid JSON with keys: decision (approve/reject/escalate), 
confidence (0.0-1.0), reason (str), conditions (list of strings or empty list)."""

        budget_ok = pr_data.get("total_amount", 0) <= pr_data.get("budget_remaining", 999999)
        prompt = f"""Evaluate this purchase requisition:
PR Number: {pr_data.get('pr_number')}
Total Amount: {pr_data.get('total_amount', 0)}
Priority: {pr_data.get('priority', 'medium')}
Budget OK: {budget_ok}
Requested By: {pr_data.get('requested_by', 'Unknown')}
Items: {pr_data.get('item_count', 0)} items
Required Date: {pr_data.get('required_date', 'Not specified')}
Notes: {pr_data.get('notes', 'None')}

Auto-approve if: amount < 50000 AND budget available AND not critical item."""

        response = await self._ask_llm(system, prompt)
        result = await self._parse_json_response(response)
        await self._log_action("evaluate_pr", result.get("decision", "escalate"),
                               pr_data, result, int((time.time() - t0) * 1000))
        return result


class ThreeWayMatchAgent(EngineBaseAgent):
    name = "ThreeWayMatchAgent"
    module = "purchase"

    async def run(self, match_data: dict = None, **kwargs) -> dict:
        if match_data is None:
            match_data = kwargs
        t0 = time.time()
        po = match_data.get("po", {})
        grn = match_data.get("grn", {})
        inv = match_data.get("invoice", {})

        qty_match = abs(grn.get("quantity", 0) - po.get("quantity", 0)) <= 0.01
        po_unit_price = po.get("unit_price", 1) or 1
        price_variance = abs(inv.get("unit_price", 0) - po.get("unit_price", 0))
        price_variance_pct = (price_variance / po_unit_price) * 100

        result = {
            "match_status": "matched" if (qty_match and price_variance_pct < 2) else "mismatch",
            "qty_match": qty_match,
            "price_variance_pct": round(price_variance_pct, 2),
            "action": "approve_payment" if qty_match and price_variance_pct < 2 else "hold_for_review",
            "discrepancies": [],
        }
        if not qty_match:
            result["discrepancies"].append(f"Qty mismatch: PO={po.get('quantity')}, GRN={grn.get('quantity')}")
        if price_variance_pct >= 2:
            result["discrepancies"].append(f"Price variance {price_variance_pct:.1f}%")

        await self._log_action("three_way_match", result["match_status"], match_data, result,
                               int((time.time() - t0) * 1000))
        return result


# ══════════════════════════════════════════════════════════════
# MATERIAL MANAGEMENT AGENTS
# ══════════════════════════════════════════════════════════════
class MRPPlanningAgent(EngineBaseAgent):
    name = "MRPPlanningAgent"
    module = "material"

    async def run(self, mrp_data: dict = None, **kwargs) -> dict:
        if mrp_data is None:
            mrp_data = kwargs
        t0 = time.time()
        system = """You are an MRP planning AI for a manufacturing company.
Analyze demand, stock levels, lead times, and generate procurement recommendations.
Return ONLY valid JSON with keys: recommendations (list), 
total_items_to_order (int), estimated_procurement_value (float), priority_items (list)."""

        prompt = f"""Run MRP analysis:
Open Sales Orders: {mrp_data.get('open_so_count', 0)}
Total SO Value: {mrp_data.get('total_so_value', 0)}
Items Below Reorder Point: {mrp_data.get('below_reorder', [])}
Average Lead Time: {mrp_data.get('avg_lead_time_days', 7)} days
Planning Horizon: 30 days
Generate purchase recommendations for items needing replenishment."""

        response = await self._ask_llm(system, prompt, max_tokens=1200)
        result = await self._parse_json_response(response)
        await self._log_action("mrp_planning", "success", mrp_data, result,
                               int((time.time() - t0) * 1000))
        return result


# ── Agent Registry ────────────────────────────────────────────
AGENT_REGISTRY = {
    "lead_scoring":          LeadScoringAgent,
    "churn_prediction":      ChurnPredictionAgent,
    "pr_approval":           PRApprovalAgent,
    "three_way_match":       ThreeWayMatchAgent,
    "mrp_planning":          MRPPlanningAgent,
}


async def run_agent(agent_name: str, db: AsyncSession = None, **kwargs) -> dict:
    """Universal agent runner."""
    if agent_name not in AGENT_REGISTRY:
        return {"error": f"Unknown agent: {agent_name}"}
    agent_class = AGENT_REGISTRY[agent_name]
    agent = agent_class(db=db)
    return await agent.run(**kwargs)
