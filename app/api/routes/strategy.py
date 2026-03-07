from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import (
    BROKER_ACCOUNT_NOT_FOUND,
    BROKER_ACCOUNT_NOT_OWNED,
    NOT_ENOUGH_PERMISSIONS,
    PORTFOLIO_BROKER_OWNER_MISMATCH,
    PORTFOLIO_NOT_FOUND,
    PORTFOLIO_NOT_OWNED,
    STRATEGY_NOT_FOUND,
)
from app.crud.strategy import (
    create_strategy,
    delete_strategy,
    get_all_strategies,
    get_broker_account_by_id,
    get_portfolio_by_id,
    get_strategies_by_owner,
    get_strategy_by_id,
    update_strategy,
)
from app.database import get_db
from app.models.user import User
from app.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate
from app.services.validators import (
    ensure_exists,
    ensure_owned_by_current_user,
    ensure_owner_or_admin,
    ensure_same_owner,
)

router = APIRouter(prefix="/strategies", tags=["Strategies"])


def _ensure_portfolio_and_broker_are_coherent(
    db: Session,
    portfolio_id: int,
    broker_account_id: int,
):
    portfolio = ensure_exists(
        get_portfolio_by_id(db, portfolio_id),
        PORTFOLIO_NOT_FOUND,
    )
    broker_account = ensure_exists(
        get_broker_account_by_id(db, broker_account_id),
        BROKER_ACCOUNT_NOT_FOUND,
    )

    ensure_same_owner(
        portfolio.owner_id,
        broker_account.owner_id,
        PORTFOLIO_BROKER_OWNER_MISMATCH,
    )

    return portfolio, broker_account


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_endpoint(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio, broker_account = _ensure_portfolio_and_broker_are_coherent(
        db,
        strategy_in.portfolio_id,
        strategy_in.broker_account_id,
    )

    ensure_owned_by_current_user(
        current_user,
        portfolio.owner_id,
        PORTFOLIO_NOT_OWNED,
    )
    ensure_owned_by_current_user(
        current_user,
        broker_account.owner_id,
        BROKER_ACCOUNT_NOT_OWNED,
    )

    return create_strategy(db, current_user.id, strategy_in)


@router.get("/", response_model=list[StrategyResponse])
def list_strategies(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_all_strategies(db, skip=skip, limit=limit)
    return get_strategies_by_owner(db, current_user.id, skip=skip, limit=limit)


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy_endpoint(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = ensure_exists(get_strategy_by_id(db, strategy_id), STRATEGY_NOT_FOUND)
    ensure_owner_or_admin(current_user, strategy.owner_id, NOT_ENOUGH_PERMISSIONS)
    return strategy


@router.patch("/{strategy_id}", response_model=StrategyResponse)
def update_strategy_endpoint(
    strategy_id: int,
    strategy_in: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = ensure_exists(get_strategy_by_id(db, strategy_id), STRATEGY_NOT_FOUND)
    ensure_owner_or_admin(current_user, strategy.owner_id, NOT_ENOUGH_PERMISSIONS)

    target_portfolio_id = (
        strategy_in.portfolio_id if strategy_in.portfolio_id is not None else strategy.portfolio_id
    )
    target_broker_account_id = (
        strategy_in.broker_account_id
        if strategy_in.broker_account_id is not None
        else strategy.broker_account_id
    )

    portfolio, broker_account = _ensure_portfolio_and_broker_are_coherent(
        db,
        target_portfolio_id,
        target_broker_account_id,
    )

    ensure_owned_by_current_user(
        current_user,
        portfolio.owner_id,
        PORTFOLIO_NOT_OWNED,
    )
    ensure_owned_by_current_user(
        current_user,
        broker_account.owner_id,
        BROKER_ACCOUNT_NOT_OWNED,
    )

    return update_strategy(db, strategy, strategy_in)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_endpoint(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = ensure_exists(get_strategy_by_id(db, strategy_id), STRATEGY_NOT_FOUND)
    ensure_owner_or_admin(current_user, strategy.owner_id, NOT_ENOUGH_PERMISSIONS)

    delete_strategy(db, strategy)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
