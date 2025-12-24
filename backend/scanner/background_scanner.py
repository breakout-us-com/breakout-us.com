"""Background scanner service for breakout detection"""
import asyncio
import os
import time
from datetime import datetime, time as dt_time, timedelta
from typing import List, Dict, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from detector.breakout_detector import BreakoutDetector
from screener.dynamic_screener import DynamicScreener
from routers.watchlist import load_dynamic_watchlist, ONEIL_WATCHLIST
from routers.db import get_db_connection, is_connected
from logging_config import setup_logging

from .market_status import get_market_status, format_market_status_message
from .signal_storage import save_signal, has_alert_today, get_today_signal_count

# Configure logging with file rotation
logger = setup_logging("scanner")

# Configuration from environment
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "1800"))  # 30 min default
SCAN_DELAY_PER_STOCK = float(os.getenv("SCAN_DELAY_PER_STOCK", "0.3"))  # Rate limiting
SCANNER_ENABLED = os.getenv("SCANNER_ENABLED", "true").lower() == "true"

# Dynamic screening schedule (23:30 KST - before US market open)
SCREENING_HOUR = int(os.getenv("SCREENING_HOUR", "23"))
SCREENING_MINUTE = int(os.getenv("SCREENING_MINUTE", "30"))


class BackgroundScanner:
    """Background service for periodic breakout scanning and dynamic screening."""

    def __init__(self):
        self.detector = BreakoutDetector()
        self.screener = DynamicScreener()
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._screening_task: Optional[asyncio.Task] = None
        self._last_scan_time: Optional[datetime] = None
        self._last_scan_results: Dict = {}
        self._last_screening_time: Optional[datetime] = None
        self._last_screening_results: Dict = {}

    def get_watchlist(self) -> List[str]:
        """Get combined watchlist (O'Neil fixed + Dynamic)."""
        # O'Neil fixed watchlist
        oneil_stocks = []
        for stocks in ONEIL_WATCHLIST.values():
            oneil_stocks.extend(stocks)

        # Dynamic watchlist
        try:
            dynamic_data = load_dynamic_watchlist()
            dynamic_stocks = dynamic_data.get("tickers", []) if dynamic_data else []
        except Exception as e:
            logger.warning(f"Could not load dynamic watchlist: {e}")
            dynamic_stocks = []

        # Combine and deduplicate
        all_stocks = list(set(oneil_stocks + dynamic_stocks))
        logger.info(f"Watchlist loaded: {len(all_stocks)} stocks (O'Neil: {len(oneil_stocks)}, Dynamic: {len(dynamic_stocks)})")
        return all_stocks

    def _run_scan(self) -> List[Dict]:
        """Execute a single scan cycle."""
        market_status = get_market_status()
        watchlist = self.get_watchlist()

        logger.info(format_market_status_message(market_status, len(watchlist)))

        if not market_status['is_open']:
            logger.info("Market closed, skipping scan")
            self._last_scan_results = {
                'skipped': True,
                'reason': 'market_closed',
                'time': datetime.now().isoformat()
            }
            return []

        logger.info(f"Starting scan at {market_status['time']}")

        # Ensure DB connection
        if not is_connected():
            conn = get_db_connection()
            if conn is None:
                logger.error("Cannot connect to database, aborting scan")
                self._last_scan_results = {
                    'skipped': True,
                    'reason': 'db_connection_failed',
                    'time': datetime.now().isoformat()
                }
                return []

        tickers = watchlist
        if not tickers:
            logger.warning("No tickers in watchlist")
            return []

        signals_found = []
        scanned = 0
        skipped = 0
        errors = 0

        logger.info(f"Scanning {len(tickers)} stocks...")

        for ticker in tickers:
            try:
                # Check for duplicate before analysis (save API calls)
                if has_alert_today(ticker, "Pivot Breakout"):
                    skipped += 1
                    continue

                signals = self.detector.analyze_stock(ticker)
                scanned += 1

                for signal in signals:
                    # Save to database
                    saved = save_signal(
                        ticker=signal['ticker'],
                        market='US',
                        pattern=signal['pattern'],
                        alert_price=signal['current_price'],
                        signal_data={
                            'resistance': signal.get('resistance'),
                            'breakout_pct': signal.get('breakout_pct'),
                            'volume_surge_pct': signal.get('volume_surge'),
                        },
                        source='background_scanner'
                    )

                    if saved:
                        signals_found.append(signal)
                        logger.info(
                            f"SIGNAL: {signal['ticker']} - {signal['pattern']} "
                            f"@ ${signal['current_price']:.2f} "
                            f"(+{signal['breakout_pct']:.1f}%, Vol +{signal['volume_surge']:.0f}%)"
                        )

                # Rate limiting
                time.sleep(SCAN_DELAY_PER_STOCK)

            except Exception as e:
                errors += 1
                logger.error(f"Error scanning {ticker}: {e}")

        self._last_scan_time = datetime.now()
        self._last_scan_results = {
            'scanned': scanned,
            'skipped': skipped,
            'signals': len(signals_found),
            'errors': errors,
            'time': self._last_scan_time.isoformat(),
            'today_total': get_today_signal_count()
        }

        logger.info(
            f"Scan complete: {scanned} scanned, {skipped} skipped, "
            f"{len(signals_found)} signals found, {errors} errors"
        )

        return signals_found

    async def _scan_loop(self):
        """Main async loop for periodic scanning."""
        logger.info(f"Background scanner loop started (interval: {SCAN_INTERVAL_SECONDS}s)")

        while self._running:
            try:
                # Run scan in thread pool to not block event loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._run_scan)

            except Exception as e:
                logger.error(f"Scan loop error: {e}")

            # Wait for next scan
            logger.info(f"Next scan in {SCAN_INTERVAL_SECONDS // 60} minutes...")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

    def _run_screening(self) -> List[str]:
        """Execute dynamic stock screening."""
        logger.info("Starting dynamic stock screening...")

        try:
            tickers = self.screener.run_and_save(max_stocks=100)

            self._last_screening_time = datetime.now()
            self._last_screening_results = {
                'stocks_selected': len(tickers),
                'time': self._last_screening_time.isoformat(),
                'status': 'success'
            }

            logger.info(f"Dynamic screening complete: {len(tickers)} stocks selected")
            return tickers

        except Exception as e:
            logger.error(f"Dynamic screening error: {e}")
            self._last_screening_results = {
                'stocks_selected': 0,
                'time': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
            return []

    async def _screening_loop(self):
        """Loop that runs dynamic screening at scheduled time (23:30 KST)."""
        logger.info(f"Dynamic screening scheduler started (scheduled: {SCREENING_HOUR:02d}:{SCREENING_MINUTE:02d} KST)")

        while self._running:
            try:
                now = datetime.now()
                target_time = now.replace(
                    hour=SCREENING_HOUR,
                    minute=SCREENING_MINUTE,
                    second=0,
                    microsecond=0
                )

                # If target time has passed today, schedule for tomorrow
                if now >= target_time:
                    target_time = target_time + timedelta(days=1)

                # Calculate seconds until target time
                wait_seconds = (target_time - now).total_seconds()

                # Cap at 24 hours max (in case of date calculation issues)
                wait_seconds = min(wait_seconds, 86400)

                logger.info(
                    f"Next dynamic screening at {target_time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"(in {wait_seconds / 3600:.1f} hours)"
                )

                await asyncio.sleep(wait_seconds)

                # Run screening
                if self._running:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._run_screening)

            except Exception as e:
                logger.error(f"Screening loop error: {e}")
                # Wait 1 hour before retry on error
                await asyncio.sleep(3600)

    async def start(self):
        """Start the background scanner and screening scheduler."""
        if not SCANNER_ENABLED:
            logger.info("Background scanner is disabled (SCANNER_ENABLED=false)")
            return

        if self._running:
            logger.warning("Scanner already running")
            return

        self._running = True

        # Start breakout scan loop
        self._scan_task = asyncio.create_task(self._scan_loop())

        # Start dynamic screening scheduler
        self._screening_task = asyncio.create_task(self._screening_loop())

        logger.info("Background scanner and screening scheduler started")

    async def stop(self):
        """Stop the background scanner and screening scheduler."""
        if not self._running:
            return

        self._running = False

        # Cancel scan task
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

        # Cancel screening task
        if self._screening_task:
            self._screening_task.cancel()
            try:
                await self._screening_task
            except asyncio.CancelledError:
                pass

        logger.info("Background scanner and screening scheduler stopped")

    def get_status(self) -> Dict:
        """Get scanner status for health checks."""
        return {
            'running': self._running,
            'enabled': SCANNER_ENABLED,
            'scan': {
                'last_time': self._last_scan_time.isoformat() if self._last_scan_time else None,
                'last_results': self._last_scan_results,
                'interval_seconds': SCAN_INTERVAL_SECONDS,
            },
            'screening': {
                'schedule': f"{SCREENING_HOUR:02d}:{SCREENING_MINUTE:02d} KST",
                'last_time': self._last_screening_time.isoformat() if self._last_screening_time else None,
                'last_results': self._last_screening_results,
            },
            'market_status': get_market_status(),
        }


# Global scanner instance
_scanner: Optional[BackgroundScanner] = None


def get_scanner() -> BackgroundScanner:
    """Get or create scanner instance."""
    global _scanner
    if _scanner is None:
        _scanner = BackgroundScanner()
    return _scanner
