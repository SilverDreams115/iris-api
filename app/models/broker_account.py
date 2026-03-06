from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id = Column(Integer, primary_key=True, index=True)
    broker_name = Column(String, nullable=False)
    account_label = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", back_populates="broker_accounts")
