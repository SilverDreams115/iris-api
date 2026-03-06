from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import (NOT_ENOUGH_PERMISSIONS, SIGNAL_NOT_FOUND,
                                     STRATEGY_NOT_FOUND, STRATEGY_NOT_OWNED,
                                     TRADE_NOT_FOUND, TRADE_NOT_OWNED)
from app.crud.signal import (create_signal, delete_signal, get_all_signals,
                             get_signal_by_id, get_signals_by_owner,
                             get_strategy_by_id, get_trade_by_id,
                             update_signal)
from app.database import get_db
from app.models.user import User
from app.schemas.signal import (SignalCreate, SignalExecuteRequest,
                                SignalRejectRequest, SignalResponse,
                                SignalUpdate)
from app.schemas.trade import TradeResponse
from app.services.execution import execute_signal, reject_signal
from app.services.validators import (ensure_exists,
                                     ensure_owned_by_current_user,
                                     ensure_owner_or_admin,
                                     ensure_trade_matches_strategy)

router = APIRouter(prefix="/signals", tags=["Signals"])


def _ensure_strategy_and_trade_are_coherent(
    db: Session,
    strategy_id: int,
    trade_id: int | None,
):
    strategy = ensure_exists(
        get_strategy_by_id(db, strategy_id),
        STRATEGY_NOT_FOUND,
    )

    trade = None
    if trade_id is not None:
        trade = ensure_exists(
            get_trade_by_id(db, trade_id),
            TRADE_NOT_FOUND,
        )
        ensure_trade_matches_strategy(trade, strategy)

    return strategy, trade


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal_endpoint(
    signal_in: SignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    strategy, trade = _ensure_strategy_and_trade_are_coherent(
        db,
        signal_in.strategy_id,
        signal_in.trade_id,
    )

    ensure_owned_by_current_user(
        current_user,
        strategy.owner_id,
        STRATEGY_NOT_OWNED,
    )
    if trade is not None:
        ensure_owned_by_current_user(
            current_user,
            trade.owner_id,
            TRADE_NOT_OWNED,
        )

    return create_signal(db, current_user.id, signal_in)


@router.post(
    "/{signal_id}/execute",
    response_model=TradeResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_signal_endpoint(
    signal_id: int,
    execution_in: SignalExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = ensure_exists(get_signal_by_id(db, signal_id), SIGNAL_NOT_FOUND)
    ensure_owner_or_admin(current_user, signal.owner_id, NOT_ENOUGH_PERMISSIONS)
    return execute_signal(db, signal, execution_in)


@router.post(
    "/{signal_id}/reject",
    response_model=SignalResponse,
    status_code=status.HTTP_200_OK,
)
def reject_signal_endpoint(
    signal_id: int,
    rejection_in: SignalRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = ensure_exists(get_signal_by_id(db, signal_id), SIGNAL_NOT_FOUND)
    ensure_owner_or_admin(current_user, signal.owner_id, NOT_ENOUGH_PERMISSIONS)
    return reject_signal(db, signal, rejection_in.rejection_reason)


@router.get("/", response_model=list[SignalResponse])
def list_signals(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_all_signals(db, skip=skip, limit=limit)
    return get_signals_by_owner(db, current_user.id, skip=skip, limit=limit)


@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal_endpoint(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = ensure_exists(get_signal_by_id(db, signal_id), SIGNAL_NOT_FOUND)
    ensure_owner_or_admin(current_user, signal.owner_id, NOT_ENOUGH_PERMISSIONS)
    return signal


@router.patch("/{signal_id}", response_model=SignalResponse)
def update_signal_endpoint(
    signal_id: int,
    signal_in: SignalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = ensure_exists(get_signal_by_id(db, signal_id), SIGNAL_NOT_FOUND)
    ensure_owner_or_admin(current_user, signal.owner_id, NOT_ENOUGH_PERMISSIONS)

    target_strategy_id = (
        signal_in.strategy_id
        if signal_in.strategy_id is not None
        else signal.strategy_id
    )
    target_trade_id = (
        signal_in.trade_id if signal_in.trade_id is not None else signal.trade_id
    )

    strategy, trade = _ensure_strategy_and_trade_are_coherent(
        db,
        target_strategy_id,
        target_trade_id,
    )

    ensure_owned_by_current_user(
        current_user,
        strategy.owner_id,
        STRATEGY_NOT_OWNED,
    )
    if trade is not None:
        ensure_owned_by_current_user(
            current_user,
            trade.owner_id,
            TRADE_NOT_OWNED,
        )

    return update_signal(db, signal, signal_in)


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal_endpoint(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = ensure_exists(get_signal_by_id(db, signal_id), SIGNAL_NOT_FOUND)
    ensure_owner_or_admin(current_user, signal.owner_id, NOT_ENOUGH_PERMISSIONS)

    delete_signal(db, signal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
