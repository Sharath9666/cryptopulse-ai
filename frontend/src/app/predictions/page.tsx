"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/services/api";
import { PredictionRecord } from "@/types";
import PredictionCard from "@/components/ui/PredictionCard";
import { Loader2, PlayCircle, Eye, CheckCircle2 } from "lucide-react";

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<PredictionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [symbolFilter, setSymbolFilter] = useState("");
  const [correctFilter, setCorrectFilter] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    async function loadPredictions() {
      setLoading(true);
      try {
        const data = await apiService.getPredictionsHistory({
          symbol: symbolFilter || undefined,
          correct: correctFilter,
          page,
          size: 6,
        });
        setPredictions(data.items);
        setTotalPages(data.pages);
      } catch (err) {
        console.error("Failed to load predictions:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPredictions();
  }, [page, symbolFilter, correctFilter]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-center border-b border-slate-900 pb-6">
        <div>
          <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">PERSISTED MACHINE LEARNING INTERFACES</span>
          <h2 className="text-3xl font-black text-white tracking-tight mt-1">AI Signals Engine</h2>
        </div>

        {/* Filter Toolbar */}
        <div className="flex gap-3">
          <select 
            value={symbolFilter} 
            onChange={(e) => { setSymbolFilter(e.target.value); setPage(1); }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-350 focus:outline-none"
          >
            <option value="">All Instruments</option>
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="ETHUSDT">ETHUSDT</option>
            <option value="DOGEUSDT">DOGEUSDT</option>
            <option value="SOLUSDT">SOLUSDT</option>
            <option value="XRPUSDT">XRPUSDT</option>
          </select>

          <select
            value={correctFilter === undefined ? "all" : String(correctFilter)}
            onChange={(e) => {
              const val = e.target.value;
              setCorrectFilter(val === "all" ? undefined : val === "true");
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-350 focus:outline-none"
          >
            <option value="all">All Outcomes</option>
            <option value="true">Correct Outcomes</option>
            <option value="false">Incorrect Outcomes</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {predictions.length === 0 ? (
              <div className="col-span-full text-center py-12 text-sm text-slate-500 font-semibold">
                No signals found matching selected filters.
              </div>
            ) : (
              predictions.map((p) => <PredictionCard key={p.id} prediction={p} />)
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-8">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-4 py-2 text-xs font-bold bg-slate-900 border border-slate-800 hover:border-slate-700 text-white rounded-xl disabled:opacity-50 disabled:pointer-events-none"
              >
                Previous
              </button>
              <span className="text-xs font-semibold text-slate-400 font-mono">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page === totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-4 py-2 text-xs font-bold bg-slate-900 border border-slate-800 hover:border-slate-700 text-white rounded-xl disabled:opacity-50 disabled:pointer-events-none"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
