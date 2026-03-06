from fastapi import FastAPI

from app.core.settings import settings


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "ok"}