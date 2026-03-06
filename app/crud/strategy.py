from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate


def create_strategy(db: Session, owner_id: int, strategy_in: StrategyCreate):
    db_strategy = Strategy(
        name=strategy_in.name,
        symbol=strategy_in.symbol,
        timeframe=strategy_in.timeframe,
        risk_percent=strategy_in.risk_percent,
        is_active=True,
        owner_id=owner_id,
        portfolio_id=strategy_in.portfolio_id,
        broker_account_id=strategy_in.broker_account_id,
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


def get_strategy_by_id(db: Session, strategy_id: int):
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def get_strategies_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Strategy)
        .filter(Strategy.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_strategies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Strategy).offset(skip).limit(limit).all()


def get_portfolio_by_id(db: Session, portfolio_id: int):
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_broker_account_by_id(db: Session, broker_account_id: int):
    return db.query(BrokerAccount).filter(BrokerAccount.id == broker_account_id).first()


def update_strategy(db: Session, db_strategy: Strategy, strategy_in: StrategyUpdate):
    if strategy_in.name is not None:
        db_strategy.name = strategy_in.name

    if strategy_in.symbol is not None:
        db_strategy.symbol = strategy_in.symbol

    if strategy_in.timeframe is not None:
        db_strategy.timeframe = strategy_in.timeframe

    if strategy_in.risk_percent is not None:
        db_strategy.risk_percent = strategy_in.risk_percent

    if strategy_in.is_active is not None:
        db_strategy.is_active = strategy_in.is_active

    if strategy_in.portfolio_id is not None:
        db_strategy.portfolio_id = strategy_in.portfolio_id

    if strategy_in.broker_account_id is not None:
        db_strategy.broker_account_id = strategy_in.broker_account_id

    db.commit()
    db.refresh(db_strategy)
    return db_strategy


def delete_strategy(db: Session, db_strategy: Strategy):
    db.delete(db_strategy)
    db.commit()
