"""
Dynamic Stock Screener for US Market

Screens US stocks based on market cap, volume, price criteria.
"""

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yfinance as yf

# Suppress yfinance error messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)


@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr output."""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


class USStockProvider:
    """Provider for US stock market data."""

    # S&P 500 major tickers
    SP500_TICKERS = [
        # Tech
        "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "ORCL",
        "CRM", "AMD", "ADBE", "CSCO", "ACN", "IBM", "INTC", "TXN", "QCOM", "AMAT",
        "INTU", "MU", "ADI", "LRCX", "KLAC", "SNPS", "CDNS", "MCHP", "FTNT", "PANW",
        # Finance
        "JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "SCHW", "AXP", "SPGI",
        "BX", "CB", "PGR", "MMC", "ICE", "CME", "AON", "MCO", "TFC", "USB",
        # Healthcare
        "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "BMY",
        "AMGN", "CVS", "ELV", "MDT", "GILD", "CI", "REGN", "ISRG", "VRTX", "ZTS",
        # Consumer
        "WMT", "HD", "MCD", "COST", "NKE", "SBUX", "TJX", "LOW", "TGT", "DG",
        "BKNG", "ABNB", "MAR", "CMG", "YUM", "ORLY", "AZO", "ROST", "EBAY", "ETSY",
        # Industrial
        "GE", "CAT", "HON", "UNP", "RTX", "BA", "LMT", "DE", "UPS", "MMM",
        "GD", "NOC", "FDX", "NSC", "CSX", "EMR", "ETN", "PH", "ITW", "CARR",
        # Energy
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
        # Communication/Media
        "TMUS", "T", "VZ", "NFLX", "DIS", "CMCSA", "CHTR", "PARA", "WBD", "FOXA",
        # Other
        "BRK-B", "V", "MA", "PM", "PG", "KO", "PEP", "MO", "CL", "MDLZ"
    ]

    # NASDAQ 100 major tickers
    NASDAQ100_TICKERS = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "COST",
        "NFLX", "AMD", "PEP", "ADBE", "CSCO", "TMUS", "CMCSA", "INTC", "INTU", "TXN",
        "QCOM", "AMGN", "HON", "SBUX", "AMAT", "BKNG", "ISRG", "GILD", "ADI", "VRTX",
        "ADP", "REGN", "MDLZ", "PANW", "MU", "LRCX", "PYPL", "SNPS", "KLAC", "CDNS",
        "MELI", "CRWD", "ABNB", "MAR", "FTNT", "ORLY", "CSX", "MRVL", "DASH", "ADSK",
        "NXPI", "WDAY", "AZN", "CPRT", "MNST", "PCAR", "ROP", "PAYX", "ROST", "FAST",
        "ODFL", "AEP", "BKR", "EA", "CTSH", "XEL", "DXCM", "VRSK", "GEHC", "EXC",
        "CTAS", "CHTR", "IDXX", "KDP", "MCHP", "KHC", "CCEP", "TTWO", "FANG", "ZS",
        "DDOG", "ANSS", "TTD", "ON", "CDW", "BIIB", "GFS", "ILMN", "WBD", "MDB",
        "MRNA", "WBA", "TEAM", "ALGN", "ZM", "LCID", "RIVN"
    ]

    @classmethod
    def get_universe(cls) -> List[str]:
        """Get combined US stock universe (S&P 500 + NASDAQ 100)."""
        return list(set(cls.SP500_TICKERS + cls.NASDAQ100_TICKERS))

    @staticmethod
    def get_stock_data(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
        """Fetch stock data from yfinance."""
        try:
            with suppress_stderr():
                stock = yf.Ticker(ticker)
                df = stock.history(period=period)
            if df.empty:
                return None
            return df
        except Exception:
            return None

    @staticmethod
    def get_stock_info(ticker: str) -> Optional[dict]:
        """Get stock info including market cap."""
        try:
            with suppress_stderr():
                stock = yf.Ticker(ticker)
                return stock.info
        except Exception:
            return None


class DynamicScreener:
    """Dynamic stock screener that finds US stocks meeting O'Neil criteria."""

    def __init__(
        self,
        min_market_cap_usd: int = 500_000_000,
        min_avg_volume: int = 50_000,
        min_price_usd: float = 5.0,
        output_path: str = None
    ):
        """
        Initialize screener with filtering criteria.

        Args:
            min_market_cap_usd: Minimum market cap in USD ($500M default)
            min_avg_volume: Minimum average volume (50K default)
            min_price_usd: Minimum stock price in USD ($5 default)
            output_path: Path to save watchlist.json
        """
        self.min_market_cap_usd = min_market_cap_usd
        self.min_avg_volume = min_avg_volume
        self.min_price_usd = min_price_usd
        self.output_path = output_path or os.getenv(
            "DYNAMIC_WATCHLIST_PATH",
            "/var/www/breakout-us.com/watchlist.json"
        )

    def screen_stocks(
        self,
        tickers: List[str] = None,
        max_stocks: int = 100
    ) -> List[str]:
        """
        Screen US stocks based on criteria.

        Args:
            tickers: List of tickers to screen (defaults to full universe)
            max_stocks: Maximum number of stocks to return

        Returns:
            List of qualified ticker symbols
        """
        if tickers is None:
            tickers = USStockProvider.get_universe()

        qualified = []
        print(f"\n🔍 US Stock Screening ({len(tickers)} candidates, max {max_stocks})")
        print("=" * 60)

        for i, ticker in enumerate(tickers):
            if len(qualified) >= max_stocks:
                break

            try:
                if (i + 1) % 50 == 0:
                    print(f"Progress: {i + 1}/{len(tickers)} ({len(qualified)} passed)")

                info = USStockProvider.get_stock_info(ticker)
                if not info:
                    continue

                # Check market cap
                market_cap = info.get('marketCap', 0)
                if market_cap < self.min_market_cap_usd:
                    continue

                # Check price
                current_price = info.get('currentPrice', 0)
                if current_price < self.min_price_usd:
                    continue

                # Get historical data for volume check
                df = USStockProvider.get_stock_data(ticker, period='3mo')
                if df is None or len(df) < 20:
                    continue

                recent = df.tail(30)

                # Check average volume
                avg_volume = recent['Volume'].mean()
                if avg_volume < self.min_avg_volume:
                    continue

                qualified.append({
                    'ticker': ticker,
                    'market_cap': market_cap,
                    'price': current_price,
                    'avg_volume': int(avg_volume),
                })

            except Exception:
                continue

            time.sleep(0.1)  # API rate limit

        # Sort by market cap
        qualified.sort(key=lambda x: x['market_cap'], reverse=True)

        print(f"\n✅ Screening complete: {len(qualified)} stocks selected")
        print("=" * 60)

        return [s['ticker'] for s in qualified]

    def run_and_save(self, max_stocks: int = 100) -> List[str]:
        """
        Run screening and save results to watchlist.json.

        Args:
            max_stocks: Maximum stocks to select

        Returns:
            List of qualified ticker symbols
        """
        print("\n" + "=" * 60)
        print("🌍 Dynamic Stock Screening (US)")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        tickers = self.screen_stocks(max_stocks=max_stocks)

        # Save to watchlist.json
        output = {
            "tickers": tickers,
            "updated_at": datetime.now().isoformat(),
            "screening_mode": "dynamic",
            "criteria": {
                "min_market_cap_usd": self.min_market_cap_usd,
                "min_avg_volume": self.min_avg_volume,
                "min_price_usd": self.min_price_usd
            }
        }

        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n💾 Saved to: {output_path}")
        print(f"   🇺🇸 US: {len(tickers)} stocks")
        print("=" * 60 + "\n")

        return tickers


if __name__ == "__main__":
    screener = DynamicScreener()
    screener.run_and_save(max_stocks=100)
