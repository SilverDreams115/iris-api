from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import BROKER_ACCOUNT_NOT_FOUND, NOT_ENOUGH_PERMISSIONS
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
from app.services.validators import (
    ensure_access_to_resource,
    ensure_exists,
    resolve_owner_scope,
)

router = APIRouter(prefix="/broker-accounts", tags=["Broker Accounts"])


def _get_accessible_broker_account(
    db: Session,
    broker_account_id: int,
    current_user: User,
):
    broker_account = ensure_exists(
        get_broker_account_by_id(db, broker_account_id),
        BROKER_ACCOUNT_NOT_FOUND,
    )
    return ensure_access_to_resource(
        current_user,
        broker_account,
        NOT_ENOUGH_PERMISSIONS,
    )


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
    owner_id = resolve_owner_scope(current_user)

    if owner_id is None:
        return get_all_broker_accounts(db, skip=skip, limit=limit)

    return get_broker_accounts_by_owner(db, owner_id, skip=skip, limit=limit)


@router.get("/{broker_account_id}", response_model=BrokerAccountResponse)
def get_broker_account_endpoint(
    broker_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_accessible_broker_account(db, broker_account_id, current_user)


@router.patch("/{broker_account_id}", response_model=BrokerAccountResponse)
def update_broker_account_endpoint(
    broker_account_id: int,
    broker_account_in: BrokerAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = _get_accessible_broker_account(db, broker_account_id, current_user)
    return update_broker_account(db, broker_account, broker_account_in)


@router.delete("/{broker_account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broker_account_endpoint(
    broker_account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker_account = _get_accessible_broker_account(db, broker_account_id, current_user)
    delete_broker_account(db, broker_account)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
