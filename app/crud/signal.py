from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.schemas.signal import SignalCreate, SignalUpdate


def create_signal(db: Session, owner_id: int, signal_in: SignalCreate):
    db_signal = Signal(
        symbol=signal_in.symbol,
        side=signal_in.side,
        confidence=signal_in.confidence,
        status=signal_in.status,
        source=signal_in.source,
        notes=signal_in.notes,
        owner_id=owner_id,
        strategy_id=signal_in.strategy_id,
        trade_id=signal_in.trade_id,
    )
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
    if signal_in.symbol is not None:
        db_signal.symbol = signal_in.symbol

    if signal_in.side is not None:
        db_signal.side = signal_in.side

    if signal_in.confidence is not None:
        db_signal.confidence = signal_in.confidence

    if signal_in.status is not None:
        db_signal.status = signal_in.status

    if signal_in.source is not None:
        db_signal.source = signal_in.source

    if signal_in.notes is not None:
        db_signal.notes = signal_in.notes

    if signal_in.strategy_id is not None:
        db_signal.strategy_id = signal_in.strategy_id

    if signal_in.trade_id is not None:
        db_signal.trade_id = signal_in.trade_id

    db.commit()
    db.refresh(db_signal)
    return db_signal


def delete_signal(db: Session, db_signal: Signal):
    db.delete(db_signal)
    db.commit()
