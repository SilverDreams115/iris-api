from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import (
    BROKER_ACCOUNT_NOT_FOUND,
    NOT_ENOUGH_PERMISSIONS,
    PORTFOLIO_NOT_FOUND,
    STRATEGY_NOT_FOUND,
)
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
from app.services.validators import ensure_access_to_resource, ensure_exists, resolve_owner_scope

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
    owner_id = resolve_owner_scope(current_user)

    if strategy_id is not None:
        strategy = ensure_exists(get_strategy_by_id(db, strategy_id), STRATEGY_NOT_FOUND)
        ensure_access_to_resource(current_user, strategy, NOT_ENOUGH_PERMISSIONS)

    if broker_account_id is not None:
        broker_account = ensure_exists(
            get_broker_account_by_id(db, broker_account_id),
            BROKER_ACCOUNT_NOT_FOUND,
        )
        ensure_access_to_resource(current_user, broker_account, NOT_ENOUGH_PERMISSIONS)

    if portfolio_id is not None:
        portfolio = ensure_exists(get_portfolio_by_id(db, portfolio_id), PORTFOLIO_NOT_FOUND)
        ensure_access_to_resource(current_user, portfolio, NOT_ENOUGH_PERMISSIONS)

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
    return get_overview_metrics(db, owner_id=resolve_owner_scope(current_user))


@router.get("/strategies/{strategy_id}", response_model=MetricsResponse)
def metrics_by_strategy(
    strategy_id: int,
    symbol: str | None = Query(default=None),
    closed_from: datetime | None = Query(default=None),
    closed_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = ensure_exists(get_strategy_by_id(db, strategy_id), STRATEGY_NOT_FOUND)
    ensure_access_to_resource(current_user, strategy, NOT_ENOUGH_PERMISSIONS)

    return get_strategy_metrics(
        db,
        strategy_id=strategy_id,
        owner_id=resolve_owner_scope(current_user),
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
    broker_account = ensure_exists(
        get_broker_account_by_id(db, broker_account_id),
        BROKER_ACCOUNT_NOT_FOUND,
    )
    ensure_access_to_resource(current_user, broker_account, NOT_ENOUGH_PERMISSIONS)

    return get_broker_account_metrics(
        db,
        broker_account_id=broker_account_id,
        owner_id=resolve_owner_scope(current_user),
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
    portfolio = ensure_exists(get_portfolio_by_id(db, portfolio_id), PORTFOLIO_NOT_FOUND)
    ensure_access_to_resource(current_user, portfolio, NOT_ENOUGH_PERMISSIONS)

    return get_portfolio_metrics(
        db,
        portfolio_id=portfolio_id,
        owner_id=resolve_owner_scope(current_user),
        symbol=symbol,
        closed_from=closed_from,
        closed_to=closed_to,
    )
