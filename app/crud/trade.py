from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.schemas.enums import TradeSide, TradeStatus
from app.schemas.trade import TradeCreate, TradeUpdate


def _validate_trade_price_relationship(
    side: str,
    entry_price: Decimal | None,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
) -> None:
    if entry_price is None or stop_loss is None or take_profit is None:
        return

    if side == TradeSide.buy.value:
        if not (stop_loss < entry_price < take_profit):
            raise ValueError("Invalid price relationship for buy trade")

    elif side == TradeSide.sell.value:
        if not (take_profit < entry_price < stop_loss):
            raise ValueError("Invalid price relationship for sell trade")


def create_trade(db: Session, owner_id: int, trade_in: TradeCreate) -> Trade:
    db_trade = Trade(
        symbol=trade_in.symbol,
        side=trade_in.side.value,
        volume=trade_in.volume,
        entry_price=trade_in.entry_price,
        exit_price=trade_in.exit_price,
        stop_loss=trade_in.stop_loss,
        take_profit=trade_in.take_profit,
        status=trade_in.status.value,
        pnl=trade_in.pnl,
        owner_id=owner_id,
        strategy_id=trade_in.strategy_id,
        broker_account_id=trade_in.broker_account_id,
    )

    _validate_trade_price_relationship(
        db_trade.side,
        db_trade.entry_price,
        db_trade.stop_loss,
        db_trade.take_profit,
    )

    if trade_in.status == TradeStatus.closed:
        db_trade.closed_at = datetime.now(UTC)

    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trade_by_id(db: Session, trade_id: int) -> Trade | None:
    return db.query(Trade).filter(Trade.id == trade_id).first()


def get_trades_by_owner(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Trade]:
    return db.query(Trade).filter(Trade.owner_id == owner_id).offset(skip).limit(limit).all()


def get_all_trades(db: Session, skip: int = 0, limit: int = 100) -> list[Trade]:
    return db.query(Trade).offset(skip).limit(limit).all()


def get_strategy_by_id(db: Session, strategy_id: int) -> Strategy | None:
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def get_broker_account_by_id(db: Session, broker_account_id: int) -> BrokerAccount | None:
    return db.query(BrokerAccount).filter(BrokerAccount.id == broker_account_id).first()


def update_trade(db: Session, db_trade: Trade, trade_in: TradeUpdate) -> Trade:
    previous_status = db_trade.status

    if trade_in.symbol is not None:
        db_trade.symbol = trade_in.symbol
    if trade_in.side is not None:
        db_trade.side = trade_in.side.value
    if trade_in.volume is not None:
        db_trade.volume = trade_in.volume
    if trade_in.entry_price is not None:
        db_trade.entry_price = trade_in.entry_price
    if trade_in.exit_price is not None:
        db_trade.exit_price = trade_in.exit_price
    if trade_in.stop_loss is not None:
        db_trade.stop_loss = trade_in.stop_loss
    if trade_in.take_profit is not None:
        db_trade.take_profit = trade_in.take_profit
    if trade_in.pnl is not None:
        db_trade.pnl = trade_in.pnl
    if trade_in.strategy_id is not None:
        db_trade.strategy_id = trade_in.strategy_id
    if trade_in.broker_account_id is not None:
        db_trade.broker_account_id = trade_in.broker_account_id

    _validate_trade_price_relationship(
        db_trade.side,
        db_trade.entry_price,
        db_trade.stop_loss,
        db_trade.take_profit,
    )

    if trade_in.status is not None:
        db_trade.status = trade_in.status.value

    if db_trade.status == TradeStatus.closed.value:
        if db_trade.exit_price is None:
            raise ValueError("Closed trades require exit_price")
        if previous_status != TradeStatus.closed.value or db_trade.closed_at is None:
            db_trade.closed_at = datetime.now(UTC)
    else:
        db_trade.closed_at = None

    db.commit()
    db.refresh(db_trade)
    return db_trade


def delete_trade(db: Session, db_trade: Trade) -> None:
    db.delete(db_trade)
    db.commit()
