from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("IRIS API startup completed")
    yield


app = FastAPI(title="IRIS API", lifespan=lifespan)

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "IRIS API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
