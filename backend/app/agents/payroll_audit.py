from app.agents.base import BaseAgent

class PayrollAuditAgent(BaseAgent):
    name = "payroll_audit_agent"
    module = "hr"
    system_prompt = """You are a payroll compliance expert for Indian manufacturing companies.
Audit payroll calculations for accuracy, PF/ESI/TDS compliance, and anomalies.
Flag errors and suggest corrections. Respond with valid JSON only."""

    async def audit(self, payroll_data: dict, db, user_id: int = None):
        prompt = f"""Audit this payroll record for compliance and accuracy:

Payroll Data: {payroll_data}

Indian statutory rates:
- PF Employee: 12% of Basic (max basic: 15000)
- PF Employer: 12% of Basic
- ESI Employee: 0.75% of Gross (if gross <= 21000/month)
- ESI Employer: 3.25% of Gross
- TDS: As per income tax slab

Respond with JSON only:
{{
  "is_compliant": <true|false>,
  "anomalies": ["<list of issues found>"],
  "corrections": {{
    "pf_employee": <corrected_value_or_null>,
    "esi_employee": <corrected_value_or_null>,
    "tds": <corrected_value_or_null>,
    "net_salary": <corrected_value_or_null>
  }},
  "risk_level": "<low|medium|high>",
  "notes": "<summary>"
}}"""
        return await self.run(prompt, db, entity_type="payroll",
                              entity_id=payroll_data.get("id"), user_id=user_id)
