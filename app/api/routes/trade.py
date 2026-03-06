from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import (BROKER_ACCOUNT_NOT_FOUND,
                                     BROKER_ACCOUNT_NOT_OWNED,
                                     NOT_ENOUGH_PERMISSIONS,
                                     STRATEGY_BROKER_OWNER_MISMATCH,
                                     STRATEGY_NOT_FOUND, STRATEGY_NOT_OWNED,
                                     TRADE_NOT_FOUND)
from app.core.exceptions import conflict, unprocessable
from app.crud.trade import (create_trade, delete_trade, get_all_trades,
                            get_broker_account_by_id, get_strategy_by_id,
                            get_trade_by_id, get_trades_by_owner, update_trade)
from app.database import get_db
from app.models.user import User
from app.schemas.enums import TradeStatus
from app.schemas.trade import (TradeCloseRequest, TradeCreate, TradeResponse,
                               TradeUpdate)
from app.services.trade_closer import close_trade
from app.services.validators import (ensure_exists,
                                     ensure_owned_by_current_user,
                                     ensure_owner_or_admin, ensure_same_owner)

router = APIRouter(prefix="/trades", tags=["Trades"])


def _ensure_strategy_and_broker_exist(
    db: Session, strategy_id: int, broker_account_id: int
):
    strategy = ensure_exists(
        get_strategy_by_id(db, strategy_id),
        STRATEGY_NOT_FOUND,
    )
    broker_account = ensure_exists(
        get_broker_account_by_id(db, broker_account_id),
        BROKER_ACCOUNT_NOT_FOUND,
    )

    ensure_same_owner(
        strategy.owner_id,
        broker_account.owner_id,
        STRATEGY_BROKER_OWNER_MISMATCH,
    )

    return strategy, broker_account


@router.post("/", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
def create_trade_endpoint(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy, broker_account = _ensure_strategy_and_broker_exist(
        db,
        trade_in.strategy_id,
        trade_in.broker_account_id,
    )

    ensure_owned_by_current_user(
        current_user,
        strategy.owner_id,
        STRATEGY_NOT_OWNED,
    )
    ensure_owned_by_current_user(
        current_user,
        broker_account.owner_id,
        BROKER_ACCOUNT_NOT_OWNED,
    )

    return create_trade(db, current_user.id, trade_in)


@router.post(
    "/{trade_id}/close", response_model=TradeResponse, status_code=status.HTTP_200_OK
)
def close_trade_endpoint(
    trade_id: int,
    close_in: TradeCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = ensure_exists(get_trade_by_id(db, trade_id), TRADE_NOT_FOUND)
    ensure_owner_or_admin(current_user, trade.owner_id, NOT_ENOUGH_PERMISSIONS)
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
    trade = ensure_exists(get_trade_by_id(db, trade_id), TRADE_NOT_FOUND)
    ensure_owner_or_admin(current_user, trade.owner_id, NOT_ENOUGH_PERMISSIONS)
    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
def update_trade_endpoint(
    trade_id: int,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = ensure_exists(get_trade_by_id(db, trade_id), TRADE_NOT_FOUND)
    ensure_owner_or_admin(current_user, trade.owner_id, NOT_ENOUGH_PERMISSIONS)

    target_strategy_id = (
        trade_in.strategy_id if trade_in.strategy_id is not None else trade.strategy_id
    )
    target_broker_account_id = (
        trade_in.broker_account_id
        if trade_in.broker_account_id is not None
        else trade.broker_account_id
    )

    strategy, broker_account = _ensure_strategy_and_broker_exist(
        db,
        target_strategy_id,
        target_broker_account_id,
    )

    ensure_owned_by_current_user(
        current_user,
        strategy.owner_id,
        STRATEGY_NOT_OWNED,
    )
    ensure_owned_by_current_user(
        current_user,
        broker_account.owner_id,
        BROKER_ACCOUNT_NOT_OWNED,
    )

    if trade_in.status == TradeStatus.closed:
        if trade.status == TradeStatus.closed.value:
            raise conflict("Trade is already closed")
        if trade_in.exit_price is None:
            raise unprocessable("Closed trades require exit_price")

    try:
        return update_trade(db, trade, trade_in)
    except ValueError as exc:
        raise unprocessable(str(exc)) from exc


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade_endpoint(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trade = ensure_exists(get_trade_by_id(db, trade_id), TRADE_NOT_FOUND)
    ensure_owner_or_admin(current_user, trade.owner_id, NOT_ENOUGH_PERMISSIONS)

    delete_trade(db, trade)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
