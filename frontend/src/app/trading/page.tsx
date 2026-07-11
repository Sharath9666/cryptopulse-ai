"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/services/api";
import { binanceWS } from "@/services/websocket";
import { MarketCandle } from "@/types";
import PriceChart from "@/components/ui/PriceChart";
import { Loader2 } from "lucide-react";

const SUPPORTED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT"];

export default function TradingPage() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [candles, setCandles] = useState<MarketCandle[]>([]);
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Load historical candles
  useEffect(() => {
    async function loadCandles() {
      setLoading(true);
      try {
        const history = await apiService.getCandlesHistory({
          symbol: selectedSymbol,
          timeframe: "1m",
          size: 40,
        });
        setCandles(history.items);
      } catch (err) {
        console.error("Failed to load historical candles:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCandles();
  }, [selectedSymbol]);

  // Connect live WebSocket stream
  useEffect(() => {
    const handleTick = (tick: { price: number }) => {
      setLivePrice(tick.price);
    };

    binanceWS.subscribe(selectedSymbol, handleTick);
    return () => {
      binanceWS.unsubscribe(selectedSymbol, handleTick);
      setLivePrice(null);
    };
  }, [selectedSymbol]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-center border-b border-slate-900 pb-6">
        <div>
          <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">LIVE STREAMED TICKERS</span>
          <h2 className="text-3xl font-black text-white tracking-tight mt-1">Live Trading Terminals</h2>
        </div>

        {/* Symbol Toggles */}
        <div className="flex gap-2">
          {SUPPORTED_SYMBOLS.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedSymbol(s)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all duration-200 ${
                selectedSymbol === s
                  ? "bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-500/20"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {s.replace("USDT", "")}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Main Price Chart Terminal */}
        <div className="lg:col-span-3 h-[500px]">
          {loading ? (
            <div className="flex h-full items-center justify-center bg-slate-900 border border-slate-800 rounded-3xl">
              <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
            </div>
          ) : (
            <PriceChart candles={candles} symbol={selectedSymbol} livePrice={livePrice} />
          )}
        </div>

        {/* Terminal stats metadata panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Instrument Specification</h3>
            <div className="space-y-4 text-xs font-mono">
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">Asset Symbol</span>
                <span className="text-white font-semibold">{selectedSymbol}</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">Margin Type</span>
                <span className="text-violet-400 font-semibold">Simulated Spot</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">Order Quantity</span>
                <span className="text-white font-semibold">10% Portfolio</span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">WebSocket Ping</span>
                <span className="text-emerald-400 font-semibold">Active</span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-850/40 text-[10px] text-slate-500 leading-relaxed">
            Candle records are generated via Binance API endpoints, saved directly inside Postgres, and synced to this interface.
          </div>
        </div>
      </div>
    </div>
  );
}
