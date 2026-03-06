from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.crud.user import get_by_email, create
from app.database import get_db
from app.schemas.auth import RegisterIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = create(db, email=payload.email, hashed_password=hash_password(payload.password))
    return {"id": user.id, "email": user.email}

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token(
        subject=user.email,
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {"access_token": token, "token_type": "bearer"}
