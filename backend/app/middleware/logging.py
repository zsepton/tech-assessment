import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and duration for every request.

    Fields are passed via `extra=` so they land as discrete attributes on the
    LogRecord (and, via JSONFormatter, as discrete JSON keys) rather than
    being folded into the free-text message.

    Unhandled exceptions are logged with the same request context (and full
    traceback via logger.exception), then converted into a 500 response with
    the same JSON error shape ({"detail": ...}) as HTTPException responses.
    This middleware sits outside FastAPI's own exception-handling layer, so
    it — not a `@app.exception_handler` — is the right place to do this: a
    handler registered on `app` would intercept the exception before it ever
    reached here, silently defeating this logging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "unhandled error handling request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
