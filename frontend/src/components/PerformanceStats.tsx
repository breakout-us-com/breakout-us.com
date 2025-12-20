"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface StatsData {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit: number;
  avg_profit_pct: number;
  avg_win_pct: number;
  avg_loss_pct: number;
  max_profit_pct: number;
  max_loss_pct: number;
  pattern_stats: Record<
    string,
    { total: number; wins: number; losses: number; win_rate: number; avg_profit_pct: number }
  >;
  reason_stats: Record<string, { count: number; avg_profit_pct: number }>;
  start_date: string | null;
  end_date: string | null;
}

export default function PerformanceStats() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/backtest/stats`)
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
            Backtest Performance
          </h2>
          {stats?.start_date && stats?.end_date && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
              {stats.start_date} ~ {stats.end_date}
            </p>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Trades"
          value={stats?.total_trades?.toString() || "0"}
        />
        <StatCard
          label="Win Rate"
          value={`${stats?.win_rate?.toFixed(1) || 0}%`}
          color={stats?.win_rate && stats.win_rate >= 50 ? "green" : "red"}
        />
        <StatCard
          label="Avg Profit"
          value={`${stats?.avg_profit_pct?.toFixed(2) || 0}%`}
          color={stats?.avg_profit_pct && stats.avg_profit_pct >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Total Profit"
          value={`$${stats?.total_profit?.toLocaleString() || 0}`}
          color={stats?.total_profit && stats.total_profit >= 0 ? "green" : "red"}
        />
      </div>

      {/* Win/Loss Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Winning Trades" value={stats?.winning_trades?.toString() || "0"} color="green" />
        <StatCard label="Losing Trades" value={stats?.losing_trades?.toString() || "0"} color="red" />
        <StatCard
          label="Avg Win"
          value={`+${stats?.avg_win_pct?.toFixed(2) || 0}%`}
          color="green"
        />
        <StatCard
          label="Avg Loss"
          value={`${stats?.avg_loss_pct?.toFixed(2) || 0}%`}
          color="red"
        />
      </div>

      {/* Pattern Stats */}
      <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">
        Pattern Performance
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="text-left py-2 px-3 text-zinc-500 dark:text-zinc-400">Pattern</th>
              <th className="text-right py-2 px-3 text-zinc-500 dark:text-zinc-400">Trades</th>
              <th className="text-right py-2 px-3 text-zinc-500 dark:text-zinc-400">Wins</th>
              <th className="text-right py-2 px-3 text-zinc-500 dark:text-zinc-400">Win Rate</th>
              <th className="text-right py-2 px-3 text-zinc-500 dark:text-zinc-400">Avg Profit</th>
            </tr>
          </thead>
          <tbody>
            {stats?.pattern_stats &&
              Object.entries(stats.pattern_stats).map(([pattern, data]) => (
                <tr
                  key={pattern}
                  className="border-b border-zinc-100 dark:border-zinc-700/50"
                >
                  <td className="py-2 px-3 font-medium text-zinc-900 dark:text-white">
                    {pattern}
                  </td>
                  <td className="py-2 px-3 text-right text-zinc-600 dark:text-zinc-300">
                    {data.total}
                  </td>
                  <td className="py-2 px-3 text-right text-green-600 dark:text-green-400">
                    {data.wins}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span
                      className={
                        data.win_rate >= 50
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }
                    >
                      {data.win_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span
                      className={
                        data.avg_profit_pct >= 0
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }
                    >
                      {data.avg_profit_pct >= 0 ? "+" : ""}
                      {data.avg_profit_pct.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
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
    <div className="bg-zinc-50 dark:bg-zinc-700/50 rounded-lg p-4">
      <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
    </div>
  );
}
