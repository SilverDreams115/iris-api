from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.signal import (
    create_signal,
    delete_signal,
    get_all_signals,
    get_signal_by_id,
    get_signals_by_owner,
    get_strategy_by_id,
    get_trade_by_id,
    update_signal,
)
from app.database import get_db
from app.models.user import User
from app.schemas.signal import (
    SignalCreate,
    SignalExecuteRequest,
    SignalRejectRequest,
    SignalResponse,
    SignalUpdate,
)
from app.schemas.trade import TradeResponse
from app.services.execution import execute_signal, reject_signal

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal_endpoint(
    signal_in: SignalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if signal_in.side not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="Invalid side")

    if signal_in.status not in {"pending", "triggered", "executed", "cancelled", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    strategy = get_strategy_by_id(db, signal_in.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if current_user.role != "admin" and strategy.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Strategy does not belong to current user")

    if signal_in.trade_id is not None:
        trade = get_trade_by_id(db, signal_in.trade_id)
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        if current_user.role != "admin" and trade.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Trade does not belong to current user")

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
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if current_user.role != "admin" and signal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

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
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if current_user.role != "admin" and signal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

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
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if current_user.role != "admin" and signal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return signal


@router.patch("/{signal_id}", response_model=SignalResponse)
def update_signal_endpoint(
    signal_id: int,
    signal_in: SignalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if current_user.role != "admin" and signal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if signal_in.side is not None and signal_in.side not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="Invalid side")

    if signal_in.status is not None and signal_in.status not in {
        "pending",
        "triggered",
        "executed",
        "cancelled",
        "rejected",
    }:
        raise HTTPException(status_code=400, detail="Invalid status")

    if signal_in.strategy_id is not None:
        strategy = get_strategy_by_id(db, signal_in.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        if current_user.role != "admin" and strategy.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Strategy does not belong to current user")

    if signal_in.trade_id is not None:
        trade = get_trade_by_id(db, signal_in.trade_id)
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        if current_user.role != "admin" and trade.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Trade does not belong to current user")

    return update_signal(db, signal, signal_in)


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal_endpoint(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    if current_user.role != "admin" and signal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    delete_signal(db, signal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
