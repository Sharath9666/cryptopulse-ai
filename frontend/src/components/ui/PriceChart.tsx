"use client";

import { useEffect, useRef } from "react";
import { MarketCandle } from "@/types";

interface PriceChartProps {
  candles: MarketCandle[];
  symbol: string;
  livePrice?: number | null;
}

export default function PriceChart({ candles, symbol, livePrice }: PriceChartProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear background
    ctx.fillStyle = "#020617"; // bg-slate-950
    ctx.fillRect(0, 0, width, height);

    if (candles.length === 0) {
      ctx.fillStyle = "#64748b";
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No historical candle data loaded.", width / 2, height / 2);
      return;
    }

    // Prepare candles to draw
    const displayCandles = [...candles];
    if (livePrice && displayCandles.length > 0) {
      const last = displayCandles[displayCandles.length - 1];
      displayCandles[displayCandles.length - 1] = {
        ...last,
        close: livePrice,
        high: Math.max(last.high, livePrice),
        low: Math.min(last.low, livePrice),
      };
    }

    const ohlcCloses = displayCandles.map((c) => c.close);
    const ohlcHighs = displayCandles.map((c) => c.high);
    const ohlcLows = displayCandles.map((c) => c.low);

    const maxVal = Math.max(...ohlcHighs);
    const minVal = Math.min(...ohlcLows);
    const padding = (maxVal - minVal) * 0.1 || 1.0;

    const scaleY = (val: number) => {
      return height - 40 - ((val - (minVal - padding)) / (maxVal - minVal + padding * 2)) * (height - 60);
    };

    const candleWidth = (width - 60) / displayCandles.length;
    const spacing = Math.max(1, candleWidth * 0.2);

    // Draw grid lines
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 0.5;
    for (let i = 1; i <= 4; i++) {
      const y = (height / 5) * i;
      ctx.beginPath();
      ctx.moveTo(10, y);
      ctx.lineTo(width - 60, y);
      ctx.stroke();
    }

    // Draw candles
    displayCandles.forEach((c, index) => {
      const x = 10 + index * candleWidth;
      const xCenter = x + (candleWidth - spacing) / 2;

      const yOpen = scaleY(c.open);
      const yClose = scaleY(c.close);
      const yHigh = scaleY(c.high);
      const yLow = scaleY(c.low);

      const isBullish = c.close >= c.open;
      const color = isBullish ? "#10b981" : "#f43f5e"; // Emerald / Rose

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(1, candleWidth * 0.08);
      ctx.beginPath();
      ctx.moveTo(xCenter, yHigh);
      ctx.lineTo(xCenter, yLow);
      ctx.stroke();

      // Body
      ctx.fillStyle = color;
      const bodyHeight = Math.max(1, Math.abs(yClose - yOpen));
      const bodyTop = Math.min(yOpen, yClose);
      ctx.fillRect(x, bodyTop, candleWidth - spacing, bodyHeight);
    });

    // Draw price scale on right
    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px monospace";
    ctx.textAlign = "left";
    ctx.fillText(maxVal.toFixed(2), width - 50, scaleY(maxVal));
    ctx.fillText(((maxVal + minVal) / 2).toFixed(2), width - 50, scaleY((maxVal + minVal) / 2));
    ctx.fillText(minVal.toFixed(2), width - 50, scaleY(minVal));
  }, [candles, livePrice]);

  return (
    <div className="relative w-full h-full bg-slate-950 rounded-2xl border border-slate-800 p-4">
      <div className="absolute top-4 left-4 z-10 flex items-center justify-between w-[95%]">
        <div>
          <span className="text-xs font-semibold text-violet-400 tracking-wider uppercase">DECISION ENGINE STREAM</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">{symbol}</h2>
        </div>
        {livePrice && (
          <div className="text-right">
            <span className="text-xs text-slate-500 font-medium">LIVE BID</span>
            <div className="text-2xl font-bold text-emerald-400 tracking-tight font-mono">
              ${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        )}
      </div>
      <canvas ref={canvasRef} className="w-full h-full mt-8" />
    </div>
  );
}
