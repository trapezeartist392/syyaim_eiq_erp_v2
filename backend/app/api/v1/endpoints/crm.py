# backend/app/api/v1/endpoints/crm.py
# CRM — Leads + Sales Orders + Invoice generation

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_tenant_session

router = APIRouter()

# ── Pydantic Models ────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    company_name:  str
    gstin:         Optional[str] = None
    contact_name:  Optional[str] = None
    email:         Optional[str] = None
    phone:         Optional[str] = None
    source:        Optional[str] = None
    value:         Optional[float] = 0
    item_code:     Optional[str] = None
    item_name:     Optional[str] = None
    item_category: Optional[str] = None

class LeadUpdate(BaseModel):
    company_name:  Optional[str] = None
    gstin:         Optional[str] = None
    contact_name:  Optional[str] = None
    email:         Optional[str] = None
    phone:         Optional[str] = None
    source:        Optional[str] = None
    value:         Optional[float] = None
    status:        Optional[str] = None
    item_code:     Optional[str] = None
    item_name:     Optional[str] = None
    item_category: Optional[str] = None

class SalesOrderCreate(BaseModel):
    lead_id:      int
    order_number: Optional[str] = None
    amount:       float
    tax_amount:   Optional[float] = 0
    notes:        Optional[str] = None

class InvoiceCreate(BaseModel):
    sales_order_id: int
    invoice_number: Optional[str] = None
    amount:         float
    tax_amount:     Optional[float] = 0
    due_date:       Optional[str] = None

# ── Leads ──────────────────────────────────────────────────────────────────────

