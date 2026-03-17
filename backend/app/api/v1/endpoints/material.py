# backend/app/api/v1/endpoints/material.py
# Material Management — Items + Stock Movements
# Stock OUT triggered by invoice, not production
# Stock IN triggered by GRN after 3-way match

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_tenant_session

router = APIRouter()

# ── Pydantic Models ────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    code:          str
    name:          str
    category:      str   # raw_material, wip, finished_goods, consumables, spares
    unit:          str
    current_stock: float = 0
    reorder_point: float = 0
    reorder_qty:   float = 0
    unit_cost:     float = 0

class StockMovement(BaseModel):
    item_id:        int
    movement_type:  str    # IN or OUT
    quantity:       float
    reference:      Optional[str] = None   # invoice_no, grn_no, etc
    reference_type: Optional[str] = None   # invoice, grn, adjustment
    notes:          Optional[str] = None

# ── Items ──────────────────────────────────────────────────────────────────────

@router.get("/items")
async def list_items(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT id, code, name, category, unit, current_stock,
               reorder_point, reorder_qty, unit_cost, created_at
        FROM items ORDER BY code
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/items")
async def create_item(body: ItemCreate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        INSERT INTO items (code, name, category, unit, current_stock, reorder_point, reorder_qty, unit_cost)
        VALUES (:code, :name, :category, :unit, :current_stock, :reorder_point, :reorder_qty, :unit_cost)
        RETURNING id, code, name
    """), body.dict())
    await db.commit()
    return dict(result.fetchone()._mapping)


@router.put("/items/{item_id}")
async def update_item(item_id: int, body: ItemCreate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    await db.execute(text("""
        UPDATE items SET name=:name, category=:category, unit=:unit,
            current_stock=:current_stock, reorder_point=:reorder_point,
            reorder_qty=:reorder_qty, unit_cost=:unit_cost
        WHERE id=:id
    """), {**body.dict(), "id": item_id})
    await db.commit()
    return {"message": "Item updated"}


# ── Stock Movements ────────────────────────────────────────────────────────────

@router.get("/stock-movements")
async def list_movements(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT sm.*, i.code as item_code, i.name as item_name, i.unit
        FROM stock_movements sm
        JOIN items i ON i.id = sm.item_id
        ORDER BY sm.created_at DESC
        LIMIT 200
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/stock-movements")
async def create_movement(body: StockMovement, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    """
    Create a stock movement.
    - movement_type=IN:  triggered by GRN (after 3-way match confirmed)
    - movement_type=OUT: triggered by invoice (when goods dispatched to client)
    """
    if body.movement_type not in ['IN','OUT']:
        raise HTTPException(400, "movement_type must be IN or OUT")

    # Get current stock
    item = await db.execute(text("SELECT id, current_stock, reorder_point, reorder_qty, code FROM items WHERE id=:id"), {"id": body.item_id})
    item = item.fetchone()
    if not item:
        raise HTTPException(404, "Item not found")

    if body.movement_type == 'OUT' and item.current_stock < body.quantity:
        raise HTTPException(400, f"Insufficient stock. Available: {item.current_stock}, Requested: {body.quantity}")

    # Record movement
    await db.execute(text("""
        INSERT INTO stock_movements (item_id, movement_type, quantity, reference, notes, created_at)
        VALUES (:item_id, :movement_type, :quantity, :reference, :notes, NOW())
    """), {
        "item_id": body.item_id,
        "movement_type": body.movement_type,
        "quantity": body.quantity,
        "reference": body.reference,
        "notes": body.notes or f"{body.movement_type} via {body.reference_type or 'manual'}"
    })

    # Update current stock
    new_stock = item.current_stock + body.quantity if body.movement_type == 'IN' else item.current_stock - body.quantity
    await db.execute(text("UPDATE items SET current_stock=:stock WHERE id=:id"), {"stock": new_stock, "id": body.item_id})

    await db.commit()

    # Check reorder trigger after OUT movement
    reorder_triggered = False
    if body.movement_type == 'OUT' and new_stock <= item.reorder_point:
        reorder_triggered = True
        # Auto-create PR in purchase_requisitions
        pr_number = f"PR-AUTO-{item.code}-{body.reference or 'STK'}"
        await db.execute(text("""
            INSERT INTO purchase_requisitions
                (pr_number, item_description, quantity, unit, estimated_cost, department, status)
            VALUES
                (:pr_number, :description, :qty, 'units', 0, 'Purchase', 'draft')
            ON CONFLICT (pr_number) DO NOTHING
        """), {
            "pr_number": pr_number,
            "description": f"Auto-reorder: {item.code} — stock fell below reorder point",
            "qty": item.reorder_qty
        })
        await db.commit()

    return {
        "message": "Stock movement recorded",
        "movement_type": body.movement_type,
        "quantity": body.quantity,
        "new_stock": new_stock,
        "reorder_triggered": reorder_triggered,
        "reorder_pr": pr_number if reorder_triggered else None
    }


@router.get("/items/{item_id}/movements")
async def item_movements(item_id: int, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT sm.*, i.code as item_code, i.name as item_name
        FROM stock_movements sm
        JOIN items i ON i.id = sm.item_id
        WHERE sm.item_id = :id
        ORDER BY sm.created_at DESC
    """), {"id": item_id})
    return [dict(r._mapping) for r in result.fetchall()]


@router.get("/low-stock")
async def low_stock_items(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    """Items at or below reorder point — need replenishment."""
    result = await db.execute(text("""
        SELECT id, code, name, category, unit, current_stock, reorder_point, reorder_qty, unit_cost
        FROM items
        WHERE current_stock <= reorder_point
        ORDER BY (reorder_point - current_stock) DESC
    """))
    return [dict(r._mapping) for r in result.fetchall()]
