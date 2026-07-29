from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from config.logger import logger

from database.init_db import ensure_schema
from exceptions.file_exceptions import FileValidationException
from middleware.request_logging import RequestLoggingMiddleware
from services.prompt_service import PromptService
from utils.storage_helper import create_storage_directories

from api.routes.document_routes import router as document_router
from api.routes.upload_alias_routes import router as upload_alias_router
from api.routes.workflow_routes import router as workflow_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Medical Document Review API...")

    create_storage_directories()
    PromptService.ensure_default_prompts()
    ensure_schema()

    logger.info("Storage folders and database schema ready.")

    yield

    logger.info("Application stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",

        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(document_router)
app.include_router(upload_alias_router)
app.include_router(workflow_router)


@app.exception_handler(FileValidationException)
async def file_validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def root():

    return {

        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "Running"

    }
