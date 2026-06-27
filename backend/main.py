from fastapi import FastAPI

from config.settings import settings
from config.logger import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)


@app.get("/")
def root():
    logger.info("Application Started")

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "Running"
    }