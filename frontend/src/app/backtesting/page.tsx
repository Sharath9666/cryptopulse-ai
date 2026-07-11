"use client";

import { useState } from "react";
import { apiService } from "@/services/api";
import { Loader2, Play, CheckCircle, HelpCircle } from "lucide-react";

export default function BacktestingPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1m");
  const [days, setDays] = useState(3);
  const [balance, setBalance] = useState(100000);
  
  const [running, setRunning] = useState(false);
  const [backtestResult, setBacktestResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStartBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setBacktestResult(null);
    setError(null);

    try {
      // Trigger simulation run
      const { backtest_id } = await apiService.startBacktest({
        symbol,
        timeframe,
        days,
        starting_balance: balance,
      });

      // Poll for completion (speed mode resolves immediately, live needs intervals)
      let attempts = 0;
      const interval = setInterval(async () => {
        try {
          attempts++;
          const status = await apiService.getBacktestStatus(backtest_id);
          if (status) {
            setBacktestResult(status);
            setRunning(false);
            clearInterval(interval);
          }
        } catch (err) {
          if (attempts > 10) {
            setError("Simulation check timeout. Verification failed.");
            setRunning(false);
            clearInterval(interval);
          }
        }
      }, 2000);
    } catch (err: any) {
      setError(err?.message || "Failed to initiate backtest simulation.");
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-center border-b border-slate-900 pb-6">
        <div>
          <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">ALGORITHMIC REPLAY INTERFACE</span>
          <h2 className="text-3xl font-black text-white tracking-tight mt-1">Backtest Replay Engine</h2>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Settings Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl h-fit">
          <h3 className="font-bold text-white tracking-tight mb-6">Replay Specifications</h3>
          
          <form onSubmit={handleStartBacktest} className="space-y-5">
            <div>
              <label className="text-[10px] text-slate-500 font-semibold block uppercase mb-2">Trading Pair</label>
              <select 
                value={symbol} 
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-350 focus:outline-none focus:border-violet-500"
              >
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
                <option value="DOGEUSDT">DOGEUSDT</option>
                <option value="SOLUSDT">SOLUSDT</option>
                <option value="XRPUSDT">XRPUSDT</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-semibold block uppercase mb-2">Replay Timeframe</label>
              <select 
                value={timeframe} 
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-350 focus:outline-none focus:border-violet-500"
              >
                <option value="1m">1m</option>
                <option value="5m">5m</option>
                <option value="1h">1h</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-semibold block uppercase mb-2">Lookback Period (Days)</label>
              <input 
                type="number" 
                min={1} 
                max={30} 
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-350 focus:outline-none focus:border-violet-500 font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-semibold block uppercase mb-2">Virtual Starting Balance (USDT)</label>
              <input 
                type="number" 
                step={1000} 
                value={balance}
                onChange={(e) => setBalance(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-slate-350 focus:outline-none focus:border-violet-500 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={running}
              className="w-full bg-violet-600 hover:bg-violet-750 text-white font-bold text-sm py-3 px-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2 shadow-lg shadow-violet-600/20"
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Replaying Stream...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Run Backtest</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Block */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-2xl text-xs font-semibold">
              {error}
            </div>
          )}

          {backtestResult ? (
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6 animate-fade-in">
              <div className="flex items-center gap-2 border-b border-slate-800/60 pb-4">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-white tracking-tight">Replay Output Results</h3>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase font-sans">Profit / Loss</span>
                  <span className={`text-xl font-bold ${backtestResult.profit_percentage >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {backtestResult.profit_percentage >= 0 ? "+" : ""}{backtestResult.profit_percentage.toFixed(2)}%
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase font-sans">Simulated Operations</span>
                  <span className="text-xl font-bold text-white">{backtestResult.total_trades} Trades</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase font-sans">Win Rate Ratio</span>
                  <span className="text-xl font-bold text-violet-400">{(backtestResult.win_rate * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase font-sans">Max Drawdown</span>
                  <span className="text-xl font-bold text-rose-400">-{backtestResult.maximum_drawdown.toFixed(2)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase font-sans">Final Account value</span>
                  <span className="text-xl font-bold text-white">${backtestResult.current_balance.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-3xl p-12 text-center text-xs text-slate-500 font-medium">
              <HelpCircle className="w-10 h-10 text-slate-650 mx-auto mb-4" />
              <p>Adjust the configuration and run simulation to inspect metric graphs.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
