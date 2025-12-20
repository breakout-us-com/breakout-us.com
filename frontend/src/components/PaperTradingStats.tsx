"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface StatsData {
  start_date: string | null;
  trading_days: number | null;
  open_positions: number;
  open_winning: number;
  open_losing: number;
  open_pnl_pct: number;
  open_avg_pnl_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_profit_pct: number;
  avg_win_pct: number;
  avg_loss_pct: number;
  max_profit_pct: number;
  max_loss_pct: number;
  total_profit_pct: number;
  error?: string;
}

export default function PaperTradingStats() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/paper-trading/stats`)
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => {
        setStats(null);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="flex gap-3 overflow-x-auto">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-16 w-24 flex-shrink-0 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (stats?.error || !stats) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-white mb-4">
          Paper Trading Stats
        </h2>
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
          <p className="text-xs mt-1">환경변수에 DB 설정을 추가해주세요</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
            Paper Trading Stats
          </h2>
          {stats.start_date && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              Since {stats.start_date} ({stats.trading_days} days)
            </p>
          )}
        </div>
        <span className="text-sm bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 px-3 py-1 rounded-full">
          {stats.open_positions} Open
        </span>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2">
        <StatCard label="Total Trades" value={stats.total_trades.toString()} />
        <StatCard
          label="Win Rate"
          value={`${stats.win_rate}%`}
          color={stats.win_rate >= 50 ? "green" : "red"}
        />
        <StatCard
          label="Total Return"
          value={`${stats.total_profit_pct >= 0 ? "+" : ""}${stats.total_profit_pct}%`}
          color={stats.total_profit_pct >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Avg Profit"
          value={`${stats.avg_profit_pct >= 0 ? "+" : ""}${stats.avg_profit_pct}%`}
          color={stats.avg_profit_pct >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Winning"
          value={stats.winning_trades.toString()}
          color="green"
        />
        <StatCard
          label="Losing"
          value={stats.losing_trades.toString()}
          color="red"
        />
        <StatCard
          label="Avg Win"
          value={`+${stats.avg_win_pct}%`}
          color="green"
        />
        <StatCard
          label="Avg Loss"
          value={`${stats.avg_loss_pct}%`}
          color="red"
        />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: "green" | "red";
}) {
  const colorClass =
    color === "green"
      ? "text-green-600 dark:text-green-400"
      : color === "red"
      ? "text-red-600 dark:text-red-400"
      : "text-zinc-900 dark:text-white";

  return (
    <div className="bg-zinc-50 dark:bg-zinc-700/50 rounded-lg p-3 flex-shrink-0 min-w-[100px]">
      <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1 whitespace-nowrap">{label}</p>
      <p className={`text-xl font-bold ${colorClass}`}>{value}</p>
    </div>
  );
}
