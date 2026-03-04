from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.crm import Lead, LeadStatus, SalesOrder
from app.models.purchase import PurchaseRequisition, PRStatus, PurchaseOrder, POStatus
from app.models.material import Item
from app.models.hr import Employee
from app.models.finance import Account, AccountType
from app.models.agent_log import AgentLog

router = APIRouter()


@router.get("/kpis")
async def dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Sales
    open_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.status.notin_([LeadStatus.WON, LeadStatus.LOST]))
    ) or 0
    total_orders = await db.scalar(select(func.count(SalesOrder.id))) or 0
    total_sales_value = await db.scalar(select(func.sum(SalesOrder.total_amount))) or 0

    # Purchase
    total_pos = await db.scalar(select(func.count(PurchaseOrder.id))) or 0
    total_po_value = await db.scalar(select(func.sum(PurchaseOrder.total_amount))) or 0

    # HR
    active_employees = await db.scalar(
        select(func.count(Employee.id)).where(Employee.is_active == True)
    ) or 0

    # Finance
    income = await db.scalar(
        select(func.sum(Account.balance)).where(Account.account_type == AccountType.INCOME)
    ) or 0
    expense = await db.scalar(
        select(func.sum(Account.balance)).where(Account.account_type == AccountType.EXPENSE)
    ) or 0
    # Outstanding AR - sales orders not yet paid
    outstanding_value = await db.scalar(
        select(func.sum(SalesOrder.total_amount)).where(SalesOrder.status.notin_(["paid", "cancelled"]))
    ) or 0
    outstanding_invoices = await db.scalar(
        select(func.count(SalesOrder.id)).where(SalesOrder.status.notin_(["paid", "cancelled"]))
    ) or 0

    # AI Agents
    total_agent_actions = await db.scalar(select(func.count(AgentLog.id))) or 0
    tokens_consumed = await db.scalar(select(func.sum(AgentLog.tokens_used))) or 0
    successful = await db.scalar(
        select(func.count(AgentLog.id)).where(AgentLog.success == True)
    ) or 0
    success_rate = round((successful / total_agent_actions * 100) if total_agent_actions > 0 else 0, 1)

    return {
        "sales": {
            "open_leads": open_leads,
            "total_orders": total_orders,
            "total_value": total_sales_value,
        },
        "purchase": {
            "total_orders": total_pos,
            "total_value": total_po_value,
        },
        "hr": {
            "active_employees": active_employees,
        },
        "finance": {
            "total_income": income,
            "total_expense": expense,
            "net_profit": income - expense,
            "outstanding_value": outstanding_value,
            "outstanding_invoices": outstanding_invoices,
        },
        "ai": {
            "total_agent_actions": total_agent_actions,
            "tokens_consumed": tokens_consumed,
            "success_rate": success_rate,
        },
    }


@router.get("/agent-activity")
async def agent_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(AgentLog).order_by(AgentLog.created_at.desc()).limit(20)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "agent": log.agent_name,
            "action": log.action,
            "module": log.module,
            "status": "success" if log.success else "failed",
            "tokens_used": log.tokens_used,
            "duration_ms": log.duration_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint - kept for compatibility."""
    kpis = await dashboard_kpis(db=db, current_user=current_user)
    return {
        "total_leads": kpis["sales"]["open_leads"],
        "pipeline_value": kpis["sales"]["total_value"],
        "pending_prs": await db.scalar(
            select(func.count(PurchaseRequisition.id)).where(
                PurchaseRequisition.status == PRStatus.PENDING_APPROVAL
            )
        ) or 0,
        "low_stock_items": await db.scalar(
            select(func.count(Item.id)).where(Item.is_active == True, Item.current_stock <= Item.reorder_point)
        ) or 0,
        "total_employees": kpis["hr"]["active_employees"],
        "net_profit": kpis["finance"]["net_profit"],
        "total_income": kpis["finance"]["total_income"],
        "ai_agent_actions": kpis["ai"]["total_agent_actions"],
    }
