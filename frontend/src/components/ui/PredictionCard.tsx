import { PredictionRecord } from "@/types";
import { Brain, Cpu, Zap, AlertTriangle } from "lucide-react";

interface PredictionCardProps {
  prediction: PredictionRecord;
}

export default function PredictionCard({ prediction }: PredictionCardProps) {
  const isBullish = prediction.direction === "BULLISH";
  const isBearish = prediction.direction === "BEARISH";

  let badgeColor = "bg-slate-800 text-slate-400 border-slate-700";
  if (isBullish) badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  if (isBearish) badgeColor = "bg-rose-500/10 text-rose-400 border-rose-500/20";

  const isML = prediction.prediction_id.includes("ml") || prediction.prediction_id.includes("_"); // simple heuristic

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all duration-200 shadow-md">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-white tracking-tight">{prediction.symbol}</span>
            <span className="text-xs text-slate-500 font-medium font-mono">{prediction.timeframe}</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono mt-1 block">
            {new Date(prediction.prediction_time).toLocaleTimeString()}
          </span>
        </div>

        <div className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${badgeColor} tracking-wide`}>
          {prediction.direction}
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Confidence Probability</span>
            <span className="font-mono font-semibold">{prediction.confidence}</span>
          </div>
          <div className="w-full bg-slate-850 h-2 rounded-full overflow-hidden border border-slate-800/40">
            <div 
              className={`h-full rounded-full ${isML ? "bg-violet-500" : "bg-indigo-500"}`}
              style={{ width: `${prediction.predicted_move * 20}%` }} // mock probability mapping
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
          <div>
            <span className="text-slate-500 block">Target Move</span>
            <span className={`font-mono font-semibold ${isBullish ? "text-emerald-400" : isBearish ? "text-rose-400" : "text-slate-400"}`}>
              {prediction.predicted_move > 0 ? "+" : ""}{prediction.predicted_move.toFixed(2)}%
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Entry Reference</span>
            <span className="font-mono font-semibold text-slate-300">
              ${prediction.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center gap-1.5 text-[10px] text-slate-400 font-medium">
          {isML ? (
            <>
              <Cpu className="w-3.5 h-3.5 text-violet-400" />
              <span>XGBoost ML Pipeline <span className="text-violet-400 font-bold font-mono">v1</span></span>
            </>
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              <span>Quantitative Rule Fallback Engine</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
