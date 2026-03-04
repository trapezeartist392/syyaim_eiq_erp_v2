from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    module = Column(String(50))
    entity_type = Column(String(50))
    entity_id = Column(Integer, nullable=True)
    input_data = Column(Text)
    output_data = Column(Text)
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Float, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
