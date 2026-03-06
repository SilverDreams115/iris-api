from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.broker_account import (
    create_broker_account,
    delete_broker_account,
    get_all_broker_accounts,
    get_broker_account_by_id,
    get_broker_accounts_by_owner,
    update_broker_account,
)
from app.database import get_db
from app.models.user import User
from app.schemas.broker_account import (
    BrokerAccountCreate,
    BrokerAccountResponse,
    BrokerAccountUpdate,
)


router = APIRouter(prefix="/broker-accounts", tags=["Broker Accounts"])


@router.post("/", response_model=BrokerAccountResponse, status_code=status.HTTP_201_CREATED)
def create_broker_account_endpoint(
    broker_account_in: BrokerAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_broker_account(db, current_user.id, broker_account_in)


@router.get("/", response_model=list[BrokerAccountResponse])
def list_broker_accounts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_all_broker_accounts(db, skip=skip, limit=limit)

    return get_broker_accounts_by_owner(db, current_user.id, skip=skip, limit=limit)


@router.get("/{broker_account_id}", response_model=BrokerAccountResponse)
def get_broker_account_endpoint(
    broker_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = get_broker_account_by_id(db, broker_account_id)
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if current_user.role != "admin" and broker_account.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return broker_account


@router.patch("/{broker_account_id}", response_model=BrokerAccountResponse)
def update_broker_account_endpoint(
    broker_account_id: int,
    broker_account_in: BrokerAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = get_broker_account_by_id(db, broker_account_id)
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if current_user.role != "admin" and broker_account.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return update_broker_account(db, broker_account, broker_account_in)


@router.delete("/{broker_account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broker_account_endpoint(
    broker_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = get_broker_account_by_id(db, broker_account_id)
    if not broker_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker account not found",
        )

    if current_user.role != "admin" and broker_account.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    delete_broker_account(db, broker_account)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
