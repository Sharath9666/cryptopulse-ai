"use client";

import { useEffect, useRef } from "react";
import { PredictionRecord } from "@/types";

interface AccuracyGraphProps {
  predictions: PredictionRecord[];
}

export default function AccuracyGraph({ predictions }: AccuracyGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear
    ctx.fillStyle = "#0f172a"; // bg-slate-900
    ctx.fillRect(0, 0, width, height);

    // Compute rolling accuracy curve
    const evaluated = predictions.filter((p) => p.correct !== null && p.correct !== undefined);

    if (evaluated.length === 0) {
      ctx.fillStyle = "#64748b";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No evaluated predictions in range.", width / 2, height / 2);
      return;
    }

    // Sort chronologically (oldest to newest)
    const sorted = [...evaluated].sort(
      (a, b) => new Date(a.prediction_time).getTime() - new Date(b.prediction_time).getTime()
    );

    const accuracyCurve: number[] = [];
    let correctCount = 0;
    sorted.forEach((p, idx) => {
      if (p.correct) correctCount++;
      accuracyCurve.push((correctCount / (idx + 1)) * 100);
    });

    // Drawing metrics
    const margin = 40;
    const chartWidth = width - margin * 2;
    const chartHeight = height - margin * 2;

    const minX = 0;
    const maxX = accuracyCurve.length - 1;
    const minY = 0;
    const maxY = 100;

    const getX = (index: number) => {
      if (maxX === 0) return margin;
      return margin + (index / maxX) * chartWidth;
    };

    const getY = (val: number) => {
      return margin + chartHeight - (val / maxY) * chartHeight;
    };

    // Draw grid horizontal lines
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const val = i * 25;
      const y = getY(val);
      ctx.beginPath();
      ctx.moveTo(margin, y);
      ctx.lineTo(width - margin, y);
      ctx.stroke();

      // label
      ctx.fillStyle = "#475569";
      ctx.font = "9px monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${val}%`, margin - 10, y + 3);
    }

    // Draw curve path
    ctx.strokeStyle = "#8b5cf6"; // Violet
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    accuracyCurve.forEach((val, idx) => {
      const cx = getX(idx);
      const cy = getY(val);
      if (idx === 0) {
        ctx.moveTo(cx, cy);
      } else {
        ctx.lineTo(cx, cy);
      }
    });
    ctx.stroke();

    // Draw area gradient under the curve
    const gradient = ctx.createLinearGradient(0, margin, 0, margin + chartHeight);
    gradient.addColorStop(0, "rgba(139, 92, 246, 0.15)");
    gradient.addColorStop(1, "rgba(139, 92, 246, 0.0)");
    ctx.fillStyle = gradient;

    ctx.beginPath();
    ctx.moveTo(margin, margin + chartHeight);
    accuracyCurve.forEach((val, idx) => {
      ctx.lineTo(getX(idx), getY(val));
    });
    ctx.lineTo(getX(accuracyCurve.length - 1), margin + chartHeight);
    ctx.closePath();
    ctx.fill();

    // Draw points for small sets
    if (accuracyCurve.length < 50) {
      ctx.fillStyle = "#a78bfa";
      accuracyCurve.forEach((val, idx) => {
        ctx.beginPath();
        ctx.arc(getX(idx), getY(val), 3.5, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }, [predictions]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl w-full">
      <h3 className="font-bold text-white tracking-tight mb-4">ML Rolling Precision Rate</h3>
      <div className="w-full h-64">
        <canvas ref={canvasRef} className="w-full h-full" />
      </div>
    </div>
  );
}
