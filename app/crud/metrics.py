from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trade import Trade


def _build_metrics_from_query(base_query):
    total_trades = base_query.count()
    open_trades = base_query.filter(Trade.status == "open").count()
    closed_trades = base_query.filter(Trade.status == "closed").count()
    winning_trades = base_query.filter(Trade.status == "closed", Trade.pnl > 0).count()
    losing_trades = base_query.filter(Trade.status == "closed", Trade.pnl < 0).count()

    total_pnl = base_query.with_entities(func.coalesce(func.sum(Trade.pnl), 0)).scalar()
    average_pnl = base_query.with_entities(func.coalesce(func.avg(Trade.pnl), 0)).scalar()

    total_pnl = Decimal(str(total_pnl or 0))
    average_pnl = Decimal(str(average_pnl or 0))

    if closed_trades > 0:
        win_rate = (Decimal(winning_trades) / Decimal(closed_trades)) * Decimal("100")
    else:
        win_rate = Decimal("0")

    return {
        "total_trades": total_trades,
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "total_pnl": total_pnl.quantize(Decimal("0.01")),
        "average_pnl": average_pnl.quantize(Decimal("0.01")),
        "win_rate": win_rate.quantize(Decimal("0.01")),
    }


def get_overview_metrics(db: Session, owner_id: int | None = None):
    query = db.query(Trade)
    if owner_id is not None:
        query = query.filter(Trade.owner_id == owner_id)
    return _build_metrics_from_query(query)


def get_strategy_metrics(db: Session, strategy_id: int, owner_id: int | None = None):
    query = db.query(Trade).filter(Trade.strategy_id == strategy_id)
    if owner_id is not None:
        query = query.filter(Trade.owner_id == owner_id)
    return _build_metrics_from_query(query)


def get_broker_account_metrics(db: Session, broker_account_id: int, owner_id: int | None = None):
    query = db.query(Trade).filter(Trade.broker_account_id == broker_account_id)
    if owner_id is not None:
        query = query.filter(Trade.owner_id == owner_id)
    return _build_metrics_from_query(query)


def get_portfolio_metrics(db: Session, portfolio_id: int, owner_id: int | None = None):
    query = db.query(Trade).join(Trade.strategy).filter(Trade.strategy.has(portfolio_id=portfolio_id))
    if owner_id is not None:
        query = query.filter(Trade.owner_id == owner_id)
    return _build_metrics_from_query(query)
