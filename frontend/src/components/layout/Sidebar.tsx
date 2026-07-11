"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Activity, 
  BrainCircuit, 
  History, 
  TrendingUp, 
  Database,
  ShieldCheck
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/trading", label: "Live Market", icon: Activity },
  { href: "/predictions", label: "AI Signals", icon: BrainCircuit },
  { href: "/backtesting", label: "Backtesting", icon: History },
  { href: "/performance", label: "Performance", icon: TrendingUp },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0">
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center font-bold text-white shadow-lg shadow-violet-500/30">
          Ω
        </div>
        <div>
          <h1 className="font-bold text-lg text-white leading-none">CryptoPulse</h1>
          <span className="text-xs font-semibold text-violet-400">DECISION ENGINE</span>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? "bg-violet-600/10 text-violet-400 border border-violet-500/20 font-semibold" 
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 space-y-3 bg-slate-950/40">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 w-fit">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>PRODUCTION PERMANENCE</span>
        </div>
        <div className="text-[10px] text-slate-500 space-y-1">
          <p>DB Host: <span className="text-slate-400">localhost</span></p>
          <p>PostgreSQL Schema: <span className="text-slate-400">Healthy</span></p>
        </div>
      </div>
    </aside>
  );
}
