"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/services/api";
import { PredictionRecord } from "@/types";
import AccuracyGraph from "@/components/ui/AccuracyGraph";
import { Loader2, TrendingUp, ShieldAlert, BadgeCheck } from "lucide-react";

export default function PerformancePage() {
  const [predictions, setPredictions] = useState<PredictionRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPerformanceData() {
      try {
        const data = await apiService.getPredictionsHistory({ page: 1, size: 50 });
        setPredictions(data.items);
      } catch (err) {
        console.error("Failed to load prediction records:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPerformanceData();
  }, []);

  const evaluated = predictions.filter((p) => p.correct !== null && p.correct !== undefined);
  const correctCount = evaluated.filter((p) => p.correct).length;
  const accuracy = evaluated.length > 0 ? (correctCount / evaluated.length) * 100 : 0;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-center border-b border-slate-900 pb-6">
        <div>
          <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">ML PRECISION & CLASSIFICATION METRICS</span>
          <h2 className="text-3xl font-black text-white tracking-tight mt-1">Accuracy Metrics</h2>
        </div>
      </div>

      {loading ? (
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Accuracy Chart */}
          <div className="lg:col-span-2">
            <AccuracyGraph predictions={predictions} />
          </div>

          {/* Stats Breakdown Column */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6">
              <h3 className="font-bold text-white uppercase tracking-wider text-xs">Analytics Breakdown</h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-2xl">
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase mb-1">AGGREGATE ACCURACY</span>
                  <span className="text-2xl font-bold text-violet-400 font-mono">{accuracy.toFixed(1)}%</span>
                </div>

                <div className="bg-slate-950/40 border border-slate-850 p-4 rounded-2xl">
                  <span className="text-[10px] text-slate-500 font-semibold block uppercase mb-1">EVALUATED COUNT</span>
                  <span className="text-2xl font-bold text-white font-mono">{evaluated.length}</span>
                </div>
              </div>

              <div className="space-y-3 font-mono text-xs border-t border-slate-800/60 pt-4">
                <div className="flex justify-between">
                  <span className="text-slate-500">Correct Predictions</span>
                  <span className="text-emerald-400 font-bold">{correctCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Incorrect Predictions</span>
                  <span className="text-rose-400 font-bold">{evaluated.length - correctCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Pending Evaluation</span>
                  <span className="text-slate-400 font-bold">{predictions.length - evaluated.length}</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-violet-600/5 border border-violet-500/10 text-[10px] text-slate-400 leading-relaxed">
              Precision metrics are compiled by matching entry predictions against asset bid ticks recorded inside the database persistence engine.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
