from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.error_messages import NOT_ENOUGH_PERMISSIONS, USER_NOT_FOUND
from app.crud.user import (
    delete_user,
    get_user_by_id,
    get_users,
    set_user_active_status,
    update_user,
    update_user_role,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRoleUpdate, UserUpdate
from app.services.validators import ensure_exists, ensure_owner_or_admin

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    ensure_owner_or_admin(current_user, user.id, NOT_ENOUGH_PERMISSIONS)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    ensure_owner_or_admin(current_user, user.id, NOT_ENOUGH_PERMISSIONS)
    return update_user(db, user, user_in)


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role_endpoint(
    user_id: int,
    role_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    return update_user_role(db, user, role_in.role.value)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    return set_user_active_status(db, user, False)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    return set_user_active_status(db, user, True)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = ensure_exists(get_user_by_id(db, user_id), USER_NOT_FOUND)
    delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
