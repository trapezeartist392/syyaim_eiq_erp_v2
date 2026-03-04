from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TenantStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Tenant(Base):
    """
    Public schema table — stores one row per customer company.
    Each tenant gets their own PostgreSQL schema: schema_name = slug
    e.g. acme -> search_path = acme
    """
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)               # Company name
    slug = Column(String(63), unique=True, nullable=False)   # acme -> schema name + subdomain
    email = Column(String(255), unique=True, nullable=False) # Billing/admin email
    phone = Column(String(20))

    # Subscription
    status = Column(
        SAEnum(TenantStatus, values_callable=lambda x: [e.value for e in x]),
        default=TenantStatus.TRIAL,
        nullable=False
    )
    plan = Column(String(50), default="growth")
    trial_ends_at = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))

    # Stripe
    stripe_customer_id = Column(String(100), unique=True, nullable=True)
    stripe_subscription_id = Column(String(100), unique=True, nullable=True)

    # Usage tracking (for AI agent billing)
    ai_actions_used = Column(Integer, default=0)
    ai_actions_limit = Column(Integer, default=2500)  # Growth plan limit

    # Schema state
    schema_created = Column(Boolean, default=False)

    # Meta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
