from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.signal import Signal
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.schemas.signal import SignalExecuteRequest


def execute_signal(db: Session, signal: Signal, execution_in: SignalExecuteRequest) -> Trade:
    if signal.status not in {"pending", "triggered"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending or triggered signals can be executed",
        )

    if signal.trade_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Signal already has an associated trade",
        )

    strategy = db.query(Strategy).filter(Strategy.id == signal.strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )

    if not strategy.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Strategy is inactive",
        )

    if strategy.owner_id != signal.owner_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Signal owner and strategy owner do not match",
        )

    if strategy.symbol != signal.symbol:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Signal symbol does not match strategy symbol",
        )

    broker_account = (
        db.query(BrokerAccount)
        .filter(BrokerAccount.id == strategy.broker_account_id)
        .first()
    )
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if broker_account.owner_id != signal.owner_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Signal owner and broker account owner do not match",
        )

    if broker_account.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Broker account is not active",
        )

    trade = Trade(
        symbol=signal.symbol,
        side=signal.side,
        volume=execution_in.volume,
        entry_price=execution_in.entry_price,
        exit_price=None,
        stop_loss=execution_in.stop_loss,
        take_profit=execution_in.take_profit,
        status="open",
        pnl=None,
        owner_id=signal.owner_id,
        strategy_id=strategy.id,
        broker_account_id=broker_account.id,
    )

    try:
        db.add(trade)
        db.flush()

        signal.trade_id = trade.id
        signal.status = "executed"

        db.commit()
        db.refresh(trade)
        db.refresh(signal)
        return trade
    except Exception:
        db.rollback()
        raise
