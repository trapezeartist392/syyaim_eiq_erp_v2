"""Base AI Agent - all agents inherit from this."""
import time
import json
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import anthropic
from app.core.config import settings
from app.models.agent_log import AgentLog

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

class BaseAgent:
    name: str = "base_agent"
    module: str = "system"
    system_prompt: str = "You are a helpful ERP assistant."

    async def run(self, prompt: str, db: AsyncSession,
                  entity_type: str = None, entity_id: int = None,
                  user_id: int = None, max_tokens: int = 1024) -> dict:
        start = time.time()
        try:
            response = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            output = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            duration = (time.time() - start) * 1000

            # Try to parse JSON from output
            result = {"raw": output}
            try:
                # Find JSON block if present
                if "```json" in output:
                    json_str = output.split("```json")[1].split("```")[0].strip()
                    result = json.loads(json_str)
                elif output.strip().startswith("{"):
                    result = json.loads(output.strip())
            except Exception:
                pass

            await db.execute(
                AgentLog.__table__.insert().values(
                    agent_name=self.name, action=prompt[:200], module=self.module,
                    entity_type=entity_type, entity_id=entity_id,
                    output_data=output[:2000], tokens_used=tokens,
                    duration_ms=duration, success=True, triggered_by=user_id
                )
            )
            await db.commit()
            return {"success": True, "data": result, "raw": output, "tokens": tokens}

        except Exception as e:
            await db.execute(
                AgentLog.__table__.insert().values(
                    agent_name=self.name, action=prompt[:200], module=self.module,
                    entity_type=entity_type, entity_id=entity_id,
                    success=False, error_message=str(e), triggered_by=user_id
                )
            )
            await db.commit()
            return {"success": False, "error": str(e)}
