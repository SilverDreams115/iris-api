from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    volume = Column(Numeric(12, 4), nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    exit_price = Column(Numeric(18, 8), nullable=True)
    stop_loss = Column(Numeric(18, 8), nullable=True)
    take_profit = Column(Numeric(18, 8), nullable=True)
    status = Column(String, nullable=False, default="open")
    pnl = Column(Numeric(18, 8), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    broker_account_id = Column(Integer, ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    broker_account = relationship("BrokerAccount", back_populates="trades")
    signal = relationship("Signal", back_populates="trade", uselist=False)
