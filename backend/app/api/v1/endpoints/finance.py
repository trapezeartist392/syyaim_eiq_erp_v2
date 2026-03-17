# backend/app/api/v1/endpoints/finance.py
# GL Accounts + Journal Entries endpoints

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_tenant_session

router = APIRouter()

# ── Pydantic Models ────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    code:         str
    name:         str
    account_type: str  # asset, liability, equity, income, expense

class JournalLine(BaseModel):
    account_id: int
    debit:      float = 0
    credit:     float = 0

class JournalCreate(BaseModel):
    description:  str
    total_amount: float
    lines:        List[JournalLine]

# ── GL Accounts ────────────────────────────────────────────────────────────────

@router.get("/accounts")
async def list_accounts(
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    result = await db.execute(text("""
        SELECT id, code, name, account_type, created_at
        FROM accounts
        ORDER BY code
    """))
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/accounts")
async def create_account(
    body: AccountCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    valid_types = ['asset','liability','equity','income','expense']
    if body.account_type not in valid_types:
        raise HTTPException(400, detail=f"account_type must be one of {valid_types}")

    result = await db.execute(text("""
        INSERT INTO accounts (code, name, account_type)
        VALUES (:code, :name, :account_type)
        RETURNING id, code, name, account_type
    """), {"code": body.code, "name": body.name, "account_type": body.account_type})
    await db.commit()
    row = result.fetchone()
    return dict(row._mapping)


@router.put("/accounts/{account_id}")
async def update_account(
    account_id: int,
    body: AccountCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    await db.execute(text("""
        UPDATE accounts SET name=:name, account_type=:account_type
        WHERE id=:id
    """), {"name": body.name, "account_type": body.account_type, "id": account_id})
    await db.commit()
    return {"message": "Account updated"}


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    await db.execute(text("DELETE FROM accounts WHERE id=:id"), {"id": account_id})
    await db.commit()
    return {"message": "Account deleted"}


# ── Journal Entries ────────────────────────────────────────────────────────────

@router.get("/journals")
async def list_journals(
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    result = await db.execute(text("""
        SELECT
            je.id, je.entry_number, je.entry_date, je.description,
            je.total_amount, je.created_at,
            COUNT(jl.id) as line_count
        FROM journal_entries je
        LEFT JOIN journal_lines jl ON jl.journal_entry_id = je.id
        GROUP BY je.id
        ORDER BY je.created_at DESC
        LIMIT 100
    """))
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/journals/{journal_id}")
async def get_journal(
    journal_id: int,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    je = await db.execute(text(
        "SELECT * FROM journal_entries WHERE id=:id"
    ), {"id": journal_id})
    entry = je.fetchone()
    if not entry:
        raise HTTPException(404, "Journal entry not found")

    lines = await db.execute(text("""
        SELECT jl.*, a.code as account_code, a.name as account_name, a.account_type
        FROM journal_lines jl
        JOIN accounts a ON a.id = jl.account_id
        WHERE jl.journal_entry_id = :id
    """), {"id": journal_id})

    return {
        **dict(entry._mapping),
        "lines": [dict(r._mapping) for r in lines.fetchall()]
    }


@router.post("/journals")
async def create_journal(
    body: JournalCreate,
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    # Validate double-entry balance
    total_debit  = sum(l.debit  for l in body.lines)
    total_credit = sum(l.credit for l in body.lines)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(400, detail=f"Journal not balanced: debit ₹{total_debit} ≠ credit ₹{total_credit}")

    # Generate entry number
    count_result = await db.execute(text("SELECT COUNT(*) as cnt FROM journal_entries"))
    count = count_result.fetchone().cnt
    entry_number = f"JE-{(count+1):04d}"

    # Insert journal entry
    je_result = await db.execute(text("""
        INSERT INTO journal_entries (entry_number, description, total_amount, entry_date)
        VALUES (:entry_number, :description, :total_amount, NOW())
        RETURNING id
    """), {
        "entry_number": entry_number,
        "description": body.description,
        "total_amount": body.total_amount
    })
    je_id = je_result.fetchone().id

    # Insert journal lines
    for line in body.lines:
        await db.execute(text("""
            INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit)
            VALUES (:je_id, :account_id, :debit, :credit)
        """), {
            "je_id": je_id,
            "account_id": line.account_id,
            "debit": line.debit,
            "credit": line.credit
        })

    await db.commit()
    return {"id": je_id, "entry_number": entry_number, "message": "Journal entry posted"}


# ── P&L Summary ────────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_financial_summary(
    request: Request,
    db: AsyncSession = Depends(get_tenant_session)
):
    """Get income vs expense totals from journal lines for P&L overview."""
    result = await db.execute(text("""
        SELECT
            a.account_type,
            SUM(jl.debit)  as total_debit,
            SUM(jl.credit) as total_credit
        FROM journal_lines jl
        JOIN accounts a ON a.id = jl.account_id
        GROUP BY a.account_type
    """))
    rows = result.fetchall()
    summary = {r.account_type: dict(r._mapping) for r in rows}

    income  = summary.get('income',  {}).get('total_credit', 0) or 0
    expense = summary.get('expense', {}).get('total_debit',  0) or 0
    net     = float(income) - float(expense)

    return {
        "income":  float(income),
        "expense": float(expense),
        "net_profit": net,
        "by_type": {k: {"debit": float(v["total_debit"] or 0), "credit": float(v["total_credit"] or 0)} for k,v in summary.items()}
    }
