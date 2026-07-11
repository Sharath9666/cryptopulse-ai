"""
Integration tests for the CryptoPulse AI API endpoints.
Tests routers, OpenAPI specs, error handling, pagination, and database/health endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "docs_url" in data
    assert "app_name" in data


@pytest.mark.anyio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "cache" in data
    assert "prediction_engine" in data


@pytest.mark.anyio
async def test_database_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/database/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "connected" in data
    assert "schema_healthy" in data
    assert "existing_tables" in data


@pytest.mark.anyio
async def test_history_candles_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/history/candles?page=1&size=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert data["page"] == 1
    assert data["size"] == 5


@pytest.mark.anyio
async def test_history_predictions_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/history/predictions?page=1&size=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["size"] == 2


@pytest.mark.anyio
async def test_history_trades_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/history/trades?page=1&size=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["size"] == 10


@pytest.mark.anyio
async def test_paper_trading_portfolio():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/paper-trading/portfolio")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "balance" in data
    assert "open_positions" in data
    assert "closed_trades" in data
    assert "profit" in data


@pytest.mark.anyio
async def test_openapi_documentation_accessible():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    openapi = response.json()
    assert openapi["info"]["title"] == "CryptoPulse AI"
    assert "/api/v1/history/candles" in openapi["paths"]
    assert "/api/v1/history/predictions" in openapi["paths"]
    assert "/api/v1/history/trades" in openapi["paths"]


@pytest.mark.anyio
async def test_validation_error_handler():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid day count (must be int)
        response = await ac.post("/api/v1/backtest/start", json={"symbol": "BTCUSDT", "timeframe": "1m", "days": "invalid", "starting_balance": 10000})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["message"] == "Validation failed"
