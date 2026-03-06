from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.schemas.trade import TradeCloseRequest


def close_trade(db: Session, trade: Trade, close_in: TradeCloseRequest) -> Trade:
    if trade.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only open trades can be closed",
        )

    trade.exit_price = close_in.exit_price
    trade.pnl = close_in.pnl
    trade.status = "closed"
    trade.closed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(trade)
    return trade
