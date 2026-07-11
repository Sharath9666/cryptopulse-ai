"""
Database connection health checking and verification utilities.
Provides comprehensive checks for connectivity, schema presence, and table counts.
"""

from typing import Dict, Any

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncConnection
from loguru import logger

from app.database.engine import engine


# Tables that must exist for the application to function correctly
REQUIRED_TABLES = [
    "prediction_records",
    "trade_records",
    "backtest_results",
    "market_candles",
    "portfolio_snapshots",
]


async def check_database_health() -> bool:
    """
    Executes a lightweight query ('SELECT 1') to verify database connectivity.

    Returns:
        bool: True if connection is alive and queries succeed, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def _get_existing_tables(conn: AsyncConnection) -> list[str]:
    """
    Returns the list of table names present in the public schema.
    """
    result = await conn.execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
    )
    return [row[0] for row in result.fetchall()]


async def check_schema_health() -> Dict[str, Any]:
    """
    Verifies that all required application tables exist in the database.

    Returns:
        dict with keys:
            - healthy (bool): True if all required tables are present.
            - existing_tables (list): Tables currently in the DB.
            - missing_tables (list): Required tables that are absent.
    """
    try:
        async with engine.connect() as conn:
            existing = await _get_existing_tables(conn)
        missing = [t for t in REQUIRED_TABLES if t not in existing]
        return {
            "healthy": len(missing) == 0,
            "existing_tables": existing,
            "missing_tables": missing,
        }
    except Exception as e:
        logger.error(f"Schema health check failed: {e}")
        return {
            "healthy": False,
            "existing_tables": [],
            "missing_tables": REQUIRED_TABLES,
        }


async def get_table_row_counts() -> Dict[str, int]:
    """
    Returns the row count for each required table.
    Useful for verifying that seed data was inserted correctly.

    Returns:
        dict mapping table_name -> row_count (or -1 on error)
    """
    counts: Dict[str, int] = {}
    try:
        async with engine.connect() as conn:
            existing = await _get_existing_tables(conn)
            for table in REQUIRED_TABLES:
                if table in existing:
                    result = await conn.execute(
                        text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                    )
                    counts[table] = result.scalar() or 0
                else:
                    counts[table] = -1  # -1 indicates table does not exist
    except Exception as e:
        logger.error(f"Failed to fetch table row counts: {e}")
    return counts


async def get_full_health_report() -> Dict[str, Any]:
    """
    Returns a comprehensive database health report including connectivity,
    schema validation, and table row counts.

    Returns:
        dict with:
            - connected (bool)
            - schema_healthy (bool)
            - missing_tables (list)
            - table_counts (dict)
    """
    connected = await check_database_health()
    if not connected:
        return {
            "connected": False,
            "schema_healthy": False,
            "missing_tables": REQUIRED_TABLES,
            "table_counts": {},
        }

    schema_info = await check_schema_health()
    table_counts = await get_table_row_counts()

    return {
        "connected": True,
        "schema_healthy": schema_info["healthy"],
        "existing_tables": schema_info["existing_tables"],
        "missing_tables": schema_info["missing_tables"],
        "table_counts": table_counts,
    }


async def verify_db_connection() -> None:
    """
    Verifies connection status on application startup.
    Logs warning/error instead of raising exceptions so the application
    can start in a degraded state if the database is unavailable.
    """
    logger.info("Initializing database connection verification...")
    report = await get_full_health_report()

    if not report["connected"]:
        logger.warning(
            "Database is unavailable. The application will start, "
            "but database-dependent features will fail. "
            "Please check connection settings and database status."
        )
        return

    logger.info("Database connection verified successfully.")

    if not report["schema_healthy"]:
        logger.warning(
            f"Schema validation failed — missing tables: {report['missing_tables']}. "
            "Run 'alembic upgrade head' to apply migrations."
        )
    else:
        logger.info("Schema validation passed — all required tables are present.")

    counts = report.get("table_counts", {})
    if counts:
        count_summary = ", ".join(f"{t}={c}" for t, c in counts.items())
        logger.info(f"Table row counts: {count_summary}")
