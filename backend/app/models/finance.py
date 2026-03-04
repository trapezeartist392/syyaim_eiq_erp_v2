from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class TransactionType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType, values_callable=lambda x: [e.value for e in x]))
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    balance = Column(Float, default=0)
    is_active = Column(Boolean, default=True)

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(50), unique=True, index=True)
    date = Column(Date, nullable=False)
    description = Column(Text)
    reference = Column(String(100))
    total_debit = Column(Float, default=0)
    total_credit = Column(Float, default=0)
    is_balanced = Column(Boolean, default=False)
    ai_generated = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JournalLine(Base):
    __tablename__ = "journal_lines"
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType, values_callable=lambda x: [e.value for e in x]))
    amount = Column(Float, nullable=False)
    narration = Column(Text)
