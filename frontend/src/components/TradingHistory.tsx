"use client";
import { API_URL } from "@/lib/config";

import { useEffect, useState } from "react";

interface Trade {
  id: number;
  ticker: string;
  market: string;
  entry_price: number;
  entry_date: string;
  exit_price: number | null;
  exit_date: string | null;
  pattern: string;
  exit_reason: string | null;
  profit_pct: number;
  holding_days: number;
}

interface TradesData {
  count: number;
  trades: Trade[];
  error?: string;
}

const EXIT_REASON_CONFIG: Record<string, { label: string; color: string }> = {
  stop_loss: { label: "손절", color: "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300" },
  take_profit: { label: "익절", color: "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300" },
  max_hold: { label: "만기", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300" },
  manual: { label: "수동", color: "bg-zinc-100 text-zinc-700 dark:bg-zinc-700 dark:text-zinc-300" },
};

export default function TradingHistory() {
  const [data, setData] = useState<TradesData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/paper-trading/closed?limit=20`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch(() => {
        setData({ count: 0, trades: [], error: "Failed to fetch" });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 sm:p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 통계 계산
  const totalPnL = data?.trades.reduce((sum, t) => sum + t.profit_pct, 0) || 0;
  const winCount = data?.trades.filter(t => t.profit_pct > 0).length || 0;
  const lossCount = data?.trades.filter(t => t.profit_pct <= 0).length || 0;

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-0 mb-4">
        <h2 className="text-lg sm:text-xl font-bold text-zinc-900 dark:text-white">
          Trading History
        </h2>
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs sm:text-sm font-semibold px-2 sm:px-3 py-1 rounded-full ${
            totalPnL >= 0
              ? "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300"
              : "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300"
          }`}>
            {totalPnL >= 0 ? "+" : ""}{totalPnL.toFixed(2)}%
          </span>
          <span className="text-xs bg-zinc-100 dark:bg-zinc-700 px-2 py-1 rounded-full text-zinc-600 dark:text-zinc-300">
            <span className="text-green-600 dark:text-green-400">{winCount}W</span>
            {" / "}
            <span className="text-red-600 dark:text-red-400">{lossCount}L</span>
          </span>
        </div>
      </div>

      {data?.error && !data.trades.length ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
        </div>
      ) : data?.trades.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p>No closed trades yet</p>
        </div>
      ) : (
        <>
          {/* Mobile: Card Layout */}
          <div className="sm:hidden space-y-3">
            {data?.trades.map((trade) => (
              <div
                key={trade.id}
                className="p-3 bg-zinc-50 dark:bg-zinc-700/50 rounded-lg border-l-4"
                style={{
                  borderLeftColor: trade.profit_pct > 0 ? "#22c55e" : "#ef4444"
                }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-zinc-900 dark:text-white">
                      {trade.ticker}
                    </span>
                    {trade.exit_reason && (
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                        EXIT_REASON_CONFIG[trade.exit_reason]?.color || "bg-zinc-100 text-zinc-600"
                      }`}>
                        {EXIT_REASON_CONFIG[trade.exit_reason]?.label || trade.exit_reason}
                      </span>
                    )}
                  </div>
                  <span className={`text-base font-semibold ${
                    trade.profit_pct > 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    {trade.profit_pct > 0 ? "+" : ""}{trade.profit_pct.toFixed(2)}%
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-zinc-500 dark:text-zinc-400">Entry</span>
                    <span className="text-zinc-700 dark:text-zinc-300">${trade.entry_price.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500 dark:text-zinc-400">Exit</span>
                    <span className="text-zinc-700 dark:text-zinc-300">
                      {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : "-"}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
                  <span>{trade.entry_date} → {trade.exit_date}</span>
                  <span>{trade.holding_days}일</span>
                </div>
              </div>
            ))}
          </div>

          {/* Desktop: Table Layout */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-700">
                  <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Ticker</th>
                  <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Entry</th>
                  <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Exit</th>
                  <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">P&L</th>
                  <th className="text-center py-2 px-2 text-zinc-500 dark:text-zinc-400">Reason</th>
                  <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Days</th>
                </tr>
              </thead>
              <tbody>
                {data?.trades.map((trade) => (
                  <tr
                    key={trade.id}
                    className="border-b border-zinc-100 dark:border-zinc-700/50 hover:bg-zinc-50 dark:hover:bg-zinc-700/30"
                  >
                    <td className="py-2 px-2 font-semibold text-zinc-900 dark:text-white">
                      {trade.ticker}
                    </td>
                    <td className="py-2 px-2 text-zinc-600 dark:text-zinc-300">
                      <div>${trade.entry_price.toFixed(2)}</div>
                      <div className="text-xs text-zinc-400">{trade.entry_date}</div>
                    </td>
                    <td className="py-2 px-2 text-zinc-600 dark:text-zinc-300">
                      <div>{trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : "-"}</div>
                      <div className="text-xs text-zinc-400">{trade.exit_date || "-"}</div>
                    </td>
                    <td className={`py-2 px-2 text-right font-semibold ${
                      trade.profit_pct > 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}>
                      {trade.profit_pct > 0 ? "+" : ""}{trade.profit_pct.toFixed(2)}%
                    </td>
                    <td className="py-2 px-2 text-center">
                      {trade.exit_reason && (
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          EXIT_REASON_CONFIG[trade.exit_reason]?.color || "bg-zinc-100 text-zinc-600"
                        }`}>
                          {EXIT_REASON_CONFIG[trade.exit_reason]?.label || trade.exit_reason}
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-2 text-right text-zinc-500 dark:text-zinc-400">
                      {trade.holding_days}d
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
