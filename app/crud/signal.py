from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.schemas.enums import SignalStatus
from app.schemas.signal import SignalCreate, SignalUpdate


def create_signal(db: Session, owner_id: int, signal_in: SignalCreate):
    db_signal = Signal(
        symbol=signal_in.symbol,
        side=signal_in.side.value,
        confidence=signal_in.confidence,
        status=signal_in.status.value,
        source=signal_in.source.value,
        notes=signal_in.notes,
        owner_id=owner_id,
        strategy_id=signal_in.strategy_id,
        trade_id=signal_in.trade_id,
        rejection_reason=signal_in.rejection_reason,
    )

    if signal_in.status == SignalStatus.executed:
        db_signal.executed_at = datetime.now(timezone.utc)
    elif signal_in.status in {SignalStatus.rejected, SignalStatus.cancelled}:
        db_signal.rejected_at = datetime.now(timezone.utc)

    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    return db_signal


def get_signal_by_id(db: Session, signal_id: int):
    return db.query(Signal).filter(Signal.id == signal_id).first()


def get_signals_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Signal)
        .filter(Signal.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_signals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Signal).offset(skip).limit(limit).all()


def get_strategy_by_id(db: Session, strategy_id: int):
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def get_trade_by_id(db: Session, trade_id: int):
    return db.query(Trade).filter(Trade.id == trade_id).first()


def update_signal(db: Session, db_signal: Signal, signal_in: SignalUpdate):
    previous_status = db_signal.status

    if signal_in.symbol is not None:
        db_signal.symbol = signal_in.symbol
    if signal_in.side is not None:
        db_signal.side = signal_in.side.value
    if signal_in.confidence is not None:
        db_signal.confidence = signal_in.confidence
    if signal_in.source is not None:
        db_signal.source = signal_in.source.value
    if signal_in.notes is not None:
        db_signal.notes = signal_in.notes
    if signal_in.strategy_id is not None:
        db_signal.strategy_id = signal_in.strategy_id
    if signal_in.trade_id is not None:
        db_signal.trade_id = signal_in.trade_id
    if signal_in.rejection_reason is not None:
        db_signal.rejection_reason = signal_in.rejection_reason

    if signal_in.status is not None:
        db_signal.status = signal_in.status.value

    if db_signal.status == SignalStatus.executed.value:
        if (
            previous_status != SignalStatus.executed.value
            or db_signal.executed_at is None
        ):
            db_signal.executed_at = datetime.now(timezone.utc)
        db_signal.rejected_at = None
        db_signal.rejection_reason = None

    elif db_signal.status in {
        SignalStatus.rejected.value,
        SignalStatus.cancelled.value,
    }:
        if previous_status != db_signal.status or db_signal.rejected_at is None:
            db_signal.rejected_at = datetime.now(timezone.utc)
        db_signal.executed_at = None

    else:
        db_signal.executed_at = None
        db_signal.rejected_at = None
        db_signal.rejection_reason = None

    db.commit()
    db.refresh(db_signal)
    return db_signal


def delete_signal(db: Session, db_signal: Signal):
    db.delete(db_signal)
    db.commit()
