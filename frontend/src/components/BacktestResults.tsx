"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface TradeResult {
  ticker: string;
  market: string;
  pattern: string;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  shares: number;
  cost: number;
  proceeds: number;
  profit: number;
  profit_pct: number;
  holding_days: number;
  reason: string;
}

interface ResultsData {
  total: number;
  results: TradeResult[];
}

const PATTERN_COLORS: Record<string, string> = {
  "컵앤핸들": "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
  "피벗돌파": "bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300",
  "베이스돌파": "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
};

const REASON_LABELS: Record<string, { label: string; color: string }> = {
  "익절": { label: "Take Profit", color: "text-green-600 dark:text-green-400" },
  "손절": { label: "Stop Loss", color: "text-red-600 dark:text-red-400" },
  "보유기간만료": { label: "Expired", color: "text-yellow-600 dark:text-yellow-400" },
  "백테스트종료": { label: "Backtest End", color: "text-zinc-500 dark:text-zinc-400" },
};

export default function BacktestResults() {
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patternFilter, setPatternFilter] = useState<string>("");

  useEffect(() => {
    const url = patternFilter
      ? `${API_URL}/api/backtest/results?pattern=${encodeURIComponent(patternFilter)}`
      : `${API_URL}/api/backtest/results`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [patternFilter]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
          Trade History
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-500 dark:text-zinc-400">Filter:</span>
          <select
            value={patternFilter}
            onChange={(e) => setPatternFilter(e.target.value)}
            className="bg-zinc-100 dark:bg-zinc-700 border-0 rounded-md px-3 py-1.5 text-sm text-zinc-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Patterns</option>
            <option value="컵앤핸들">Cup & Handle</option>
            <option value="피벗돌파">Pivot Breakout</option>
            <option value="베이스돌파">Base Breakout</option>
          </select>
          <span className="text-sm bg-zinc-100 dark:bg-zinc-700 px-3 py-1 rounded-full text-zinc-600 dark:text-zinc-300">
            {data?.total} trades
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="text-left py-3 px-3 text-zinc-500 dark:text-zinc-400">Ticker</th>
              <th className="text-left py-3 px-3 text-zinc-500 dark:text-zinc-400">Pattern</th>
              <th className="text-left py-3 px-3 text-zinc-500 dark:text-zinc-400">Entry</th>
              <th className="text-left py-3 px-3 text-zinc-500 dark:text-zinc-400">Exit</th>
              <th className="text-right py-3 px-3 text-zinc-500 dark:text-zinc-400">Profit %</th>
              <th className="text-right py-3 px-3 text-zinc-500 dark:text-zinc-400">Days</th>
              <th className="text-left py-3 px-3 text-zinc-500 dark:text-zinc-400">Reason</th>
            </tr>
          </thead>
          <tbody>
            {data?.results.map((trade, idx) => (
              <tr
                key={idx}
                className="border-b border-zinc-100 dark:border-zinc-700/50 hover:bg-zinc-50 dark:hover:bg-zinc-700/30"
              >
                <td className="py-3 px-3 font-semibold text-zinc-900 dark:text-white">
                  {trade.ticker}
                </td>
                <td className="py-3 px-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      PATTERN_COLORS[trade.pattern] || "bg-zinc-100 text-zinc-800"
                    }`}
                  >
                    {trade.pattern}
                  </span>
                </td>
                <td className="py-3 px-3 text-zinc-600 dark:text-zinc-300">
                  <div>{trade.entry_date}</div>
                  <div className="text-xs text-zinc-400">${trade.entry_price.toFixed(2)}</div>
                </td>
                <td className="py-3 px-3 text-zinc-600 dark:text-zinc-300">
                  <div>{trade.exit_date}</div>
                  <div className="text-xs text-zinc-400">${trade.exit_price.toFixed(2)}</div>
                </td>
                <td className="py-3 px-3 text-right">
                  <span
                    className={`font-semibold ${
                      trade.profit_pct >= 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {trade.profit_pct >= 0 ? "+" : ""}
                    {trade.profit_pct.toFixed(2)}%
                  </span>
                </td>
                <td className="py-3 px-3 text-right text-zinc-600 dark:text-zinc-300">
                  {trade.holding_days}
                </td>
                <td className="py-3 px-3">
                  <span className={REASON_LABELS[trade.reason]?.color || "text-zinc-500"}>
                    {REASON_LABELS[trade.reason]?.label || trade.reason}
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
