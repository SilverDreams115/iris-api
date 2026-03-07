from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter(prefix="/private", tags=["Private"])


@router.get("/ping")
def private_ping(current_user: User = Depends(get_current_user)):
    return {
        "message": "Private route access granted",
        "user_email": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin")
def admin_only(current_user: User = Depends(require_role("admin"))):
    return {
        "message": "Admin route access granted",
        "user_email": current_user.email,
        "role": current_user.role,
    }
