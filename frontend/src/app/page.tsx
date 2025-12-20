import WatchlistPanel from "@/components/WatchlistPanel";
import PerformanceStats from "@/components/PerformanceStats";
import BacktestResults from "@/components/BacktestResults";
import MarketStatus from "@/components/MarketStatus";
import TodaySignals from "@/components/TodaySignals";
import RecentSignals from "@/components/RecentSignals";
import CurrentPositions from "@/components/CurrentPositions";
import MonthlyPerformance from "@/components/MonthlyPerformance";
import PaperTradingStats from "@/components/PaperTradingStats";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      {/* Header */}
      <header className="bg-white dark:bg-zinc-800 shadow-sm border-b border-zinc-200 dark:border-zinc-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
                O&apos;Neil Breakout
              </h1>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                US Stock Trading Signals & Paper Trading
              </p>
            </div>
            <MarketStatus />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Row 1: Monitoring Stocks */}
        <div className="mb-6">
          <WatchlistPanel />
        </div>

        {/* Row 2: Today's Signals + Latest Signals (side by side) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <TodaySignals />
          <RecentSignals />
        </div>

        {/* Row 3: Open Positions */}
        <div className="mb-6">
          <CurrentPositions />
        </div>

        {/* Row 4: Paper Trading Stats (one row) */}
        <div className="mb-6">
          <PaperTradingStats />
        </div>

        {/* Row 5: Monthly Performance */}
        <div className="mb-6">
          <MonthlyPerformance />
        </div>

        {/* Row 6: Backtest Results (Historical Reference) */}
        <details className="mb-8">
          <summary className="cursor-pointer text-lg font-semibold text-zinc-700 dark:text-zinc-300 mb-4 hover:text-zinc-900 dark:hover:text-white">
            Backtest Results (Historical Reference)
          </summary>
          <div className="mt-4">
            <PerformanceStats />
            <div className="mt-6">
              <BacktestResults />
            </div>
          </div>
        </details>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-zinc-800 border-t border-zinc-200 dark:border-zinc-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              O&apos;Neil Breakout Strategy - CAN SLIM Methodology
            </p>
            <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
              <span>Stop Loss: -8%</span>
              <span>Take Profit: +20%</span>
              <span>Max Hold: 30 days</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-700 text-xs text-zinc-400 dark:text-zinc-500 text-center">
            <p>
              본 사이트는 Google AdSense를 사용하며, 광고 목적으로 쿠키가 수집될 수 있습니다.{" "}
              <a
                href="https://adssettings.google.com"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-zinc-600 dark:hover:text-zinc-300"
              >
                광고 개인화 거부
              </a>
            </p>
            <p className="mt-1">
              투자 시그널은 참고용이며, 투자 손실에 대한 책임은 본인에게 있습니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
