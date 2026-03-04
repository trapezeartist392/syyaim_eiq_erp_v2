from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    source = Column(String(100))
    status = Column(Enum(LeadStatus, values_callable=lambda x: [e.value for e in x]), default=LeadStatus.NEW)
    value = Column(Float, default=0)
    ai_score = Column(Integer, default=0)  # AI-generated score 0-100
    ai_notes = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255))
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="draft")
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
