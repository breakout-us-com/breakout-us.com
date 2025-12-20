"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface Position {
  id: number;
  ticker: string;
  market: string;
  entry_price: number;
  current_price: number | null;
  quantity: number;
  investment_amount: number;
  current_value: number;
  pnl_amount: number;
  pnl_pct: number | null;
  entry_date: string;
  pattern: string;
  stop_loss: number | null;
  take_profit: number | null;
  holding_days: number;
}

interface PositionsData {
  count: number;
  winning: number;
  losing: number;
  total_invested: number;
  total_value: number;
  total_pnl_amount: number;
  total_pnl_pct: number;
  available_capital: number;
  positions: Position[];
  error?: string;
}

const PATTERN_COLORS: Record<string, string> = {
  "컵앤핸들": "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
  "피벗돌파": "bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300",
  "베이스돌파": "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
};

export default function CurrentPositions() {
  const [data, setData] = useState<PositionsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/paper-trading/positions`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch(() => {
        setData({ count: 0, positions: [], error: "Failed to fetch" });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
          Open Positions
        </h2>
        <div className="flex items-center gap-3">
          {data && data.total_pnl_pct !== undefined && (
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
              data.total_pnl_pct >= 0
                ? "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300"
                : "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300"
            }`}>
              {data.total_pnl_pct >= 0 ? "+" : ""}{data.total_pnl_pct.toFixed(2)}%
              {" "}(${data.total_pnl_amount >= 0 ? "+" : ""}{data.total_pnl_amount.toLocaleString()})
            </span>
          )}
          <span className="text-sm bg-zinc-100 dark:bg-zinc-700 px-3 py-1 rounded-full text-zinc-600 dark:text-zinc-300">
            {data?.count || 0} positions
          </span>
        </div>
      </div>

      {data?.error && !data.positions.length ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
        </div>
      ) : data?.positions.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p>No open positions</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Ticker</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Entry</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Current</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">P&L</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Stop</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Target</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Days</th>
              </tr>
            </thead>
            <tbody>
              {data?.positions.map((pos) => (
                <tr
                  key={pos.id}
                  className="border-b border-zinc-100 dark:border-zinc-700/50"
                >
                  <td className="py-2 px-2 font-semibold text-zinc-900 dark:text-white">
                    {pos.ticker}
                  </td>
                  <td className="py-2 px-2 text-right text-zinc-600 dark:text-zinc-300">
                    ${pos.entry_price.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-right text-zinc-600 dark:text-zinc-300">
                    {pos.current_price ? `$${pos.current_price.toFixed(2)}` : "-"}
                  </td>
                  <td className={`py-2 px-2 text-right font-semibold ${
                    pos.pnl_pct !== null
                      ? pos.pnl_pct >= 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                      : "text-zinc-400"
                  }`}>
                    {pos.pnl_pct !== null
                      ? `${pos.pnl_pct >= 0 ? "+" : ""}${pos.pnl_pct.toFixed(2)}%`
                      : "-"}
                  </td>
                  <td className="py-2 px-2 text-right text-red-600 dark:text-red-400 text-xs">
                    {pos.stop_loss ? `$${pos.stop_loss.toFixed(0)}` : "-"}
                  </td>
                  <td className="py-2 px-2 text-right text-green-600 dark:text-green-400 text-xs">
                    {pos.take_profit ? `$${pos.take_profit.toFixed(0)}` : "-"}
                  </td>
                  <td className="py-2 px-2 text-right text-zinc-500 dark:text-zinc-400">
                    {pos.holding_days}d
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
