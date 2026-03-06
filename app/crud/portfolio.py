from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate


def create_portfolio(db: Session, owner_id: int, portfolio_in: PortfolioCreate):
    db_portfolio = Portfolio(
        name=portfolio_in.name,
        description=portfolio_in.description,
        owner_id=owner_id,
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def get_portfolio_by_id(db: Session, portfolio_id: int):
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_portfolios_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Portfolio)
        .filter(Portfolio.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_portfolios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Portfolio).offset(skip).limit(limit).all()


def update_portfolio(db: Session, db_portfolio: Portfolio, portfolio_in: PortfolioUpdate):
    if portfolio_in.name is not None:
        db_portfolio.name = portfolio_in.name

    if portfolio_in.description is not None:
        db_portfolio.description = portfolio_in.description

    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def delete_portfolio(db: Session, db_portfolio: Portfolio):
    db.delete(db_portfolio)
    db.commit()
