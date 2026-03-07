from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.signal import Signal
from app.models.trade import Trade
from app.schemas.signal import SignalExecuteRequest

logger = get_logger(__name__)


def _conflict(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def _validate_execution_prices(signal: Signal, execution_in: SignalExecuteRequest) -> None:
    entry_price: Decimal = execution_in.entry_price
    stop_loss: Decimal = execution_in.stop_loss
    take_profit: Decimal = execution_in.take_profit

    if signal.side == "buy":
        if not (stop_loss < entry_price < take_profit):
            raise _conflict("Invalid price relationship for buy signal")

    elif signal.side == "sell":
        if not (take_profit < entry_price < stop_loss):
            raise _conflict("Invalid price relationship for sell signal")


def execute_signal(db: Session, signal: Signal, execution_in: SignalExecuteRequest) -> Trade:
    if signal.status not in {"pending", "triggered"}:
        logger.warning(
            "Signal execution rejected. signal_id=%s status=%s",
            signal.id,
            signal.status,
        )
        raise _conflict("Only pending or triggered signals can be executed")

    strategy = signal.strategy
    broker_account = strategy.broker_account if strategy else None

    if strategy is None:
        logger.warning(
            "Signal execution rejected. signal_id=%s missing_strategy",
            signal.id,
        )
        raise _conflict("Signal strategy is not available")

    if not strategy.is_active:
        logger.warning(
            "Signal execution rejected. signal_id=%s strategy_id=%s inactive_strategy",
            signal.id,
            strategy.id,
        )
        raise _conflict("Strategy is inactive")

    if broker_account is None:
        logger.warning(
            ("Signal execution rejected. signal_id=%s " "strategy_id=%s missing_broker_account"),
            signal.id,
            strategy.id,
        )
        raise _conflict("Strategy broker account is not available")

    if broker_account.status != "active":
        logger.warning(
            ("Signal execution rejected. signal_id=%s " "broker_account_id=%s broker_status=%s"),
            signal.id,
            broker_account.id,
            broker_account.status,
        )
        raise _conflict("Broker account is not active")

    _validate_execution_prices(signal, execution_in)

    trade = Trade(
        symbol=signal.symbol,
        side=signal.side,
        volume=execution_in.volume,
        entry_price=execution_in.entry_price,
        stop_loss=execution_in.stop_loss,
        take_profit=execution_in.take_profit,
        status="open",
        owner_id=signal.owner_id,
        strategy_id=signal.strategy_id,
        broker_account_id=broker_account.id,
    )

    db.add(trade)
    db.flush()

    signal.status = "executed"
    signal.trade_id = trade.id
    signal.executed_at = datetime.now(UTC)
    if execution_in.notes is not None:
        signal.notes = execution_in.notes

    db.commit()
    db.refresh(trade)
    db.refresh(signal)

    logger.info(
        "Signal executed successfully. signal_id=%s trade_id=%s owner_id=%s",
        signal.id,
        trade.id,
        signal.owner_id,
    )

    return trade


def reject_signal(db: Session, signal: Signal, rejection_reason: str) -> Signal:
    if signal.status not in {"pending", "triggered"}:
        logger.warning(
            "Signal rejection rejected. signal_id=%s status=%s",
            signal.id,
            signal.status,
        )
        raise _conflict("Only pending or triggered signals can be rejected")

    signal.status = "rejected"
    signal.rejection_reason = rejection_reason
    signal.rejected_at = datetime.now(UTC)

    db.commit()
    db.refresh(signal)

    logger.info(
        "Signal rejected. signal_id=%s owner_id=%s reason=%s",
        signal.id,
        signal.owner_id,
        rejection_reason,
    )

    return signal
