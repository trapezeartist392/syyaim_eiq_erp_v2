from app.agents.base import BaseAgent

class LeadScoringAgent(BaseAgent):
    name = "lead_scoring_agent"
    module = "crm"
    system_prompt = """You are an expert B2B sales analyst for a manufacturing ERP company.
Analyze leads and score them 0-100 based on: company size, industry fit, budget signals,
engagement, and pain points. Always respond with valid JSON only."""

    async def score_lead(self, lead_data: dict, db, user_id: int = None):
        prompt = f"""Score this manufacturing company lead for ERP software:

Lead: {lead_data}

Respond with JSON only:
{{
  "score": <0-100>,
  "grade": "<A/B/C/D>",
  "rationale": "<2-3 sentence explanation>",
  "recommended_action": "<next best action>",
  "estimated_deal_size": <number in INR lakhs>,
  "win_probability": <0-100>
}}"""
        return await self.run(prompt, db, entity_type="lead",
                              entity_id=lead_data.get("id"), user_id=user_id)
