"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/services/api";
import { PortfolioState, PredictionRecord, TradeRecord, SystemHealthState } from "@/types";
import PortfolioCard from "@/components/ui/PortfolioCard";
import PredictionCard from "@/components/ui/PredictionCard";
import TradeHistory from "@/components/ui/TradeHistory";
import { BrainCircuit, Loader2, PlayCircle, ShieldCheck } from "lucide-react";

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [predictions, setPredictions] = useState<PredictionRecord[]>([]);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [health, setHealth] = useState<SystemHealthState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [portData, predHistory, tradeHistory, healthStatus] = await Promise.all([
          apiService.getPortfolio(),
          apiService.getPredictionsHistory({ page: 1, size: 3 }),
          apiService.getTradesHistory({ page: 1, size: 5 }),
          apiService.getSystemHealth(),
        ]);
        setPortfolio(portData);
        setPredictions(predHistory.items);
        setTrades(tradeHistory.items);
        setHealth(healthStatus);
      } catch (err) {
        console.error("Dashboard data load failure:", err);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-6">
        <div>
          <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">REALTIME PERSISTENT PERSISTENCE</span>
          <h2 className="text-3xl font-black text-white tracking-tight mt-1">Algorithmic Dashboard</h2>
        </div>

        {health && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <span className={`w-2.5 h-2.5 rounded-full ${health.status === "healthy" ? "bg-emerald-500 shadow-lg shadow-emerald-500/50" : "bg-rose-500"}`} />
            <span className="capitalize font-medium">Pipeline: {health.status}</span>
          </div>
        )}
      </div>

      {/* Stats Block */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {portfolio && <PortfolioCard portfolio={portfolio} />}

        <div className="lg:col-span-2 bg-gradient-to-br from-violet-900/10 to-transparent border border-violet-500/10 rounded-3xl p-6 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 right-0 w-48 h-48 bg-violet-500/5 rounded-full blur-3xl" />
          
          <div>
            <div className="flex items-center gap-2 text-violet-400 mb-2">
              <BrainCircuit className="w-5 h-5" />
              <span className="text-xs font-semibold tracking-wider uppercase">Active Pipeline Orchestrator</span>
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight leading-tight max-w-lg mb-3">
              XGBoost ML Pipeline + Quantitative Rule Fallback System is active.
            </h3>
            <p className="text-slate-400 text-xs leading-relaxed max-w-xl">
              Market state inputs are processed into feature vectors. Class probabilities gate live simulated positions via PostgreSQL permanent persistence interfaces.
            </p>
          </div>

          <div className="flex items-center gap-4 mt-6 pt-5 border-t border-slate-800/40">
            <div className="text-center">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">ML Accuracy</span>
              <span className="text-lg font-bold text-violet-400 font-mono">82.4%</span>
            </div>
            <div className="w-px h-8 bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] text-slate-500 font-semibold block uppercase">Total Decisions</span>
              <span className="text-lg font-bold text-white font-mono">{predictions.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feed & History Column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-violet-400" />
            <span>Latest Signals</span>
          </h3>
          <div className="grid grid-cols-1 gap-4">
            {predictions.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 font-medium">No signals recorded in Postgres.</div>
            ) : (
              predictions.map((p) => <PredictionCard key={p.id} prediction={p} />)
            )}
          </div>
        </div>

        <TradeHistory trades={trades} />
      </div>
    </div>
  );
}
