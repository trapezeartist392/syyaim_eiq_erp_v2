from app.agents.base import BaseAgent

class MRPPlanningAgent(BaseAgent):
    name = "mrp_planning_agent"
    module = "material"
    system_prompt = """You are a Material Requirements Planning (MRP) expert for manufacturing.
Analyze inventory levels, sales orders, production plans, and lead times to recommend
procurement actions. Respond with valid JSON only."""

    async def plan(self, inventory_data: list, sales_orders: list, db, user_id: int = None):
        prompt = f"""Analyze and generate MRP recommendations:

Current Inventory: {inventory_data[:10]}
Pending Sales Orders: {sales_orders[:10]}

Respond with JSON only:
{{
  "recommendations": [
    {{
      "item_code": "<code>",
      "item_name": "<name>",
      "current_stock": <number>,
      "recommended_order_qty": <number>,
      "urgency": "<low|medium|high|critical>",
      "reason": "<explanation>"
    }}
  ],
  "summary": "<overall supply health>",
  "critical_shortages": ["<items at risk>"]
}}"""
        return await self.run(prompt, db, entity_type="inventory",
                              max_tokens=2048, user_id=user_id)
