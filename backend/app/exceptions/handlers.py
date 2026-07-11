"""
Global exception handlers for the FastAPI application.
Standardizes error response structures and logs error details.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
from app.config.settings import settings


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handles standard HTTPExceptions and returns a structured JSON response.
    """
    logger.warning(f"HTTP error occurred: {request.method} {request.url.path} | Status: {exc.status_code} | Detail: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
                "details": None
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handles validation errors (e.g. invalid request body/params) and returns a detailed response.
    """
    errors = exc.errors()
    logger.warning(f"Validation error occurred: {request.method} {request.url.path} | Details: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation failed",
                "details": errors
            }
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler for any unhandled exceptions.
    Prevents exposing sensitive stack traces in production.
    """
    logger.exception(f"Unhandled exception occurred: {request.method} {request.url.path} | Error: {str(exc)}")
    
    message = str(exc) if settings.DEBUG else "Internal Server Error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": message,
                "details": None
            }
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Helper function to register all global exception handlers onto the FastAPI application instance.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
