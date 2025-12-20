"""
Breakout Pattern Detection for O'Neil Style Trading

Detects pivot point breakout signals in US stock data.
"""

import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from screener.dynamic_screener import USStockProvider


class BreakoutDetector:
    """Detects pivot point breakout patterns in US stock data."""

    def __init__(
        self,
        min_volume_surge: float = 50.0,
        max_breakout_pct: float = 5.0
    ):
        """
        Initialize detector with parameters.

        Args:
            min_volume_surge: Minimum volume increase % for valid signal (default 50%)
            max_breakout_pct: Maximum % above resistance for valid signal (default 5%)
        """
        self.min_volume_surge = min_volume_surge
        self.max_breakout_pct = max_breakout_pct

    def detect_pivot_breakout(
        self,
        df: pd.DataFrame,
        ticker: str
    ) -> Optional[Dict]:
        """
        Detect pivot point breakout pattern.

        A valid breakout requires:
        - Price breaks above 20-day high (resistance)
        - Volume surge >= min_volume_surge%
        - Breakout not too extended (within max_breakout_pct%)

        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol

        Returns:
            Signal dictionary or None if no signal
        """
        if df is None or len(df) < 30:
            return None

        try:
            recent = df.tail(30).copy()

            # Volume analysis
            avg_volume = recent['Volume'].iloc[:-1].mean()
            current_volume = recent['Volume'].iloc[-1]
            volume_surge = (current_volume / avg_volume - 1) * 100

            # Price analysis
            close = recent['Close'].values
            current_price = close[-1]
            resistance = np.max(close[-20:-1])  # 20-day high excluding today

            # Breakout conditions
            breakout = current_price > resistance
            breakout_pct = ((current_price - resistance) / resistance) * 100

            if (breakout and
                volume_surge >= self.min_volume_surge and
                0 < breakout_pct <= self.max_breakout_pct):

                signal = {
                    'ticker': ticker,
                    'pattern': 'Pivot Breakout',
                    'resistance': round(resistance, 2),
                    'current_price': round(current_price, 2),
                    'breakout_pct': round(breakout_pct, 2),
                    'volume_surge': round(volume_surge, 2)
                }

                return signal

        except Exception:
            pass

        return None

    def analyze_stock(self, ticker: str) -> List[Dict]:
        """
        Analyze US stock for breakout signals.

        Args:
            ticker: US stock ticker

        Returns:
            List of signals found (empty if none)
        """
        df = USStockProvider.get_stock_data(ticker, period='3mo')
        if df is None:
            return []

        signals = []
        pivot_signal = self.detect_pivot_breakout(df, ticker)
        if pivot_signal:
            signals.append(pivot_signal)

        return signals

    def scan_watchlist(self, tickers: List[str]) -> List[Dict]:
        """
        Scan watchlist for breakout signals.

        Args:
            tickers: List of US tickers

        Returns:
            List of all signals found
        """
        all_signals = []

        if not tickers:
            return all_signals

        print(f"\n🔍 Scanning {len(tickers)} stocks for breakout signals...")
        print("=" * 60)

        for i, ticker in enumerate(tickers):
            try:
                if (i + 1) % 25 == 0:
                    print(f"   Progress: {i + 1}/{len(tickers)} ({len(all_signals)} signals)")

                signals = self.analyze_stock(ticker)
                if signals:
                    all_signals.extend(signals)
                    for s in signals:
                        print(f"   ✅ {s['ticker']}: {s['pattern']} "
                              f"(+{s['breakout_pct']:.1f}%, Vol +{s['volume_surge']:.0f}%)")

            except Exception as e:
                print(f"   ❌ {ticker}: Error - {e}")

            time.sleep(0.3)  # API rate limit

        print("=" * 60)
        print(f"✅ Scan complete: {len(all_signals)} signals found\n")

        return all_signals
