from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.private import router as private_router
from app.api.routes.user import router as user_router


api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(auth_router)
api_router.include_router(private_router)
api_router.include_router(portfolio_router)
