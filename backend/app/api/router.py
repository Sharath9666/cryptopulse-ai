from fastapi import APIRouter
from app.api.v1.endpoints import health, root, backtest, paper_trading, database, history

api_router = APIRouter()

# Root level/public routes (no version prefix needed for basic access/health)
api_router.include_router(root.router, tags=["General"])
api_router.include_router(health.router, tags=["Monitoring"])

# Versioned routes
api_router.include_router(backtest.router, prefix="/api/v1/backtest", tags=["Backtesting"])
api_router.include_router(paper_trading.router, prefix="/api/v1/paper-trading", tags=["Paper Trading"])
api_router.include_router(database.router, prefix="/api/v1/database", tags=["Database"])
api_router.include_router(history.router, prefix="/api/v1/history", tags=["History"])
