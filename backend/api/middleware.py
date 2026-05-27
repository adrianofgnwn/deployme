"""Security middleware: response headers and request body size limits."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("deployme.middleware")

# 6 MB: the 5 MB PDF cap plus headroom for multipart encoding overhead.
MAX_BODY_BYTES = 6 * 1024 * 1024

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    # The API serves JSON only and is consumed cross-origin by the SPA, so a
    # tight default-src is safe here. The frontend ships its own CSP.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardening headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies early with a 413, before parsing.

    Relies on the ``Content-Length`` header. Streaming uploads without a length
    are still bounded downstream by the explicit PDF size check, but rejecting
    here avoids buffering obviously-too-large payloads.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "detail": "Request body is too large.",
                        },
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"error": "bad_request", "detail": "Invalid Content-Length."},
                )
        return await call_next(request)
