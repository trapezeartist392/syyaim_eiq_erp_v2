from app.agents.base import BaseAgent

class FinancialReportingAgent(BaseAgent):
    name = "financial_reporting_agent"
    module = "finance"
    system_prompt = """You are a CFO-level financial analyst for a manufacturing company.
Analyze financial data and generate insights, ratios, and recommendations.
Respond with valid JSON only."""

    async def analyze(self, financial_data: dict, db, user_id: int = None):
        prompt = f"""Analyze this financial summary and provide insights:

Financial Data: {financial_data}

Respond with JSON only:
{{
  "health_score": <0-100>,
  "key_insights": ["<insight 1>", "<insight 2>", "<insight 3>"],
  "ratios": {{
    "gross_margin_pct": <number>,
    "operating_margin_pct": <number>
  }},
  "alerts": ["<any financial alerts>"],
  "recommendations": ["<action items for management>"],
  "summary": "<executive summary in 2-3 sentences>"
}}"""
        return await self.run(prompt, db, entity_type="financial_report",
                              max_tokens=2048, user_id=user_id)
