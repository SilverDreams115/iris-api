from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
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


router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_endpoint(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = get_portfolio_by_id(db, strategy_in.portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )

    broker_account = get_broker_account_by_id(db, strategy_in.broker_account_id)
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if current_user.role != "admin":
        if portfolio.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Portfolio does not belong to current user",
            )

        if broker_account.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Broker account does not belong to current user",
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
    strategy = get_strategy_by_id(db, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )

    if current_user.role != "admin" and strategy.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return strategy


@router.patch("/{strategy_id}", response_model=StrategyResponse)
def update_strategy_endpoint(
    strategy_id: int,
    strategy_in: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = get_strategy_by_id(db, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )

    if current_user.role != "admin" and strategy.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if strategy_in.portfolio_id is not None:
        portfolio = get_portfolio_by_id(db, strategy_in.portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found",
            )
        if current_user.role != "admin" and portfolio.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Portfolio does not belong to current user",
            )

    if strategy_in.broker_account_id is not None:
        broker_account = get_broker_account_by_id(db, strategy_in.broker_account_id)
        if not broker_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker account not found",
            )
        if current_user.role != "admin" and broker_account.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Broker account does not belong to current user",
            )

    return update_strategy(db, strategy, strategy_in)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_endpoint(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy = get_strategy_by_id(db, strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )

    if current_user.role != "admin" and strategy.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    delete_strategy(db, strategy)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
