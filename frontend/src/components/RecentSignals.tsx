"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface Signal {
  ticker: string;
  market: string;
  pattern: string;
  source: string;
  date: string;
  price: number;
  time: string;
  volume_surge: number | null;
  breakout_pct: number | null;
}

interface SignalsData {
  days: number;
  count: number;
  signals: Signal[];
  error?: string;
}

const PATTERN_COLORS: Record<string, string> = {
  "피벗돌파": "bg-purple-500",
  "컵앤핸들": "bg-blue-500",
  "베이스돌파": "bg-green-500",
  "Pivot Breakout": "bg-orange-500",
};

const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  oneil: { label: "O'Neil", color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300" },
  dynamic: { label: "Dynamic", color: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300" },
};

export default function RecentSignals() {
  const [data, setData] = useState<SignalsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/signals/recent?days=7`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch(() => {
        setData({ days: 7, count: 0, signals: [], error: "Failed to fetch" });
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
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
          Latest Signals
        </h2>
        <span className="text-sm text-zinc-500 dark:text-zinc-400">
          Last 7 days
        </span>
      </div>

      {data?.error && !data.signals.length ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
        </div>
      ) : data?.signals.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 dark:text-zinc-400">
          <p>No signals in the last 7 days</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Date</th>
                <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Ticker</th>
                <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Pattern</th>
                <th className="text-left py-2 px-2 text-zinc-500 dark:text-zinc-400">Source</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Price</th>
                <th className="text-right py-2 px-2 text-zinc-500 dark:text-zinc-400">Vol Surge</th>
              </tr>
            </thead>
            <tbody>
              {data?.signals.map((signal, idx) => (
                <tr
                  key={idx}
                  className="border-b border-zinc-100 dark:border-zinc-700/50 hover:bg-zinc-50 dark:hover:bg-zinc-700/30"
                >
                  <td className="py-2 px-2 text-zinc-600 dark:text-zinc-300">
                    {signal.date}
                  </td>
                  <td className="py-2 px-2 font-semibold text-zinc-900 dark:text-white">
                    {signal.ticker}
                  </td>
                  <td className="py-2 px-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium text-white ${
                        PATTERN_COLORS[signal.pattern] || "bg-zinc-500"
                      }`}
                    >
                      {signal.pattern}
                    </span>
                  </td>
                  <td className="py-2 px-2">
                    <span
                      className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                        SOURCE_CONFIG[signal.source]?.color || "bg-zinc-100 text-zinc-600"
                      }`}
                    >
                      {SOURCE_CONFIG[signal.source]?.label || signal.source}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right text-zinc-600 dark:text-zinc-300">
                    ${signal.price.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-right text-green-600 dark:text-green-400">
                    {signal.volume_surge ? `+${signal.volume_surge.toFixed(0)}%` : "-"}
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
