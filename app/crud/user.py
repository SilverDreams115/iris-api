from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate, role: str = "user"):
    db_user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hash_password(user_in.password),
        role=role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_in: UserUpdate):
    if user_in.name is not None:
        db_user.name = user_in.name

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: User):
    db.delete(db_user)
    db.commit()


def update_user_role(db: Session, db_user: User, role: str):
    db_user.role = role
    db.commit()
    db.refresh(db_user)
    return db_user


def set_user_active_status(db: Session, db_user: User, is_active: bool):
    db_user.is_active = is_active
    db.commit()
    db.refresh(db_user)
    return db_user


def change_user_password(db: Session, db_user: User, new_password: str):
    db_user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user
