from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.logging import configure_logging, get_logger
from app.core.redis_client import redis_client
from app.core.settings import settings
from app.database import SessionLocal

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("IRIS API startup completed")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
    }


@app.get("/ready")
def readiness_check():
    checks = {
        "database": "ok",
        "redis": "ok",
    }

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database readiness check failed")
        checks["database"] = f"error: {exc.__class__.__name__}"

    try:
        redis_client.ping()
    except Exception as exc:
        logger.exception("Redis readiness check failed")
        checks["redis"] = f"error: {exc.__class__.__name__}"

    if all(value == "ok" for value in checks.values()):
        return {
            "status": "ok",
            "app_name": settings.APP_NAME,
            "checks": checks,
        }

    raise HTTPException(
        status_code=503,
        detail={
            "status": "error",
            "app_name": settings.APP_NAME,
            "checks": checks,
        },
    )
