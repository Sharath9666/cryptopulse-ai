import { PortfolioState } from "@/types";
import { Wallet, TrendingUp, TrendingDown, Layers, Landmark } from "lucide-react";

interface PortfolioCardProps {
  portfolio: PortfolioState;
}

export default function PortfolioCard({ portfolio }: PortfolioCardProps) {
  const totalValue = portfolio.balance;
  const netProfit = portfolio.profit;
  const isProfit = netProfit >= 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 relative overflow-hidden shadow-xl">
      {/* Decorative gradient overlay */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-violet-600/10 rounded-full blur-3xl" />

      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-violet-600/10 border border-violet-500/20 text-violet-400 rounded-2xl">
          <Landmark className="w-6 h-6" />
        </div>
        <div>
          <span className="text-xs text-slate-500 tracking-wider font-semibold uppercase">PAPER BALANCE</span>
          <h3 className="text-sm font-bold text-white leading-none mt-1">Virtual Ledger Account</h3>
        </div>
      </div>

      <div className="mb-6">
        <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">AVAILABLE EQUITY</span>
        <div className="text-4xl font-black text-white tracking-tight font-mono mt-1">
          ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-5 border-t border-slate-800/80">
        <div>
          <span className="text-[10px] text-slate-500 font-semibold block mb-1">TOTAL PROFIT/LOSS</span>
          <div className={`flex items-center gap-1.5 font-bold font-mono ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
            {isProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>${netProfit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          </div>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 font-semibold block mb-1">ACTIVE POSITIONS</span>
          <div className="flex items-center gap-1.5 text-white font-bold font-mono">
            <Layers className="w-4 h-4 text-violet-400" />
            <span>{portfolio.open_positions.length} Open</span>
          </div>
        </div>
      </div>
    </div>
  );
}
