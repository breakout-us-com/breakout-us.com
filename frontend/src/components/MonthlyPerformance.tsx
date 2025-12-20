"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface MonthlyData {
  month: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_profit_pct: number;
  avg_profit_pct: number;
}

interface MonthlyResponse {
  count: number;
  monthly: MonthlyData[];
  error?: string;
}

export default function MonthlyPerformance() {
  const [data, setData] = useState<MonthlyResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/paper-trading/monthly`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch(() => {
        setData({ count: 0, monthly: [], error: "Failed to fetch" });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 총 수익률 계산
  const totalProfit = data?.monthly.reduce((sum, m) => sum + m.total_profit_pct, 0) || 0;

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
          Monthly Performance
        </h2>
        <div className="text-right">
          <span className="text-sm text-zinc-500 dark:text-zinc-400">Total</span>
          <span
            className={`ml-2 text-lg font-bold ${
              totalProfit >= 0
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {totalProfit >= 0 ? "+" : ""}
            {totalProfit.toFixed(2)}%
          </span>
        </div>
      </div>

      {data?.error && !data.monthly.length ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
        </div>
      ) : data?.monthly.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p>No trading history yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data?.monthly.map((month) => (
            <div
              key={month.month}
              className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-700/50 rounded-lg"
            >
              <div className="flex items-center gap-4">
                <span className="font-medium text-zinc-900 dark:text-white w-20">
                  {month.month}
                </span>
                <span className="text-sm text-zinc-500 dark:text-zinc-400">
                  {month.trades} trades
                </span>
                <span className="text-sm">
                  <span className="text-green-600 dark:text-green-400">{month.wins}W</span>
                  {" / "}
                  <span className="text-red-600 dark:text-red-400">{month.losses}L</span>
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`text-sm ${
                    month.win_rate >= 50
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {month.win_rate.toFixed(0)}% WR
                </span>
                <span
                  className={`font-semibold min-w-[80px] text-right ${
                    month.total_profit_pct >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {month.total_profit_pct >= 0 ? "+" : ""}
                  {month.total_profit_pct.toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
