from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import settings


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


@app.get("/", tags=["Root"])
def root():
    return {"message": "IRIS API is running"}


@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "ok"}


app.include_router(api_router)