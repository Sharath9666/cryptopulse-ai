"""
Database health and administration endpoints.
Provides detailed schema validation, table counts, and migration status.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List

router = APIRouter()


class DatabaseHealthResponse(BaseModel):
    """Response model for detailed database health report."""
    connected: bool = Field(..., description="Whether the database connection is alive.")
    schema_healthy: bool = Field(..., description="Whether all required tables are present.")
    existing_tables: List[str] = Field(default_factory=list, description="Tables found in the public schema.")
    missing_tables: List[str] = Field(default_factory=list, description="Required tables that are absent.")
    table_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Row count per table. -1 means the table does not exist."
    )
    migration_hint: str = Field("", description="Actionable hint if schema is unhealthy.")


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=DatabaseHealthResponse,
    summary="Database health report",
    description=(
        "Returns detailed database health: connectivity, schema validation "
        "against required tables, and per-table row counts."
    ),
)
async def database_health() -> DatabaseHealthResponse:
    from app.database.health import get_full_health_report

    report = await get_full_health_report()
    migration_hint = ""
    if not report.get("schema_healthy", True):
        migration_hint = (
            "One or more required tables are missing. "
            "Run: cd backend && alembic upgrade head"
        )

    return DatabaseHealthResponse(
        connected=report["connected"],
        schema_healthy=report.get("schema_healthy", False),
        existing_tables=report.get("existing_tables", []),
        missing_tables=report.get("missing_tables", []),
        table_counts=report.get("table_counts", {}),
        migration_hint=migration_hint,
    )
