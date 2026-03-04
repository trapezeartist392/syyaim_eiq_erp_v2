from app.agents.base import BaseAgent

class PRApprovalAgent(BaseAgent):
    name = "pr_approval_agent"
    module = "purchase"
    system_prompt = """You are an intelligent purchase requisition reviewer for a manufacturing company.
Analyze PRs for completeness, budget compliance, urgency, and vendor availability.
Recommend approve, reject, or escalate. Respond with valid JSON only."""

    async def review_pr(self, pr_data: dict, db, user_id: int = None):
        prompt = f"""Review this Purchase Requisition:

PR Data: {pr_data}

Respond with JSON only:
{{
  "recommendation": "<approve|reject|escalate>",
  "confidence": <0-100>,
  "rationale": "<detailed reasoning>",
  "estimated_vendor": "<suggested vendor type>",
  "urgency_level": "<low|medium|high|critical>",
  "flags": ["<any concerns>"]
}}"""
        return await self.run(prompt, db, entity_type="purchase_requisition",
                              entity_id=pr_data.get("id"), user_id=user_id)
