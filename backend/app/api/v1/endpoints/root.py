"""
Root endpoint.
Serves a basic welcome message and general API metadata.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class RootResponse(BaseModel):
    """
    Response model for root endpoint.
    """
    message: str = Field(..., description="Welcome message")
    app_name: str = Field(..., description="Name of the application")
    docs_url: str = Field(..., description="Link to the API documentation")


@router.get(
    "/",
    response_model=RootResponse,
    summary="Root endpoint",
    description="Returns welcome message and links to interactive API documentation."
)
async def root() -> RootResponse:
    from app.config.settings import settings
    return RootResponse(
        message="Welcome to the CryptoPulse AI API!",
        app_name=settings.APP_NAME,
        docs_url="/docs"
    )
