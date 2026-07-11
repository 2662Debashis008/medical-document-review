import time

from starlette.middleware.base import BaseHTTPMiddleware

from config.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(f"Unhandled error for {request.method} {request.url.path}")
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} duration_ms={elapsed_ms:.2f}"
        )
        return response
