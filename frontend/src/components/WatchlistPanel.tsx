"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface FixedData {
  total: number;
  by_sector: Record<string, string[]>;
  all: string[];
  source: string;
  label: string;
  description: string;
}

interface DynamicData {
  total: number;
  all: string[];
  source: string;
  label: string;
  description: string;
  updated_at: string | null;
}

interface WatchlistData {
  fixed: FixedData;
  dynamic: DynamicData;
  total: number;
}

const SECTOR_COLORS: Record<string, { bg: string; text: string; badge: string }> = {
  Tech: { bg: "bg-blue-50 dark:bg-blue-900/20", text: "text-blue-700 dark:text-blue-300", badge: "bg-blue-200 dark:bg-blue-800" },
  Communication: { bg: "bg-purple-50 dark:bg-purple-900/20", text: "text-purple-700 dark:text-purple-300", badge: "bg-purple-200 dark:bg-purple-800" },
  Consumer: { bg: "bg-green-50 dark:bg-green-900/20", text: "text-green-700 dark:text-green-300", badge: "bg-green-200 dark:bg-green-800" },
  Financial: { bg: "bg-yellow-50 dark:bg-yellow-900/20", text: "text-yellow-700 dark:text-yellow-300", badge: "bg-yellow-200 dark:bg-yellow-800" },
  Healthcare: { bg: "bg-pink-50 dark:bg-pink-900/20", text: "text-pink-700 dark:text-pink-300", badge: "bg-pink-200 dark:bg-pink-800" },
  Energy: { bg: "bg-orange-50 dark:bg-orange-900/20", text: "text-orange-700 dark:text-orange-300", badge: "bg-orange-200 dark:bg-orange-800" },
  Industrial: { bg: "bg-slate-50 dark:bg-slate-900/20", text: "text-slate-700 dark:text-slate-300", badge: "bg-slate-200 dark:bg-slate-800" },
};

type TabType = "fixed" | "dynamic";

export default function WatchlistPanel() {
  const [data, setData] = useState<WatchlistData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("fixed");

  useEffect(() => {
    fetch(`${API_URL}/api/watchlist`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4">
        <div className="animate-pulse flex items-center gap-4">
          <div className="h-5 bg-zinc-200 dark:bg-zinc-700 rounded w-32"></div>
          <div className="h-5 bg-zinc-200 dark:bg-zinc-700 rounded w-48"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4">
        <p className="text-red-500 text-sm">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4">
      {/* Header with Tabs inline */}
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <h2 className="text-lg font-bold text-zinc-900 dark:text-white">
          Monitoring Stocks
        </h2>
        <span className="text-xs bg-zinc-100 dark:bg-zinc-700 px-2 py-0.5 rounded-full text-zinc-600 dark:text-zinc-300">
          {data?.total} total
        </span>
        <div className="flex gap-1.5 ml-auto">
          <button
            onClick={() => setActiveTab("fixed")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
              activeTab === "fixed"
                ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-600"
            }`}
          >
            고정 ({data?.fixed.total})
          </button>
          <button
            onClick={() => setActiveTab("dynamic")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
              activeTab === "dynamic"
                ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-600"
            }`}
          >
            동적 ({data?.dynamic.total})
          </button>
        </div>
      </div>

      {/* Fixed Tab Content - Sectors in horizontal flow */}
      {activeTab === "fixed" && data?.fixed && (
        <div className="flex flex-wrap gap-2">
          {data.fixed.by_sector &&
            Object.entries(data.fixed.by_sector).map(([sector, stocks]) => {
              const colors = SECTOR_COLORS[sector] || { bg: "bg-zinc-50 dark:bg-zinc-700", text: "text-zinc-700 dark:text-zinc-300", badge: "bg-zinc-200 dark:bg-zinc-600" };
              return (
                <div
                  key={sector}
                  className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg ${colors.bg}`}
                >
                  <span className={`text-xs font-semibold ${colors.text}`}>{sector}</span>
                  <div className="flex gap-1">
                    {stocks.map((stock) => (
                      <span
                        key={stock}
                        className={`px-1.5 py-0.5 text-xs font-medium rounded ${colors.badge} ${colors.text}`}
                      >
                        {stock}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {/* Dynamic Tab Content */}
      {activeTab === "dynamic" && data?.dynamic && (
        <div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">
            S&P 500 + NASDAQ 100 중 시총 $500M↑, 거래량 50K↑, 주가 $5↑
          </p>
          <div className="max-h-24 overflow-y-auto">
            <div className="flex flex-wrap gap-1">
              {data.dynamic.all.map((stock) => (
                <span
                  key={stock}
                  className="px-1.5 py-0.5 text-xs font-medium rounded bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                >
                  {stock}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
