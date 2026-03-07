from sqlalchemy.orm import Session

from app.core.error_messages import PORTFOLIO_NAME_ALREADY_EXISTS
from app.core.exceptions import conflict
from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


def get_portfolio_by_id(db: Session, portfolio_id: int) -> Portfolio | None:
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_portfolios_by_owner(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Portfolio]:
    return (
        db.query(Portfolio).filter(Portfolio.owner_id == owner_id).offset(skip).limit(limit).all()
    )


def get_all_portfolios(db: Session, skip: int = 0, limit: int = 100) -> list[Portfolio]:
    return db.query(Portfolio).offset(skip).limit(limit).all()


def get_portfolio_by_owner_and_name(db: Session, owner_id: int, name: str) -> Portfolio | None:
    return (
        db.query(Portfolio).filter(Portfolio.owner_id == owner_id, Portfolio.name == name).first()
    )


def create_portfolio(db: Session, owner_id: int, portfolio_in: PortfolioCreate) -> Portfolio:
    existing = get_portfolio_by_owner_and_name(db, owner_id, portfolio_in.name)
    if existing is not None:
        raise conflict(PORTFOLIO_NAME_ALREADY_EXISTS)

    db_portfolio = Portfolio(
        name=portfolio_in.name,
        description=portfolio_in.description,
        owner_id=owner_id,
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def update_portfolio(
    db: Session,
    db_portfolio: Portfolio,
    portfolio_in: PortfolioUpdate,
) -> Portfolio:
    if portfolio_in.name is not None and portfolio_in.name != db_portfolio.name:
        existing = get_portfolio_by_owner_and_name(db, db_portfolio.owner_id, portfolio_in.name)
        if existing is not None and existing.id != db_portfolio.id:
            raise conflict(PORTFOLIO_NAME_ALREADY_EXISTS)
        db_portfolio.name = portfolio_in.name

    if portfolio_in.description is not None:
        db_portfolio.description = portfolio_in.description

    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def delete_portfolio(db: Session, db_portfolio: Portfolio) -> None:
    db.delete(db_portfolio)
    db.commit()
