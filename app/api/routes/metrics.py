from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.broker_account import get_broker_account_by_id
from app.crud.metrics import (
    get_broker_account_metrics,
    get_overview_metrics,
    get_portfolio_metrics,
    get_strategy_metrics,
)
from app.crud.portfolio import get_portfolio_by_id
from app.crud.strategy import get_strategy_by_id
from app.database import get_db
from app.models.user import User
from app.schemas.metrics import MetricsResponse

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=MetricsResponse)
def metrics_summary(
    strategy_id: int | None = Query(default=None, ge=1),
    broker_account_id: int | None = Query(default=None, ge=1),
    portfolio_id: int | None = Query(default=None, ge=1),
    symbol: str | None = Query(default=None),
    closed_from: datetime | None = Query(default=None),
    closed_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owner_id = None if current_user.role == "admin" else current_user.id

    if strategy_id is not None:
        strategy = get_strategy_by_id(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        if current_user.role != "admin" and strategy.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    if broker_account_id is not None:
        broker_account = get_broker_account_by_id(db, broker_account_id)
        if not broker_account:
            raise HTTPException(status_code=404, detail="Broker account not found")
        if current_user.role != "admin" and broker_account.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    if portfolio_id is not None:
        portfolio = get_portfolio_by_id(db, portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        if current_user.role != "admin" and portfolio.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return get_overview_metrics(
        db,
        owner_id=owner_id,
        strategy_id=strategy_id,
        broker_account_id=broker_account_id,
        portfolio_id=portfolio_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )


@router.get("/overview", response_model=MetricsResponse)
def metrics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_overview_metrics(db)

    return get_overview_metrics(db, owner_id=current_user.id)


@router.get("/strategies/{strategy_id}", response_model=MetricsResponse)
def metrics_by_strategy(
    strategy_id: int,
    symbol: str | None = Query(default=None),
    closed_from: datetime | None = Query(default=None),
    closed_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = get_strategy_by_id(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if current_user.role != "admin" and strategy.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    owner_id = None if current_user.role == "admin" else current_user.id
    return get_strategy_metrics(
        db,
        strategy_id=strategy_id,
        owner_id=owner_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )


@router.get("/broker-accounts/{broker_account_id}", response_model=MetricsResponse)
def metrics_by_broker_account(
    broker_account_id: int,
    symbol: str | None = Query(default=None),
    closed_from: datetime | None = Query(default=None),
    closed_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = get_broker_account_by_id(db, broker_account_id)
    if not broker_account:
        raise HTTPException(status_code=404, detail="Broker account not found")

    if current_user.role != "admin" and broker_account.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    owner_id = None if current_user.role == "admin" else current_user.id
    return get_broker_account_metrics(
        db,
        broker_account_id=broker_account_id,
        owner_id=owner_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )


@router.get("/portfolios/{portfolio_id}", response_model=MetricsResponse)
def metrics_by_portfolio(
    portfolio_id: int,
    symbol: str | None = Query(default=None),
    closed_from: datetime | None = Query(default=None),
    closed_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = get_portfolio_by_id(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if current_user.role != "admin" and portfolio.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    owner_id = None if current_user.role == "admin" else current_user.id
    return get_portfolio_metrics(
        db,
        portfolio_id=portfolio_id,
        owner_id=owner_id,
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
