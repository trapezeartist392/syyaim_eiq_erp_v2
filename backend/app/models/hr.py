from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(20))
    department = Column(String(100))
    designation = Column(String(100))
    employment_type = Column(Enum(EmploymentType, values_callable=lambda x: [e.value for e in x]), default=EmploymentType.FULL_TIME)
    date_of_joining = Column(Date)
    date_of_birth = Column(Date)
    pan = Column(String(10))
    aadhaar = Column(String(12))
    bank_account = Column(String(20))
    ifsc_code = Column(String(11))
    basic_salary = Column(Float, default=0)
    hra = Column(Float, default=0)
    allowances = Column(Float, default=0)
    pf_applicable = Column(Boolean, default=True)
    esi_applicable = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Payroll(Base):
    __tablename__ = "payrolls"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(Integer)
    year = Column(Integer)
    working_days = Column(Float, default=26)
    present_days = Column(Float, default=26)
    basic = Column(Float, default=0)
    hra = Column(Float, default=0)
    allowances = Column(Float, default=0)
    gross_salary = Column(Float, default=0)
    pf_employee = Column(Float, default=0)
    pf_employer = Column(Float, default=0)
    esi_employee = Column(Float, default=0)
    esi_employer = Column(Float, default=0)
    tds = Column(Float, default=0)
    net_salary = Column(Float, default=0)
    status = Column(String(20), default="draft")
    processed_at = Column(DateTime(timezone=True))
    ai_anomaly_flag = Column(Boolean, default=False)
    ai_anomaly_notes = Column(Text)
