from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class ItemCategory(str, enum.Enum):
    RAW_MATERIAL = "raw_material"
    WIP = "wip"
    FINISHED_GOODS = "finished_goods"
    CONSUMABLES = "consumables"
    SPARES = "spares"

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(Enum(ItemCategory, values_callable=lambda x: [e.value for e in x]), default=ItemCategory.RAW_MATERIAL)
    unit = Column(String(20), default="pcs")
    current_stock = Column(Float, default=0)
    reorder_point = Column(Float, default=0)
    reorder_qty = Column(Float, default=0)
    unit_cost = Column(Float, default=0)
    location = Column(String(100))
    is_active = Column(Boolean, default=True)
    ai_forecast_qty = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    movement_type = Column(String(20))  # in / out / transfer / adjustment
    quantity = Column(Float, nullable=False)
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
