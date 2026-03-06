from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.trade import (
    create_trade,
    delete_trade,
    get_all_trades,
    get_broker_account_by_id,
    get_strategy_by_id,
    get_trade_by_id,
    get_trades_by_owner,
    update_trade,
)
from app.database import get_db
from app.models.user import User
from app.schemas.trade import TradeCloseRequest, TradeCreate, TradeResponse, TradeUpdate
from app.services.trade_closer import close_trade


router = APIRouter(prefix="/trades", tags=["Trades"])


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade_endpoint(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if trade_in.side not in {"buy", "sell"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid side",
        )

    if trade_in.status not in {"open", "closed", "cancelled"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status",
        )

    strategy = get_strategy_by_id(db, trade_in.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )

    broker_account = get_broker_account_by_id(db, trade_in.broker_account_id)
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if current_user.role != "admin":
        if strategy.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to current user",
            )

        if broker_account.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Broker account does not belong to current user",
            )

    return create_trade(db, current_user.id, trade_in)


@router.post("/{trade_id}/close", response_model=TradeResponse, status_code=status.HTTP_200_OK)
def close_trade_endpoint(
    trade_id: int,
    close_in: TradeCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = get_trade_by_id(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    if current_user.role != "admin" and trade.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return close_trade(db, trade, close_in)


@router.get("/", response_model=list[TradeResponse])
def list_trades(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_all_trades(db, skip=skip, limit=limit)

    return get_trades_by_owner(db, current_user.id, skip=skip, limit=limit)


@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade_endpoint(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = get_trade_by_id(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    if current_user.role != "admin" and trade.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
def update_trade_endpoint(
    trade_id: int,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = get_trade_by_id(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    if current_user.role != "admin" and trade.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if trade_in.side is not None and trade_in.side not in {"buy", "sell"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid side",
        )

    if trade_in.status is not None and trade_in.status not in {"open", "closed", "cancelled"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status",
        )

    if trade_in.strategy_id is not None:
        strategy = get_strategy_by_id(db, trade_in.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found",
            )
        if current_user.role != "admin" and strategy.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Strategy does not belong to current user",
            )

    if trade_in.broker_account_id is not None:
        broker_account = get_broker_account_by_id(db, trade_in.broker_account_id)
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

    return update_trade(db, trade, trade_in)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade_endpoint(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = get_trade_by_id(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    if current_user.role != "admin" and trade.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    delete_trade(db, trade)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
