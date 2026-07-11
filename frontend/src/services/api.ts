import { MarketCandle, PredictionRecord, TradeRecord, PortfolioState, DBHealthState, SystemHealthState } from "@/types";

const BACKEND_URL = "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BACKEND_URL}${path}`;
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`Fetch failed for ${url}:`, error);
    throw error;
  }
}

export const apiService = {
  // Health APIs
  async getSystemHealth(): Promise<SystemHealthState> {
    return apiFetch<SystemHealthState>("/health");
  },

  async getDBHealth(): Promise<DBHealthState> {
    return apiFetch<DBHealthState>("/api/v1/database/health");
  },

  // Portfolio & Live Paper Trading
  async getPortfolio(): Promise<PortfolioState> {
    return apiFetch<PortfolioState>("/api/v1/paper-trading/portfolio");
  },

  // Backtest Management
  async startBacktest(params: {
    symbol: string;
    timeframe: string;
    days: number;
    starting_balance: number;
  }): Promise<{ backtest_id: string }> {
    return apiFetch<{ backtest_id: string }>("/api/v1/backtest/start", {
      method: "POST",
      body: JSON.stringify(params),
    });
  },

  async getBacktestStatus(id: string): Promise<{
    backtest_id: string;
    symbol: string;
    timeframe: string;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    profit_percentage: number;
    maximum_drawdown: number;
    current_balance: number;
  }> {
    return apiFetch<any>(`/api/v1/backtest/${id}`);
  },

  // Paginated History endpoints
  async getCandlesHistory(params: {
    symbol?: string;
    timeframe?: string;
    page?: number;
    size?: number;
  }): Promise<{ items: MarketCandle[]; total: number; page: number; size: number; pages: number }> {
    const q = new URLSearchParams();
    if (params.symbol) q.set("symbol", params.symbol);
    if (params.timeframe) q.set("timeframe", params.timeframe);
    if (params.page) q.set("page", String(params.page));
    if (params.size) q.set("size", String(params.size));
    return apiFetch<any>(`/api/v1/history/candles?${q.toString()}`);
  },

  async getPredictionsHistory(params: {
    symbol?: string;
    correct?: boolean;
    page?: number;
    size?: number;
  }): Promise<{ items: PredictionRecord[]; total: number; page: number; size: number; pages: number }> {
    const q = new URLSearchParams();
    if (params.symbol) q.set("symbol", params.symbol);
    if (params.correct !== undefined) q.set("correct", String(params.correct));
    if (params.page) q.set("page", String(params.page));
    if (params.size) q.set("size", String(params.size));
    return apiFetch<any>(`/api/v1/history/predictions?${q.toString()}`);
  },

  async getTradesHistory(params: {
    symbol?: string;
    status?: string;
    page?: number;
    size?: number;
  }): Promise<{ items: TradeRecord[]; total: number; page: number; size: number; pages: number }> {
    const q = new URLSearchParams();
    if (params.symbol) q.set("symbol", params.symbol);
    if (params.status) q.set("status", params.status);
    if (params.page) q.set("page", String(params.page));
    if (params.size) q.set("size", String(params.size));
    return apiFetch<any>(`/api/v1/history/trades?${q.toString()}`);
  },
};
