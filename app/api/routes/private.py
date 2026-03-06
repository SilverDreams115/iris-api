from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/private", tags=["Private"])


@router.get("/ping")
def private_ping(current_user: User = Depends(get_current_user)):
    return {
        "message": "Private route access granted",
        "user_email": current_user.email,
    }
