import { TradeRecord } from "@/types";
import { ArrowUpRight, ArrowDownRight, CircleDollarSign } from "lucide-react";

interface TradeHistoryProps {
  trades: TradeRecord[];
}

export default function TradeHistory({ trades }: TradeHistoryProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl h-full flex flex-col">
      <div className="flex items-center gap-2 mb-6">
        <CircleDollarSign className="w-5 h-5 text-violet-400" />
        <h3 className="font-bold text-white tracking-tight">Ledger Operations</h3>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[400px] space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-800">
        {trades.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500 font-medium">
            No executed operations in database.
          </div>
        ) : (
          trades.map((t) => {
            const isProfit = t.profit_loss >= 0;
            const pnlColor = isProfit ? "text-emerald-400" : "text-rose-400";
            return (
              <div 
                key={t.trade_id} 
                className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-950/40 border border-slate-800/40 hover:border-slate-800 transition-all duration-200"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${isProfit ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                    {isProfit ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-200">{t.symbol}</span>
                      <span className="text-[9px] font-bold text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded uppercase font-mono tracking-wider">
                        {t.status}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                      Qty: {t.quantity.toFixed(4)} @ ${t.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <div className={`text-sm font-bold font-mono ${pnlColor}`}>
                    {t.profit_loss >= 0 ? "+" : ""}${t.profit_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  {t.exit_price && (
                    <span className="text-[9px] text-slate-500 font-mono mt-0.5 block">
                      Exit: ${t.exit_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
