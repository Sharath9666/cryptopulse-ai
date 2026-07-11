export interface MarketCandle {
  id?: string;
  symbol: string;
  timeframe: string;
  start_time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  created_at?: string;
}

export interface PredictionRecord {
  id?: string;
  prediction_id: string;
  symbol: string;
  timeframe: string;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  predicted_move: number;
  entry_price: number;
  actual_price?: number | null;
  actual_move?: number | null;
  correct?: boolean | null;
  prediction_time: string;
  evaluation_time?: string | null;
}

export interface TradeRecord {
  id?: string;
  trade_id: string;
  symbol: string;
  direction: "LONG";
  entry_price: number;
  exit_price?: number | null;
  quantity: number;
  profit_loss: number;
  status: "OPEN" | "CLOSED";
  opened_at: string;
  closed_at?: string | null;
}

export interface PortfolioState {
  balance: number;
  open_positions: TradeRecord[];
  closed_trades: TradeRecord[];
  profit: number;
}

export interface EngineHealthDetail {
  status?: string;
  health_status?: string;
  [key: string]: any;
}

export interface DBHealthState {
  connected: boolean;
  schema_healthy: boolean;
  existing_tables: string[];
  missing_tables: string[];
  table_counts: Record<string, number>;
  migration_hint?: string;
}

export interface SystemHealthState {
  status: string;
  database: string;
  cache: string;
  market_engine: EngineHealthDetail;
  candle_engine: EngineHealthDetail;
  event_bus: EngineHealthDetail;
  feature_engine: EngineHealthDetail;
  prediction_engine: EngineHealthDetail;
  paper_trading: EngineHealthDetail;
  backtesting: EngineHealthDetail;
  performance_tracking: EngineHealthDetail;
  strategy_engine: EngineHealthDetail;
  environment: string;
}
