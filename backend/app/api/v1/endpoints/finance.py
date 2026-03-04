from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.finance import Account, JournalEntry, JournalLine, AccountType, TransactionType
from app.agents.registry import financial_reporting_agent

router = APIRouter()

class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: AccountType
    parent_id: Optional[int] = None

@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Account).where(Account.is_active == True).limit(200))
    accounts = result.scalars().all()
    return [{"id": a.id, "code": a.code, "name": a.name,
             "account_type": a.account_type.value if a.account_type else None, "balance": a.balance} for a in accounts]

@router.post("/accounts", status_code=201)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    account = Account(**data.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "code": account.code, "name": account.name}

@router.get("/journal-entries")
async def list_journal_entries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(100))
    entries = result.scalars().all()
    return [{"id": e.id, "entry_number": e.entry_number, "date": e.date,
             "description": e.description, "total_debit": e.total_debit,
             "is_balanced": e.is_balanced, "ai_generated": e.ai_generated} for e in entries]

@router.get("/pl-summary")
async def pl_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.INCOME))
    expense = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.EXPENSE))
    asset = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.ASSET))
    liability = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.LIABILITY))
    income = income or 0; expense = expense or 0
    return {"total_income": income, "total_expense": expense,
            "net_profit": income - expense, "total_assets": asset or 0,
            "total_liabilities": liability or 0}

@router.get("/ai-insights")
async def financial_insights(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.INCOME)) or 0
    expense = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.EXPENSE)) or 0
    result = await financial_reporting_agent.analyze(
        {"total_income": income, "total_expense": expense, "net_profit": income - expense},
        db, user_id=current_user.id
    )
    return result

@router.get("/stats")
async def finance_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_accounts = await db.scalar(select(func.count(Account.id)).where(Account.is_active == True))
    total_entries = await db.scalar(select(func.count(JournalEntry.id)))
    income = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.INCOME)) or 0
    expense = await db.scalar(select(func.sum(Account.balance)).where(Account.account_type == AccountType.EXPENSE)) or 0
    return {"total_accounts": total_accounts or 0, "total_journal_entries": total_entries or 0,
            "net_profit": income - expense, "total_income": income}
