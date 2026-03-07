from sqlalchemy.orm import Session

from app.core.error_messages import STRATEGY_NAME_ALREADY_EXISTS
from app.core.exceptions import conflict
from app.models.broker_account import BrokerAccount
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate


def get_strategy_by_id(db: Session, strategy_id: int) -> Strategy | None:
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def get_strategies_by_owner(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Strategy]:
    return db.query(Strategy).filter(Strategy.owner_id == owner_id).offset(skip).limit(limit).all()


def get_all_strategies(db: Session, skip: int = 0, limit: int = 100) -> list[Strategy]:
    return db.query(Strategy).offset(skip).limit(limit).all()


def get_portfolio_by_id(db: Session, portfolio_id: int) -> Portfolio | None:
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_broker_account_by_id(db: Session, broker_account_id: int) -> BrokerAccount | None:
    return db.query(BrokerAccount).filter(BrokerAccount.id == broker_account_id).first()


def get_strategy_by_owner_and_name(db: Session, owner_id: int, name: str) -> Strategy | None:
    return db.query(Strategy).filter(Strategy.owner_id == owner_id, Strategy.name == name).first()


def create_strategy(db: Session, owner_id: int, strategy_in: StrategyCreate) -> Strategy:
    existing = get_strategy_by_owner_and_name(db, owner_id, strategy_in.name)
    if existing is not None:
        raise conflict(STRATEGY_NAME_ALREADY_EXISTS)

    db_strategy = Strategy(
        name=strategy_in.name,
        symbol=strategy_in.symbol,
        timeframe=strategy_in.timeframe.value,
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


def update_strategy(db: Session, db_strategy: Strategy, strategy_in: StrategyUpdate) -> Strategy:
    if strategy_in.name is not None and strategy_in.name != db_strategy.name:
        existing = get_strategy_by_owner_and_name(db, db_strategy.owner_id, strategy_in.name)
        if existing is not None and existing.id != db_strategy.id:
            raise conflict(STRATEGY_NAME_ALREADY_EXISTS)
        db_strategy.name = strategy_in.name

    if strategy_in.symbol is not None:
        db_strategy.symbol = strategy_in.symbol
    if strategy_in.timeframe is not None:
        db_strategy.timeframe = strategy_in.timeframe.value
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


def delete_strategy(db: Session, db_strategy: Strategy) -> None:
    db.delete(db_strategy)
    db.commit()
