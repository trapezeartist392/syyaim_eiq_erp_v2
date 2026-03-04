from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.agent_log import AgentLog

router = APIRouter()

@router.get("/logs")
async def get_agent_logs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(AgentLog).order_by(AgentLog.created_at.desc()).limit(100))
    logs = result.scalars().all()
    return [{"id": l.id, "agent_name": l.agent_name, "action": l.action[:100],
             "module": l.module, "success": l.success, "tokens_used": l.tokens_used,
             "duration_ms": l.duration_ms, "created_at": l.created_at} for l in logs]

@router.get("/stats")
async def agent_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import func
    total = await db.scalar(select(func.count(AgentLog.id)))
    total_tokens = await db.scalar(select(func.sum(AgentLog.tokens_used)))
    success_count = await db.scalar(select(func.count(AgentLog.id)).where(AgentLog.success == True))
    return {"total_agent_actions": total or 0, "total_tokens_used": total_tokens or 0,
            "success_rate": round((success_count or 0) / max(total or 1, 1) * 100, 1)}
