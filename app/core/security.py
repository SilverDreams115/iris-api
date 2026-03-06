from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt
from passlib.hash import bcrypt

ALGORITHM = "HS256"
SECRET_KEY = "supersecretkey"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _pw72(value: Any) -> bytes:
    b = str(value).encode("utf-8")
    return b[:72]


def hash_password(password: Any) -> str:
    return bcrypt.hash(_pw72(password))


def verify_password(plain_password: Any, hashed_password: str) -> bool:
    return bcrypt.verify(_pw72(plain_password), hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
