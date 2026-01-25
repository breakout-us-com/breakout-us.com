"use client";
import { API_URL } from "@/lib/config";


import { useEffect, useState } from "react";

interface Signal {
  ticker: string;
  market: string;
  pattern: string;
  source: string;
  price: number;
  time: string;
  volume_surge: number | null;
  breakout_pct: number | null;
  resistance: number | null;
}

interface SignalsData {
  date: string;
  count: number;
  signals: Signal[];
  last_scan: string | null;
  error?: string;
}

const PATTERN_COLORS: Record<string, string> = {
  "피벗돌파": "bg-purple-500",
  "컵앤핸들": "bg-blue-500",
  "베이스돌파": "bg-green-500",
  "Pivot Breakout": "bg-orange-500",
};

function formatLastScan(isoString: string | null): string {
  if (!isoString) return "-";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    return `${diffDays}일 전`;
  } else if (diffHours > 0) {
    return `${diffHours}시간 전`;
  } else if (diffMins > 0) {
    return `${diffMins}분 전`;
  } else {
    return "방금 전";
  }
}

export default function TodaySignals() {
  const [data, setData] = useState<SignalsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/signals/today`)
      .then((res) => res.json())
      .then((data) => {
        setData(data);
        setLoading(false);
      })
      .catch(() => {
        setData({ date: "", count: 0, signals: [], last_scan: null, error: "Failed to fetch" });
        setLoading(false);
      });

    // 5분마다 갱신
    const interval = setInterval(() => {
      fetch(`${API_URL}/api/signals/today`)
        .then((res) => res.json())
        .then((data) => setData(data))
        .catch(() => {});
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-zinc-200 dark:bg-zinc-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-zinc-200 dark:bg-zinc-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-lg shadow p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-0 mb-4">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-zinc-900 dark:text-white">
            Today&apos;s Signals
            {data?.date && (
              <span className="text-sm sm:text-base font-normal text-zinc-500 dark:text-zinc-400 ml-2">
                ({data.date})
              </span>
            )}
          </h2>
          {data && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              최근 스캔: {formatLastScan(data.last_scan)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {data && data.count > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
              </span>
              <span className="text-sm font-medium text-green-600 dark:text-green-400">
                {data.count} new
              </span>
            </span>
          )}
        </div>
      </div>

      {data?.error && !data.signals.length ? (
        <div className="text-center py-8 text-zinc-500 dark:text-zinc-400">
          <p className="text-sm">DB 연결이 필요합니다</p>
          <p className="text-xs mt-1">환경변수에 DB 설정을 추가해주세요</p>
        </div>
      ) : data?.signals.length === 0 ? (
        <div className="py-4">
          <div className="text-center mb-4 text-zinc-500 dark:text-zinc-400">
            <p className="text-lg">No signals yet today</p>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <span className="text-amber-500 mt-0.5">⚠️</span>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">하락장 주의</p>
                <p className="text-xs text-amber-700 dark:text-amber-300">시장이 하락 추세일 때는 신규 진입을 자제하세요. 손절 비율이 높아집니다.</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <span className="text-blue-500 mt-0.5">💡</span>
              <div>
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">O&apos;Neil 원칙</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">돌파 시 거래량이 평균의 50% 이상 급증해야 유효한 시그널입니다.</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <span className="text-green-500 mt-0.5">✅</span>
              <div>
                <p className="text-sm font-medium text-green-800 dark:text-green-200">리스크 관리</p>
                <p className="text-xs text-green-700 dark:text-green-300">한 종목에 포트폴리오의 20% 이상 투자하지 마세요. 손절선(-8%)을 반드시 지키세요.</p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.signals.map((signal, idx) => (
            <div
              key={idx}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-zinc-50 dark:bg-zinc-700/50 rounded-lg border-l-4"
              style={{
                borderLeftColor:
                  signal.pattern === "피벗돌파"
                    ? "#a855f7"
                    : signal.pattern === "컵앤핸들"
                    ? "#3b82f6"
                    : signal.pattern === "Pivot Breakout"
                    ? "#f97316"
                    : "#22c55e",
              }}
            >
              <div className="flex items-start sm:items-center gap-3 sm:gap-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-base sm:text-lg font-bold text-zinc-900 dark:text-white">
                      {signal.ticker}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium text-white ${
                        PATTERN_COLORS[signal.pattern] || "bg-zinc-500"
                      }`}
                    >
                      {signal.pattern}
                    </span>
                  </div>
                  <div className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                    {signal.time && <span>{signal.time} KST</span>}
                    {signal.volume_surge && (
                      <span className="ml-2">
                        Vol +{signal.volume_surge.toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-left sm:text-right mt-2 sm:mt-0">
                <div className="text-base sm:text-lg font-semibold text-zinc-900 dark:text-white">
                  ${signal.price.toFixed(2)}
                </div>
                {signal.breakout_pct && (
                  <div className="text-xs sm:text-sm text-green-600 dark:text-green-400">
                    +{signal.breakout_pct.toFixed(2)}% breakout
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
