from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class PRStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PO_CREATED = "po_created"

class POStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    INVOICED = "invoiced"
    PAID = "paid"
    CANCELLED = "cancelled"

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    gstin = Column(String(15))
    payment_terms = Column(Integer, default=30)
    rating = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"
    id = Column(Integer, primary_key=True, index=True)
    pr_number = Column(String(50), unique=True, index=True)
    item_description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="pcs")
    estimated_cost = Column(Float)
    department = Column(String(100))
    required_by = Column(DateTime(timezone=True))
    status = Column(Enum(PRStatus, values_callable=lambda x: [e.value for e in x]), default=PRStatus.DRAFT)
    ai_recommendation = Column(Text)
    requested_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    pr_id = Column(Integer, ForeignKey("purchase_requisitions.id"), nullable=True)
    total_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    status = Column(Enum(POStatus, values_callable=lambda x: [e.value for e in x]), default=POStatus.DRAFT)
    delivery_date = Column(DateTime(timezone=True))
    terms = Column(Text)
    three_way_match_status = Column(String(50), default="pending")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
