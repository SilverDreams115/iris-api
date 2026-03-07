from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.error_messages import NOT_ENOUGH_PERMISSIONS, PORTFOLIO_NOT_FOUND
from app.crud.portfolio import (
    create_portfolio,
    delete_portfolio,
    get_all_portfolios,
    get_portfolio_by_id,
    get_portfolios_by_owner,
    update_portfolio,
)
from app.database import get_db
from app.models.user import User
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate
from app.services.validators import ensure_access_to_resource, ensure_exists

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio_endpoint(
    portfolio_in: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_portfolio(db, current_user.id, portfolio_in)


@router.get("/", response_model=list[PortfolioResponse])
def list_portfolios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        return get_all_portfolios(db, skip=skip, limit=limit)

    return get_portfolios_by_owner(db, current_user.id, skip=skip, limit=limit)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = ensure_exists(get_portfolio_by_id(db, portfolio_id), PORTFOLIO_NOT_FOUND)
    ensure_access_to_resource(current_user, portfolio, NOT_ENOUGH_PERMISSIONS)
    return portfolio


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio_endpoint(
    portfolio_id: int,
    portfolio_in: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = ensure_exists(get_portfolio_by_id(db, portfolio_id), PORTFOLIO_NOT_FOUND)
    ensure_access_to_resource(current_user, portfolio, NOT_ENOUGH_PERMISSIONS)
    return update_portfolio(db, portfolio, portfolio_in)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_endpoint(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    portfolio = ensure_exists(get_portfolio_by_id(db, portfolio_id), PORTFOLIO_NOT_FOUND)
    ensure_access_to_resource(current_user, portfolio, NOT_ENOUGH_PERMISSIONS)
    delete_portfolio(db, portfolio)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