@router.get("/leads")
async def list_leads(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT id, company_name, gstin, contact_name, email, phone,
               source, status, value, ai_score, ai_notes,
               item_code, item_name, item_category, created_at, updated_at
        FROM leads ORDER BY created_at DESC
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/leads")
async def create_lead(body: LeadCreate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        INSERT INTO leads (company_name, gstin, contact_name, email, phone,
                           source, value, item_code, item_name, item_category, status)
        VALUES (:company_name, :gstin, :contact_name, :email, :phone,
                :source, :value, :item_code, :item_name, :item_category, 'new')
        RETURNING id, company_name, status
    """), body.dict())
    await db.commit()
    return dict(result.fetchone()._mapping)


@router.put("/leads/{lead_id}")
async def update_lead(lead_id: int, body: LeadUpdate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    sets = ", ".join(f"{k}=:{k}" for k in updates)
    await db.execute(text(f"UPDATE leads SET {sets}, updated_at=NOW() WHERE id=:id"), {**updates, "id": lead_id})
    await db.commit()
    return {"message": "Lead updated"}


# ── Sales Orders ───────────────────────────────────────────────────────────────

@router.get("/sales-orders")
async def list_sales_orders(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT so.*, l.company_name, l.contact_name, l.item_name, l.item_code
        FROM sales_orders so
        LEFT JOIN leads l ON l.id = so.lead_id
        ORDER BY so.created_at DESC
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/sales-orders")
async def create_sales_order(body: SalesOrderCreate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    # Get lead details
    lead = await db.execute(text("SELECT * FROM leads WHERE id=:id"), {"id": body.lead_id})
    lead = lead.fetchone()
    if not lead:
        raise HTTPException(404, "Lead not found")

    # Generate order number if not provided
    count = await db.execute(text("SELECT COUNT(*) as cnt FROM sales_orders"))
    cnt = count.fetchone().cnt
    order_number = body.order_number or f"SO-{(cnt+1):04d}"

    result = await db.execute(text("""
        INSERT INTO sales_orders (lead_id, order_number, amount, tax_amount, status, notes)
        VALUES (:lead_id, :order_number, :amount, :tax_amount, 'confirmed', :notes)
        RETURNING id, order_number
    """), {
        "lead_id": body.lead_id,
        "order_number": order_number,
        "amount": body.amount,
        "tax_amount": body.tax_amount,
        "notes": body.notes
    })
    await db.commit()
    row = result.fetchone()

    # Update lead status to won
    await db.execute(text("UPDATE leads SET status='won', updated_at=NOW() WHERE id=:id"), {"id": body.lead_id})
    await db.commit()

    return {
        "id": row.id,
        "order_number": row.order_number,
        "message": "Sales order created. Next step: generate invoice to trigger stock movement.",
        "next_step": "POST /crm/invoices"
    }


# ── Invoices ───────────────────────────────────────────────────────────────────
# Invoice generation triggers:
# 1. Stock OUT movement in material module
# 2. Revenue posting to GL (4001 Sales - Domestic)

@router.get("/invoices")
async def list_invoices(request: Request, db: AsyncSession = Depends(get_tenant_session)):
    result = await db.execute(text("""
        SELECT i.*, so.order_number, l.company_name, l.contact_name
        FROM sales_invoices i
        LEFT JOIN sales_orders so ON so.id = i.sales_order_id
        LEFT JOIN leads l ON l.id = so.lead_id
        ORDER BY i.created_at DESC
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/invoices")
async def create_invoice(body: InvoiceCreate, request: Request, db: AsyncSession = Depends(get_tenant_session)):
    """
    Generate invoice from sales order.
    Triggers:
      - Stock OUT movement (item qty reduced in material module)
      - Journal entry: Debit 1101 (Receivables) / Credit 4001 (Sales Revenue)
    """
    # Get sales order
    so = await db.execute(text("""
        SELECT so.*, l.item_code, l.item_name, l.company_name
        FROM sales_orders so
        LEFT JOIN leads l ON l.id = so.lead_id
        WHERE so.id = :id
    """), {"id": body.sales_order_id})
    so = so.fetchone()
    if not so:
        raise HTTPException(404, "Sales order not found")

    # Generate invoice number
    count = await db.execute(text("SELECT COUNT(*) as cnt FROM sales_invoices"))
    cnt = count.fetchone().cnt
    invoice_number = body.invoice_number or f"INV-{(cnt+1):04d}"

    # Create invoice
    inv_result = await db.execute(text("""
        INSERT INTO sales_invoices (sales_order_id, invoice_number, amount, tax_amount, status, due_date)
        VALUES (:sales_order_id, :invoice_number, :amount, :tax_amount, 'issued', :due_date::timestamptz)
        RETURNING id, invoice_number
    """), {
        "sales_order_id": body.sales_order_id,
        "invoice_number": invoice_number,
        "amount": body.amount,
        "tax_amount": body.tax_amount,
        "due_date": body.due_date
    })
    await db.commit()
    inv_row = inv_result.fetchone()

    stock_moved    = False
    gl_posted      = False
    reorder_pr     = None

    # ── Trigger 1: Stock OUT movement ─────────────────────────────────────────
    if so.item_code:
        item = await db.execute(text(
            "SELECT id, current_stock, reorder_point, reorder_qty FROM items WHERE code=:code"
        ), {"code": so.item_code})
        item = item.fetchone()

        if item and item.current_stock > 0:
            qty_out = min(1, item.current_stock)  # default 1 unit per invoice
            new_stock = item.current_stock - qty_out

            await db.execute(text("""
                INSERT INTO stock_movements (item_id, movement_type, quantity, reference, notes, created_at)
                VALUES (:item_id, 'OUT', :qty, :ref, :notes, NOW())
            """), {
                "item_id": item.id,
                "qty": qty_out,
                "ref": invoice_number,
                "notes": f"Stock OUT on invoice {invoice_number} for order {so.order_number}"
            })
            await db.execute(text("UPDATE items SET current_stock=:s WHERE id=:id"), {"s": new_stock, "id": item.id})
            await db.commit()
            stock_moved = True

            # Check reorder trigger
            if new_stock <= item.reorder_point:
                pr_number = f"PR-AUTO-{so.item_code}-{invoice_number}"
                await db.execute(text("""
                    INSERT INTO purchase_requisitions
                        (pr_number, item_description, quantity, unit, estimated_cost, department, status)
                    VALUES (:pr_number, :desc, :qty, 'units', 0, 'Purchase', 'draft')
                    ON CONFLICT (pr_number) DO NOTHING
                """), {
                    "pr_number": pr_number,
                    "desc": f"Auto-reorder: {so.item_code} after invoice {invoice_number}",
                    "qty": item.reorder_qty
                })
                await db.commit()
                reorder_pr = pr_number

    # ── Trigger 2: Post revenue to GL ─────────────────────────────────────────
    # Debit 1101 Accounts Receivable / Credit 4001 Sales - Domestic
    rec_account = await db.execute(text("SELECT id FROM accounts WHERE code='1101' LIMIT 1"))
    rec_account = rec_account.fetchone()
    sal_account = await db.execute(text("SELECT id FROM accounts WHERE code='4001' LIMIT 1"))
    sal_account = sal_account.fetchone()

    if rec_account and sal_account:
        count = await db.execute(text("SELECT COUNT(*) as cnt FROM journal_entries"))
        cnt = count.fetchone().cnt
        entry_number = f"JE-{(cnt+1):04d}"

        je = await db.execute(text("""
            INSERT INTO journal_entries (entry_number, description, total_amount, entry_date)
            VALUES (:en, :desc, :amount, NOW())
            RETURNING id
        """), {
            "en": entry_number,
            "desc": f"Sales revenue — {invoice_number} — {so.company_name}",
            "amount": body.amount
        })
        je_id = je.fetchone().id

        await db.execute(text("""
            INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit)
            VALUES (:je_id, :acc_id, :debit, 0)
        """), {"je_id": je_id, "acc_id": rec_account.id, "debit": body.amount})

        await db.execute(text("""
            INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit)
            VALUES (:je_id, :acc_id, 0, :credit)
        """), {"je_id": je_id, "acc_id": sal_account.id, "credit": body.amount})

        await db.commit()
        gl_posted = True

    return {
        "id": inv_row.id,
        "invoice_number": inv_row.invoice_number,
        "stock_moved": stock_moved,
        "reorder_pr_created": reorder_pr,
        "gl_posted": gl_posted,
        "message": f"Invoice {invoice_number} created. Stock OUT: {stock_moved}. GL posted: {gl_posted}."
    }
