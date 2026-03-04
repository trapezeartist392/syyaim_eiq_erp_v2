from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.material import Item, StockMovement, ItemCategory
from app.agents.registry import mrp_planning_agent

router = APIRouter()

class ItemCreate(BaseModel):
    code: str
    name: str
    category: ItemCategory = ItemCategory.RAW_MATERIAL
    unit: str = "pcs"
    current_stock: float = 0
    reorder_point: float = 0
    reorder_qty: float = 0
    unit_cost: float = 0
    location: Optional[str] = None

class StockMovementCreate(BaseModel):
    item_id: int
    movement_type: str  # in/out/adjustment
    quantity: float
    reference: Optional[str] = None
    notes: Optional[str] = None

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Item).where(Item.is_active == True).limit(200))
    items = result.scalars().all()
    return [{"id": i.id, "code": i.code, "name": i.name, "category": i.category.value if i.category else None,
             "unit": i.unit, "current_stock": i.current_stock,
             "reorder_point": i.reorder_point, "unit_cost": i.unit_cost,
             "location": i.location,
             "below_reorder": i.current_stock <= i.reorder_point} for i in items]

@router.post("/items", status_code=201)
async def create_item(data: ItemCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    item = Item(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "code": item.code, "name": item.name}

@router.post("/movements", status_code=201)
async def record_movement(data: StockMovementCreate, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Item).where(Item.id == data.item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    # Update stock
    if data.movement_type == "in":
        item.current_stock += data.quantity
    elif data.movement_type == "out":
        if item.current_stock < data.quantity:
            raise HTTPException(400, "Insufficient stock")
        item.current_stock -= data.quantity
    else:
        item.current_stock = data.quantity  # adjustment
    movement = StockMovement(**data.model_dump(), created_by=current_user.id)
    db.add(movement)
    await db.commit()
    return {"item_id": item.id, "new_stock": item.current_stock, "movement_type": data.movement_type}

@router.get("/mrp-plan")
async def run_mrp(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Item).where(Item.is_active == True,
                                                   Item.current_stock <= Item.reorder_point))
    low_items = result.scalars().all()
    inventory_data = [{"code": i.code, "name": i.name, "current_stock": i.current_stock,
                       "reorder_point": i.reorder_point, "reorder_qty": i.reorder_qty} for i in low_items]
    mrp_result = await mrp_planning_agent.plan(inventory_data, [], db, user_id=current_user.id)
    return mrp_result

@router.get("/stats")
async def material_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = await db.scalar(select(func.count(Item.id)).where(Item.is_active == True))
    low_stock = await db.scalar(select(func.count(Item.id)).where(
        Item.is_active == True, Item.current_stock <= Item.reorder_point))
    total_value = await db.scalar(select(func.sum(Item.current_stock * Item.unit_cost)).where(Item.is_active == True))
    return {"total_items": total or 0, "low_stock_items": low_stock or 0,
            "inventory_value": total_value or 0}
