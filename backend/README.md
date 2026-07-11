# CryptoPulse AI - Backend Foundation

A production-grade, scalable FastAPI backend boilerplate built with Python 3.12, featuring environment-driven configurations, intercepting structured logging via Loguru, global exception handlers, and custom request logging middleware.

## Features

- **FastAPI**: Modern, fast web framework for building APIs.
- **Python 3.12**: Clean, optimized code conforming to modern syntax and type hints.
- **Pydantic Settings**: Centralized environment variable validation using `pydantic-settings`.
- **Loguru Integration**: Custom log formatting and interception of native Python logs (`uvicorn`, `fastapi`, etc.).
- **Lifespan Manager**: Handles clean startup and shutdown events.
- **Custom Middleware**: Automatic request logging including client IP, HTTP method, path, response status, and processing duration.
- **Global Error Interceptors**: Standardized JSON responses for HTTP exceptions, request validation errors, and untrusted internal errors.

---

## Folder Structure

```text
backend/
│
├── .env.example            # Sample configuration file
├── .gitignore              # Git ignored files pattern
├── requirements.txt        # Third-party dependency definition
├── README.md               # Developer guidelines & usage documentation
├── alembic.ini             # Alembic migration tool settings
├── alembic/                # Database migrations folder
│   ├── env.py              # Alembic environment runner
│   ├── script.py.mako      # Template for migrations
│   └── versions/           # Schema migration history files
│
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI App instance and middleware configuration
    │
    ├── api/                # Sub-routes and API routers
    │   ├── __init__.py
    │   ├── router.py       # Main API aggregator router
    │   └── v1/             # Version 1 routing layer
    │       ├── __init__.py
    │       └── endpoints/  # Resource endpoint modules
    │           ├── __init__.py
    │           ├── health.py
    │           └── root.py
    │
    ├── config/             # Pydantic environment configuration
    │   ├── __init__.py
    │   └── settings.py
    │
    ├── core/               # App lifecycle hook and logging configs
    │   ├── __init__.py
    │   ├── lifespan.py
    │   └── logging.py
    │
    ├── cache/              # Redis caching layer infrastructure
    │   ├── __init__.py     # Exposes cache utilities
    │   ├── client.py       # RedisClientManager for pooling & lifespan management
    │   ├── dependencies.py # Redis client FastAPI dependencies
    │   ├── health.py       # Redis health checks and startup validation
    │   └── redis.py        # Centralized Redis client wrapper
    │
    ├── candles/            # Candle Aggregation Engine
    │   ├── __init__.py     # Exposes candle engine package structures
    │   ├── models/         # Pydantic schemas representing completed candles
    │   ├── services/       # Candle aggregator for building OHLCV from ticks
    │   ├── health.py       # Active/completed candle counts and statistics
    │   ├── manager.py      # Aggregator lifecycle coordinator
    │   └── publisher.py    # Completed candle Redis publisher
    │
    ├── database/           # Database layer infrastructure
    │   ├── __init__.py     # Exposes database utilities
    │   ├── base.py         # SQLAlchemy Base and BaseModel with UUID, timestamps
    │   ├── dependencies.py # Database async session FastAPI dependencies
    │   ├── engine.py       # SQLAlchemy async engine configuration
    │   ├── health.py       # Database health checks and startup validation
    │   └── session.py      # Async session factory
    │
    ├── events/             # Asynchronous in-process Event Bus
    │   ├── __init__.py     # Exposes event package components
    │   ├── base_event.py   # Base event schema
    │   ├── event_bus.py    # EventBus dispatch loop and queue
    │   ├── health.py       # Event bus monitoring statistics
    │   ├── publisher.py    # Generic publisher interface
    │   ├── registry.py     # Registry to automate subscriber hooks
    │   └── subscriber.py   # Abstract subscriber interface
    │
    ├── features/           # Feature Engineering Engine
    │   ├── __init__.py     # Exposes feature package components
    │   ├── models/         # FeatureVector schema definition
    │   ├── services/       # Feature engine service managing history buffers
    │   ├── calculators/    # Independent indicators calculators (trend, momentum, volatility, volume)
    │   ├── health.py       # Generation counts, buffers sizes, latency metrics
    │   ├── publisher.py    # Cache publisher for feature vectors
    │   └── subscribers.py  # CompletedCandleSubscriber event listener
    │
    ├── prediction/         # Prediction Engine (Rule-based)
    │   ├── __init__.py     # Exposes prediction package structures
    │   ├── models/         # Prediction schema definitions
    │   ├── services/       # Prediction coordinator and rule scoring engines
    │   ├── health.py       # Prediction counters and latencies trackers
    │   ├── publisher.py    # Cache publisher for prediction vectors
    │   └── subscribers.py  # FeatureVectorSubscriber event listener
    │
    ├── paper_trading/      # Paper Trading Engine (Simulation)
    │   ├── __init__.py     # Exposes paper trading package structures
    │   ├── models/         # Trade and Portfolio schema definitions
    │   ├── services/       # Simulated execution and portfolio tracking managers
    │   ├── health.py       # Win/loss stats, balances, and returns trackers
    │   ├── publisher.py    # Cache publisher for trade files
    │   └── subscribers.py  # PredictionSubscriber and TickSubscriber event listeners
    │
    ├── backtesting/        # Backtesting Engine
    │   ├── __init__.py     # Exposes backtesting package structures
    │   ├── models/         # HistoricalCandle and BacktestResult schemas
    │   ├── services/       # Historical data downloaders and market replays
    │   ├── health.py       # Diagnostics for completed/active backtests
    │   └── publisher.py    # Cache publisher for backtest results
    │
    ├── market/             # Market data engine infrastructure
    │   ├── __init__.py     # Exposes market module utilities
    │   ├── clients/        # WebSocket client for data feeds (e.g. Binance)
    │   ├── services/       # Stream processing and caching services
    │   ├── schemas/        # Tick schemas (Pydantic validation)
    │   ├── health.py       # WebSocket connection statistics and health
    │   └── manager.py      # Engine lifecycle coordinator
    │
    ├── middleware/         # App middleware stack
    │   ├── __init__.py
    │   └── logging.py      # HTTP Request logger middleware
    │
    ├── exceptions/         # Centralized error interceptors
    │   ├── __init__.py
    │   └── handlers.py
    │
    └── utils/              # Common project utilities
        └── __init__.py
```

