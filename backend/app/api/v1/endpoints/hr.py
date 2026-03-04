from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.hr import Employee, Payroll, EmploymentType
from app.agents.registry import payroll_audit_agent

router = APIRouter()

class EmployeeCreate(BaseModel):
    employee_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    department: str
    designation: str
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    date_of_joining: Optional[date] = None
    basic_salary: float = 0
    hra: float = 0
    allowances: float = 0
    pf_applicable: bool = True
    esi_applicable: bool = False

class PayrollCreate(BaseModel):
    employee_id: int
    month: int
    year: int
    present_days: float = 26

@router.get("/employees")
async def list_employees(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Employee).where(Employee.is_active == True).limit(200))
    emps = result.scalars().all()
    return [{"id": e.id, "employee_id": e.employee_id, "full_name": e.full_name,
             "department": e.department, "designation": e.designation,
             "basic_salary": e.basic_salary, "is_active": e.is_active} for e in emps]

@router.post("/employees", status_code=201)
async def create_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    emp = Employee(**data.model_dump())
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return {"id": emp.id, "employee_id": emp.employee_id, "full_name": emp.full_name}

@router.post("/payroll/process", status_code=201)
async def process_payroll(data: PayrollCreate, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Employee).where(Employee.id == data.employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Employee not found")
    working_days = 26.0
    ratio = data.present_days / working_days
    basic = emp.basic_salary * ratio
    hra = emp.hra * ratio
    allowances = emp.allowances * ratio
    gross = basic + hra + allowances
    pf_emp = round(min(basic, 15000) * 0.12, 2) if emp.pf_applicable else 0
    pf_er = pf_emp
    esi_emp = round(gross * 0.0075, 2) if emp.esi_applicable and gross <= 21000 else 0
    tds = round(max(0, (gross * 12 - 250000) / 12 * 0.05), 2)
    net = round(gross - pf_emp - esi_emp - tds, 2)
    payroll = Payroll(
        employee_id=data.employee_id, month=data.month, year=data.year,
        working_days=working_days, present_days=data.present_days,
        basic=basic, hra=hra, allowances=allowances, gross_salary=gross,
        pf_employee=pf_emp, pf_employer=pf_er, esi_employee=esi_emp,
        tds=tds, net_salary=net, status="processed"
    )
    db.add(payroll)
    await db.commit()
    await db.refresh(payroll)
    # AI audit
    audit = await payroll_audit_agent.audit(
        {"id": payroll.id, "basic": basic, "hra": hra, "gross": gross,
         "pf_employee": pf_emp, "esi_employee": esi_emp, "tds": tds, "net": net,
         "pf_applicable": emp.pf_applicable, "esi_applicable": emp.esi_applicable},
        db, user_id=current_user.id
    )
    if audit["success"] and isinstance(audit["data"], dict):
        payroll.ai_anomaly_flag = not audit["data"].get("is_compliant", True)
        payroll.ai_anomaly_notes = str(audit["data"].get("anomalies", []))
        await db.commit()
    return {"id": payroll.id, "net_salary": payroll.net_salary,
            "gross_salary": gross, "ai_anomaly_flag": payroll.ai_anomaly_flag}

@router.get("/payroll")
async def list_payroll(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Payroll).order_by(Payroll.year.desc(), Payroll.month.desc()).limit(100))
    payrolls = result.scalars().all()
    return [{"id": p.id, "employee_id": p.employee_id, "month": p.month,
             "year": p.year, "gross_salary": p.gross_salary,
             "net_salary": p.net_salary, "status": p.status,
             "ai_anomaly_flag": p.ai_anomaly_flag} for p in payrolls]

@router.get("/stats")
async def hr_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_emp = await db.scalar(select(func.count(Employee.id)).where(Employee.is_active == True))
    total_payroll = await db.scalar(select(func.sum(Payroll.net_salary)))
    anomalies = await db.scalar(select(func.count(Payroll.id)).where(Payroll.ai_anomaly_flag == True))
    return {"total_employees": total_emp or 0, "total_payroll_disbursed": total_payroll or 0,
            "payroll_anomalies": anomalies or 0}
