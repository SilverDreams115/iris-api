from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trade import Trade


def _q(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _apply_trade_filters(
    query,
    owner_id: Optional[int] = None,
    strategy_id: Optional[int] = None,
    broker_account_id: Optional[int] = None,
    portfolio_id: Optional[int] = None,
    symbol: Optional[str] = None,
    closed_from=None,
    closed_to=None,
):
    if owner_id is not None:
        query = query.filter(Trade.owner_id == owner_id)

    if strategy_id is not None:
        query = query.filter(Trade.strategy_id == strategy_id)

    if broker_account_id is not None:
        query = query.filter(Trade.broker_account_id == broker_account_id)

    if portfolio_id is not None:
        query = query.join(Trade.strategy).filter(
            Trade.strategy.has(portfolio_id=portfolio_id)
        )

    if symbol is not None:
        query = query.filter(Trade.symbol == symbol)

    if closed_from is not None:
        query = query.filter(
            Trade.closed_at.is_not(None), Trade.closed_at >= closed_from
        )

    if closed_to is not None:
        query = query.filter(Trade.closed_at.is_not(None), Trade.closed_at <= closed_to)

    return query


def _calculate_max_drawdown(base_query) -> Decimal:
    closed_trades = (
        base_query.filter(Trade.status == "closed", Trade.pnl.is_not(None))
        .order_by(Trade.closed_at.asc(), Trade.id.asc())
        .all()
    )

    equity = Decimal("0")
    peak = Decimal("0")
    max_drawdown = Decimal("0")

    for trade in closed_trades:
        pnl = Decimal(str(trade.pnl or 0))
        equity += pnl
        if equity > peak:
            peak = equity

        drawdown = peak - equity
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown.quantize(Decimal("0.01"))


def _build_metrics_from_query(base_query):
    total_trades = base_query.count()
    open_trades = base_query.filter(Trade.status == "open").count()
    closed_trades = base_query.filter(Trade.status == "closed").count()
    winning_trades = base_query.filter(Trade.status == "closed", Trade.pnl > 0).count()
    losing_trades = base_query.filter(Trade.status == "closed", Trade.pnl < 0).count()

    total_pnl_raw = base_query.with_entities(
        func.coalesce(func.sum(Trade.pnl), 0)
    ).scalar()
    average_pnl_raw = base_query.with_entities(
        func.coalesce(func.avg(Trade.pnl), 0)
    ).scalar()

    gross_profit_raw = (
        base_query.filter(Trade.status == "closed", Trade.pnl > 0)
        .with_entities(func.coalesce(func.sum(Trade.pnl), 0))
        .scalar()
    )
    gross_loss_raw = (
        base_query.filter(Trade.status == "closed", Trade.pnl < 0)
        .with_entities(func.coalesce(func.sum(Trade.pnl), 0))
        .scalar()
    )

    average_win_raw = (
        base_query.filter(Trade.status == "closed", Trade.pnl > 0)
        .with_entities(func.coalesce(func.avg(Trade.pnl), 0))
        .scalar()
    )
    average_loss_raw = (
        base_query.filter(Trade.status == "closed", Trade.pnl < 0)
        .with_entities(func.coalesce(func.avg(Trade.pnl), 0))
        .scalar()
    )

    total_pnl = Decimal(str(total_pnl_raw or 0))
    average_pnl = Decimal(str(average_pnl_raw or 0))
    gross_profit = Decimal(str(gross_profit_raw or 0))
    gross_loss = Decimal(str(gross_loss_raw or 0))
    average_win = Decimal(str(average_win_raw or 0))
    average_loss = Decimal(str(average_loss_raw or 0))

    if closed_trades > 0:
        win_rate = (Decimal(winning_trades) / Decimal(closed_trades)) * Decimal("100")
        expectancy = total_pnl / Decimal(closed_trades)
    else:
        win_rate = Decimal("0")
        expectancy = Decimal("0")

    if gross_loss < 0:
        profit_factor = gross_profit / abs(gross_loss)
    elif gross_profit > 0:
        profit_factor = Decimal("999999.99")
    else:
        profit_factor = Decimal("0")

    max_drawdown = _calculate_max_drawdown(base_query)

    return {
        "total_trades": total_trades,
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "total_pnl": total_pnl.quantize(Decimal("0.01")),
        "average_pnl": average_pnl.quantize(Decimal("0.01")),
        "win_rate": win_rate.quantize(Decimal("0.01")),
        "average_win": average_win.quantize(Decimal("0.01")),
        "average_loss": average_loss.quantize(Decimal("0.01")),
        "profit_factor": profit_factor.quantize(Decimal("0.01")),
        "expectancy": expectancy.quantize(Decimal("0.01")),
        "max_drawdown": max_drawdown,
    }


def get_overview_metrics(
    db: Session,
    owner_id: int | None = None,
    strategy_id: int | None = None,
    broker_account_id: int | None = None,
    portfolio_id: int | None = None,
    symbol: str | None = None,
    closed_from=None,
    closed_to=None,
):
    query = db.query(Trade)
    query = _apply_trade_filters(
        query,
        owner_id=owner_id,
        strategy_id=strategy_id,
        broker_account_id=broker_account_id,
        portfolio_id=portfolio_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
    return _build_metrics_from_query(query)


def get_strategy_metrics(
    db: Session,
    strategy_id: int,
    owner_id: int | None = None,
    symbol: str | None = None,
    closed_from=None,
    closed_to=None,
):
    query = db.query(Trade)
    query = _apply_trade_filters(
        query,
        owner_id=owner_id,
        strategy_id=strategy_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
    return _build_metrics_from_query(query)


def get_broker_account_metrics(
    db: Session,
    broker_account_id: int,
    owner_id: int | None = None,
    symbol: str | None = None,
    closed_from=None,
    closed_to=None,
):
    query = db.query(Trade)
    query = _apply_trade_filters(
        query,
        owner_id=owner_id,
        broker_account_id=broker_account_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
    return _build_metrics_from_query(query)


def get_portfolio_metrics(
    db: Session,
    portfolio_id: int,
    owner_id: int | None = None,
    symbol: str | None = None,
    closed_from=None,
    closed_to=None,
):
    query = db.query(Trade)
    query = _apply_trade_filters(
        query,
        owner_id=owner_id,
        portfolio_id=portfolio_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
    return _build_metrics_from_query(query)
