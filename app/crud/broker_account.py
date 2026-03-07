from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.schemas.broker_account import BrokerAccountCreate, BrokerAccountUpdate


def create_broker_account(
    db: Session, owner_id: int, broker_account_in: BrokerAccountCreate
):
    db_broker_account = BrokerAccount(
        broker_name=broker_account_in.broker_name,
        account_label=broker_account_in.account_label,
        account_type=broker_account_in.account_type.value,
        status="active",
        owner_id=owner_id,
    )
    db.add(db_broker_account)
    db.commit()
    db.refresh(db_broker_account)
    return db_broker_account


def get_broker_account_by_id(db: Session, broker_account_id: int):
    return db.query(BrokerAccount).filter(BrokerAccount.id == broker_account_id).first()


def get_broker_accounts_by_owner(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(BrokerAccount)
        .filter(BrokerAccount.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_broker_accounts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(BrokerAccount).offset(skip).limit(limit).all()


def update_broker_account(
    db: Session,
    db_broker_account: BrokerAccount,
    broker_account_in: BrokerAccountUpdate,
):
    if broker_account_in.broker_name is not None:
        db_broker_account.broker_name = broker_account_in.broker_name
    if broker_account_in.account_label is not None:
        db_broker_account.account_label = broker_account_in.account_label
    if broker_account_in.account_type is not None:
        db_broker_account.account_type = broker_account_in.account_type.value
    if broker_account_in.status is not None:
        db_broker_account.status = broker_account_in.status.value

    db.commit()
    db.refresh(db_broker_account)
    return db_broker_account


def delete_broker_account(db: Session, db_broker_account: BrokerAccount):
    db.delete(db_broker_account)
    db.commit()
