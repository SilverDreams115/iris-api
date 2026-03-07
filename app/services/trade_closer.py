from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.trade import Trade
from app.schemas.enums import TradeStatus
from app.schemas.trade import TradeCloseRequest

logger = get_logger(__name__)


def close_trade(db: Session, trade: Trade, close_in: TradeCloseRequest) -> Trade:
    if trade.status != TradeStatus.open.value:
        logger.warning(
            "Trade close rejected. trade_id=%s status=%s",
            trade.id,
            trade.status,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only open trades can be closed",
        )

    trade.exit_price = close_in.exit_price
    trade.pnl = close_in.pnl
    trade.status = TradeStatus.closed.value
    trade.closed_at = datetime.now(UTC)

    db.commit()
    db.refresh(trade)

    logger.info(
        "Trade closed successfully. trade_id=%s owner_id=%s pnl=%s",
        trade.id,
        trade.owner_id,
        trade.pnl,
    )

    return trade
