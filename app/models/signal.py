from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)
    confidence = Column(Numeric(5, 2), nullable=False)
    status = Column(String, nullable=False, default="pending")
    source = Column(String, nullable=False, default="manual")
    notes = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="SET NULL"), nullable=True)

    owner = relationship("User", back_populates="signals")
    strategy = relationship("Strategy", back_populates="signals")
    trade = relationship("Trade", back_populates="signal", foreign_keys=[trade_id])
