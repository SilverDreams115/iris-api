from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging import configure_logging, get_logger
from app.core.settings import settings

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("IRIS API startup completed")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
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
