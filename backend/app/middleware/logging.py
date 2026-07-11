"""
Request logging middleware.
Logs incoming HTTP requests, status codes, and execution durations.
"""

import time
from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log details about every incoming HTTP request and its corresponding response.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"

        logger.info(f"Incoming request: {method} {path} - Client: {client_host}")

        try:
            response = await call_next(request)
            duration = (time.perf_counter() - start_time) * 1000
            
            # Log successful or client-side/server-side responses with appropriate levels
            log_msg = f"Completed request: {method} {path} | Status: {response.status_code} | Duration: {duration:.2f}ms"
            if response.status_code >= 500:
                logger.error(log_msg)
            elif response.status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            response.headers["X-Process-Time-Ms"] = f"{duration:.2f}"
            return response
            
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Exception during request: {method} {path} | Duration: {duration:.2f}ms | Error: {str(exc)}"
            )
            raise exc
