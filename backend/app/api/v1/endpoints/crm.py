from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.crm import Lead, LeadStatus, SalesOrder
from app.agents.registry import lead_scoring_agent

router = APIRouter()

class LeadCreate(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    value: float = 0

class SalesOrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    total_amount: float = 0
    lead_id: Optional[int] = None

@router.get("/leads")
async def list_leads(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(100))
    leads = result.scalars().all()
    return [{"id": l.id, "company_name": l.company_name, "contact_name": l.contact_name,
             "email": l.email, "status": l.status.value if l.status else None, "value": l.value,
             "ai_score": l.ai_score, "ai_notes": l.ai_notes,
             "created_at": l.created_at} for l in leads]

@router.post("/leads", status_code=201)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    lead = Lead(**data.model_dump(), assigned_to=current_user.id)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    # Auto-score with AI
    result = await lead_scoring_agent.score_lead(
        {"id": lead.id, **data.model_dump()}, db, user_id=current_user.id
    )
    if result["success"] and isinstance(result["data"], dict):
        d = result["data"]
        lead.ai_score = d.get("score", 0)
        lead.ai_notes = d.get("rationale", "")
        await db.commit()
    return {"id": lead.id, "company_name": lead.company_name, "ai_score": lead.ai_score}

@router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, status: LeadStatus,
                              db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    lead.status = status
    await db.commit()
    return {"id": lead.id, "status": lead.status.value}

@router.get("/stats")
async def crm_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = await db.scalar(select(func.count(Lead.id)))
    won = await db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.WON))
    pipeline_value = await db.scalar(select(func.sum(Lead.value)).where(Lead.status.notin_([LeadStatus.WON, LeadStatus.LOST])))
    orders = await db.scalar(select(func.count(SalesOrder.id)))
    return {"total_leads": total or 0, "won_leads": won or 0,
            "pipeline_value": pipeline_value or 0, "total_orders": orders or 0}