---

## Prerequisites

- **Python 3.12** or higher.
- `pip` package manager.

## Getting Started

### 1. Copy the Configuration

Duplicate `.env.example` to create your local configuration:

```bash
cp .env.example .env
```

### 2. Install Dependencies

It is highly recommended to use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Development Server

Execute the following command from the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

- **API Root**: [http://localhost:8000/](http://localhost:8000/)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Database Infrastructure

The database layer is configured with:
- **SQLAlchemy 2.x**: Declarative mappings, modern 2.x syntax, and asynchronous engine support.
- **asyncpg**: High-performance PostgreSQL client library for Python asyncio.
- **Alembic**: Async-configured migration suite to track schema versions.

### Database Operations and Migrations

#### Create a New Migration
To autogenerate a migration after updating database models in the codebase:
```bash
alembic revision --autogenerate -m "describe your changes"
```

#### Run Migrations
To apply all pending migrations to the database:
```bash
alembic upgrade head
```

#### Revert Migrations
To rollback the last migration:
```bash
alembic downgrade -1
```

---

## Cache Infrastructure

The caching layer is configured with:
- **redis-py**: Async client library for connection, pooling, and cache management.
- **Connection Manager**: Exposes pools and clients, handling cleanup automatically on shutdown.
- **FastAPI Dependency**: Injects Redis connection pool instances into API endpoints.
- **Health Verification**: Periodically polls cache status via the centralized health check endpoint.

---

## Market Data Engine

The live market feed engine connects to external sources to stream and cache exchange data:
- **WebSocket Streaming**: Uses `websockets` to stream live ticker updates directly from the Binance API.
- **Auto-Reconnection**: Reconnects with exponential backoff if the feed disconnects, ensuring uninterrupted operations.
- **Cache Persistence**: Parses, validates, and stores ticks as JSON strings in Redis with a 5-minute Time-To-Live (TTL).
- **Diagnostics**: Monitors socket parameters (connection state, reconnect count, list of connected streams, and time since last tick received) and exposes them on the centralized `/health` check.

---

## Candle Aggregation Engine

The candle aggregation module groups live ticks into standard interval periods:
- **OHLCV Construction**: Updates open, high, low, close, and base volume metrics in real-time as ticks arrive.
- **Delta Volume Tracking**: Computes true candle volume by tracking shifts in cumulative 24h ticker volumes.
- **Event-Driven Completion**: Detects the completion of candle periods (e.g. 1-minute blocks) using incoming tick event times, prompting immediate publication.
- **Cache Publication**: Serializes completed candles as JSON strings in Redis under `candle:{timeframe}:{symbol}` with a 24-hour TTL.
- **Engine Analytics**: Monitors currently active in-memory candles, completed candle counts, and last completed stats, exporting them via the `/health` diagnostic endpoint.

---

## Internal Event Bus

The application leverages an asynchronous in-process publish-subscribe system to decouple communication across engines:
- **Queue-Based Routing**: Decouples event publication from handler execution using an internal `asyncio.Queue` event loop.
- **Exception Isolation**: Isolates event handler errors, ensuring a failure in one subscriber does not impact the dispatching of other events.
- **Unified Registry**: Automatically wires up event subscriptions during application lifespan startup using a central registry.
- **Uptime Monitoring**: Exposes metrics including subscriber counts, total published events, failure rates, and queue size to the `/health` endpoint.

---

## Feature Engineering Engine

The Feature Engineering engine generates real-time technical indicators from completed candle updates:
- **Historical Buffers**: Retains a stateful rolling history of completed candles per symbol (up to 300 periods) to calculate long indicators such as EMA 200.
- **Decoupled Calculators**: Divides computations into modular Trend, Momentum, Volatility, and Volume indicators:
  - **Trend**: EMA 9, EMA 20, EMA 50, EMA 200.
  - **Momentum**: RSI 14, MACD, Signal Line, MACD Histogram, Stochastic RSI.
  - **Volatility**: ATR 14, Bollinger Bands (Upper, Middle, Lower, Width).
  - **Volume**: VWAP, On Balance Volume (OBV).
- **Cache Persistence**: Caches the latest computed FeatureVector in Redis under `feature:{timeframe}:{symbol}` keys with a 24-hour TTL.
- **Engine Diagnostics**: Exposes metrics detailing tracked symbols, historical buffer lengths, total features generated, and calculation latency to the `/health` endpoint.

---

## Prediction Engine

The Prediction engine processes FeatureVectors to generate direction predictions:
- **Decoupled Scoring Engine**: Employs a rule-based scoring module evaluating trend golden/death crossovers (EMA20, EMA50, EMA200), RSI thresholds, MACD boundaries, and VWAP alignments.
- **Probabilistic Calibration**: Scales directional scores to output predictions as BULLISH, BEARISH, or NEUTRAL with calculated probabilities and confidence grades (HIGH, MEDIUM, LOW).
- **Cache Persistence**: Stores the latest Prediction payload in Redis under `prediction:{timeframe}:{symbol}` keys with a 24-hour TTL.
- **Engine Diagnostics**: Exposes execution metrics detailing generated predictions count, average processing latency, last execution timestamp, and tracked symbols to the `/health` endpoint.

---

## Paper Trading Engine

The Paper Trading engine simulates live trades using generated predictions in a risk-free environment:
- **Simulation Parameters**: Operates with a starting balance of 100,000 USDT, allocating 10% of available funds for LONG positions.
- **Dynamic Exit Targets**: Automates target evaluations, closing open trades when hitting +3% Take Profit or -2% Stop Loss thresholds.
- **Position Price Monitoring**: Subscribes to live `MarketTickReceivedEvent` inputs to verify open position values against real-time exchange rates.
- **Cache Persistence**: Persists current portfolio states (`paper_portfolio`) and individual trade actions (`paper_trade:{trade_id}`) in Redis with a 7-day TTL.
- **Engine Diagnostics**: Exposes performance parameters including total trades executed, current balance, wins/losses counts, and overall returns percentages to the `/health` endpoint.

---

## Backtesting Engine

The Backtesting engine replays historical exchange OHLCV data through the prediction and paper trading simulation pipeline:
- **Historical Data Downloads**: Downloads historical candle intervals from the Binance public REST API within specified ranges.
- **Chronological Market Replay**: Converts historical bars into sequential proxy `MarketTickReceivedEvent` signals, streaming them onto the Event Bus to drive processing.
- **Quantitative Performance Stats**: Compiles backtest results including win rates, total profit, profit percentage, maximum equity drawdown, and average trade return.
- **Cache Persistence**: Caches simulation results under `backtest:{id}` keys in Redis.
- **Engine Diagnostics**: Exposes metrics detailing completed backtests count, active backtests, and details of the last result to the `/health` endpoint.

---

## Performance Tracking Engine

The Performance Tracking engine evaluates directional predictions over a configurable time lookback:
- **Prediction Registration**: Subscribes to `PredictionCreatedEvent` inputs, caching prediction parameters and entry prices dynamically.
- **Asynchronous Evaluations**: Spawns deferred accuracy review timers in the background, matching prediction parameters against later market prices.
- **Accuracy Metrics**: Compiles overall direction alignment percentages, total predictions received vs evaluated, average confidence grades, and tracked symbols lists.
- **Cache Persistence**: Stores evaluation snapshots in Redis under `perf_pred:{prediction_id}` keys.
- **Engine Diagnostics**: Exposes metrics detailing accuracy percentages, average confidence, total evaluation counts, and tracked symbols to the `/health` endpoint.
