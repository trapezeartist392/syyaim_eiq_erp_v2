from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.purchase import Vendor, PurchaseRequisition, PurchaseOrder, PRStatus, POStatus
from app.agents.registry import pr_approval_agent

router = APIRouter()

class VendorCreate(BaseModel):
    name: str
    code: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    payment_terms: int = 30

class PRCreate(BaseModel):
    item_description: str
    quantity: float
    unit: str = "pcs"
    estimated_cost: Optional[float] = None
    department: Optional[str] = None
    required_by: Optional[datetime] = None

class POCreate(BaseModel):
    vendor_id: int
    pr_id: Optional[int] = None
    total_amount: float
    tax_amount: float = 0
    delivery_date: Optional[datetime] = None
    terms: Optional[str] = None

@router.get("/vendors")
async def list_vendors(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Vendor).where(Vendor.is_active == True).limit(100))
    vendors = result.scalars().all()
    return [{"id": v.id, "name": v.name, "code": v.code, "email": v.email,
             "rating": v.rating, "payment_terms": v.payment_terms} for v in vendors]

@router.post("/vendors", status_code=201)
async def create_vendor(data: VendorCreate, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    vendor = Vendor(**data.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return {"id": vendor.id, "name": vendor.name, "code": vendor.code}

@router.get("/requisitions")
async def list_prs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseRequisition).order_by(PurchaseRequisition.created_at.desc()).limit(100))
    prs = result.scalars().all()
    return [{"id": p.id, "pr_number": p.pr_number, "item_description": p.item_description,
             "quantity": p.quantity, "estimated_cost": p.estimated_cost,
             "status": p.status.value if p.status else None, "ai_recommendation": p.ai_recommendation,
             "created_at": p.created_at} for p in prs]

@router.post("/requisitions", status_code=201)
async def create_pr(data: PRCreate, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    # Generate PR number
    count = await db.scalar(select(func.count(PurchaseRequisition.id)))
    pr_number = f"PR-{datetime.now().year}-{(count or 0) + 1:05d}"
    pr = PurchaseRequisition(**data.model_dump(), pr_number=pr_number,
                              requested_by=current_user.id)
    db.add(pr)
    await db.commit()
    await db.refresh(pr)
    # AI review
    result = await pr_approval_agent.review_pr(
        {"id": pr.id, "pr_number": pr_number, **data.model_dump()}, db, user_id=current_user.id
    )
    if result["success"] and isinstance(result["data"], dict):
        pr.ai_recommendation = result["data"].get("rationale", "")
        await db.commit()
    return {"id": pr.id, "pr_number": pr.pr_number, "status": pr.status.value}

@router.patch("/requisitions/{pr_id}/approve")
async def approve_pr(pr_id: int, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseRequisition).where(PurchaseRequisition.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(404, "PR not found")
    pr.status = PRStatus.APPROVED
    pr.approved_by = current_user.id
    await db.commit()
    return {"id": pr.id, "status": pr.status.value}

@router.get("/orders")
async def list_pos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(100))
    pos = result.scalars().all()
    return [{"id": p.id, "po_number": p.po_number, "vendor_id": p.vendor_id,
             "total_amount": p.total_amount, "status": p.status.value if p.status else None,
             "three_way_match_status": p.three_way_match_status,
             "created_at": p.created_at} for p in pos]

@router.post("/orders", status_code=201)
async def create_po(data: POCreate, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    count = await db.scalar(select(func.count(PurchaseOrder.id)))
    po_number = f"PO-{datetime.now().year}-{(count or 0) + 1:05d}"
    po = PurchaseOrder(**data.model_dump(), po_number=po_number, created_by=current_user.id)
    db.add(po)
    await db.commit()
    await db.refresh(po)
    return {"id": po.id, "po_number": po.po_number}

@router.get("/stats")
async def purchase_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_prs = await db.scalar(select(func.count(PurchaseRequisition.id)))
    pending = await db.scalar(select(func.count(PurchaseRequisition.id)).where(PurchaseRequisition.status == PRStatus.PENDING_APPROVAL))
    total_pos = await db.scalar(select(func.count(PurchaseOrder.id)))
    po_value = await db.scalar(select(func.sum(PurchaseOrder.total_amount)))
    return {"total_prs": total_prs or 0, "pending_approval": pending or 0,
            "total_pos": total_pos or 0, "total_po_value": po_value or 0}
