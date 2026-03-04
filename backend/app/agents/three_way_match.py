from app.agents.base import BaseAgent

class ThreeWayMatchAgent(BaseAgent):
    name = "three_way_match_agent"
    module = "purchase"
    system_prompt = """You are an accounts payable expert performing 3-way matching
(PO vs GRN vs Invoice) for manufacturing. Identify discrepancies and recommend action.
Respond with valid JSON only."""

    async def match(self, po_data: dict, grn_data: dict, invoice_data: dict, db, user_id: int = None):
        prompt = f"""Perform 3-way match:

Purchase Order: {po_data}
Goods Receipt Note: {grn_data}
Invoice: {invoice_data}

Respond with JSON only:
{{
  "match_status": "<matched|partial_match|mismatch>",
  "quantity_variance": <number>,
  "price_variance": <number>,
  "discrepancies": ["<list of issues>"],
  "recommendation": "<approve_payment|hold|dispute>",
  "notes": "<explanation>"
}}"""
        return await self.run(prompt, db, entity_type="purchase_order",
                              entity_id=po_data.get("id"), user_id=user_id)
