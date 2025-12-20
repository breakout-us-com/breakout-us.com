"use client";

import { useEffect, useState } from "react";

type MarketSession = "closed" | "premarket" | "regular" | "afterhours" | "daymarket";

interface SessionConfig {
  label: string;
  labelKo: string;
  color: string;
  bgColor: string;
  dotColor: string;
  timeKST: string;
}

const SESSION_CONFIG: Record<MarketSession, SessionConfig> = {
  daymarket: {
    label: "Day Market",
    labelKo: "데이마켓",
    color: "text-orange-600 dark:text-orange-400",
    bgColor: "bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800",
    dotColor: "bg-orange-500",
    timeKST: "10:00-17:50",
  },
  premarket: {
    label: "Pre-Market",
    labelKo: "프리마켓",
    color: "text-blue-600 dark:text-blue-400",
    bgColor: "bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800",
    dotColor: "bg-blue-500",
    timeKST: "18:00-23:30",
  },
  regular: {
    label: "Regular",
    labelKo: "정규장",
    color: "text-green-600 dark:text-green-400",
    bgColor: "bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800",
    dotColor: "bg-green-500",
    timeKST: "23:30-06:00",
  },
  afterhours: {
    label: "After-Hours",
    labelKo: "애프터마켓",
    color: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800",
    dotColor: "bg-purple-500",
    timeKST: "06:00-09:50",
  },
  closed: {
    label: "Closed",
    labelKo: "휴장",
    color: "text-zinc-500 dark:text-zinc-400",
    bgColor: "bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700",
    dotColor: "bg-zinc-400",
    timeKST: "-",
  },
};

export default function MarketStatus() {
  const [currentSession, setCurrentSession] = useState<MarketSession>("closed");
  const [etTime, setEtTime] = useState("");
  const [kstTime, setKstTime] = useState("");

  useEffect(() => {
    const checkMarketStatus = () => {
      const now = new Date();

      // KST 시간 계산
      const kstFormatter = new Intl.DateTimeFormat("ko-KR", {
        timeZone: "Asia/Seoul",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        weekday: "short",
      });
      const kstParts = kstFormatter.formatToParts(now);
      const kstHour = parseInt(kstParts.find(p => p.type === "hour")?.value || "0");
      const kstMinute = parseInt(kstParts.find(p => p.type === "minute")?.value || "0");
      const kstDay = kstParts.find(p => p.type === "weekday")?.value || "";

      // ET 시간 계산
      const etFormatter = new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
      const etParts = etFormatter.formatToParts(now);
      const etHour = parseInt(etParts.find(p => p.type === "hour")?.value || "0");
      const etMinute = parseInt(etParts.find(p => p.type === "minute")?.value || "0");

      const kstTimeNum = kstHour * 100 + kstMinute;

      // 주말 체크 (KST 기준 토요일 10:00 이후 ~ 월요일 10:00 이전은 휴장)
      const isWeekend = kstDay === "토" || kstDay === "일";

      let session: MarketSession = "closed";
      if (!isWeekend) {
        // KST 기준 시간대
        // 데이마켓: 10:00-17:50
        // 프리마켓: 18:00-23:30
        // 정규장: 23:30-06:00 (다음날)
        // 애프터마켓: 06:00-09:50
        if (kstTimeNum >= 1000 && kstTimeNum < 1750) {
          session = "daymarket";
        } else if (kstTimeNum >= 1800 && kstTimeNum < 2330) {
          session = "premarket";
        } else if (kstTimeNum >= 2330 || kstTimeNum < 600) {
          session = "regular";
        } else if (kstTimeNum >= 600 && kstTimeNum < 950) {
          session = "afterhours";
        }
      }

      setCurrentSession(session);
      setEtTime(`${etHour.toString().padStart(2, "0")}:${etMinute.toString().padStart(2, "0")}`);
      setKstTime(`${kstHour.toString().padStart(2, "0")}:${kstMinute.toString().padStart(2, "0")}`);
    };

    checkMarketStatus();
    const interval = setInterval(checkMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const sessions: MarketSession[] = ["daymarket", "premarket", "regular", "afterhours"];

  return (
    <div className="flex items-center gap-2">
      {/* 현재 시간 */}
      <div className="text-sm text-zinc-500 dark:text-zinc-400 mr-2">
        <span className="font-medium">{etTime}</span>
        <span className="text-xs ml-1">미국 동부</span>
        <span className="mx-1">·</span>
        <span className="font-medium">{kstTime}</span>
        <span className="text-xs ml-1">한국</span>
      </div>

      {/* 세션 표시 */}
      <div className="flex items-center gap-1">
        {sessions.map((session) => {
          const config = SESSION_CONFIG[session];
          const isActive = currentSession === session;

          return (
            <div
              key={session}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs border transition-all ${
                isActive
                  ? config.bgColor
                  : "bg-transparent border-transparent opacity-50"
              }`}
              title={`${config.label}: ${config.timeKST} KST`}
            >
              <div
                className={`w-1.5 h-1.5 rounded-full ${config.dotColor} ${
                  isActive ? "animate-pulse" : ""
                }`}
              />
              <span className={isActive ? config.color : "text-zinc-400 dark:text-zinc-500"}>
                {config.labelKo}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
