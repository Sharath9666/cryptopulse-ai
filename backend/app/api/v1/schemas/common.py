"""
Base schemas, pagination schemas, and standard error models.
"""

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIErrorDetails(BaseModel):
    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="User-facing error message")
    details: Optional[dict | list] = Field(None, description="Detailed validation or exception info")


class APIErrorResponse(BaseModel):
    success: bool = Field(False, description="Flag indicating failed request")
    error: APIErrorDetails = Field(..., description="Error details payload")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    size: int = Field(50, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items available")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size limit")
    pages: int = Field(..., description="Total number of pages")
