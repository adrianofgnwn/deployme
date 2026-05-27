"""FastAPI application entrypoint.

Wires together the security foundation built in Phase 0:
  * CORS restricted to configured origins (never ``*``)
  * Security response headers and a request body-size cap
  * Rate limiting via slowapi
  * Exception handlers that return safe, consistent error envelopes and never
    leak stack traces, file paths, or library versions to clients.

Run locally with: ``uvicorn main:app --reload``
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.middleware import MaxBodySizeMiddleware, SecurityHeadersMiddleware
from api.routes import health
from core.auth import AuthError
from core.config import get_settings
from core.rate_limiter import limiter, rate_limit_exceeded_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("deployme")

settings = get_settings()

app = FastAPI(
    title="DeployMe API",
    description="Job market analysis, CV optimization, and application tracking.",
    version="0.1.0",
)

# ─── Rate limiting ───────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ─── Middleware ──────────────────────────────────────────────────────────────
# Order matters: body-size check first (reject early), then security headers,
# then CORS (added last so it runs first on the inbound path).
app.add_middleware(MaxBodySizeMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Key"],
)


# ─── Exception handlers (no internal details ever reach the client) ──────────
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": "unauthorized", "detail": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Surface which fields failed (useful and safe) without echoing internals.
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": "Request validation failed.",
            "fields": [
                {"loc": err.get("loc"), "msg": err.get("msg")}
                for err in exc.errors()
            ],
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full traceback server-side; return an opaque message to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


# ─── Routes ──────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
