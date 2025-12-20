#!/usr/bin/env python3
"""
Breakout Signal Scanner

Scans watchlist for breakout signals and saves to database.

Usage:
    python scripts/run_scanner.py [--source dynamic|fixed]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from detector import BreakoutDetector
from routers.db import get_cursor
from routers.watchlist import FIXED_WATCHLIST


def load_dynamic_watchlist() -> list:
    """Load tickers from dynamic watchlist.json."""
    watchlist_path = Path(
        os.getenv(
            "DYNAMIC_WATCHLIST_PATH",
            "/var/www/breakout-us.com/watchlist.json"
        )
    )

    if not watchlist_path.exists():
        print(f"⚠️  Dynamic watchlist not found: {watchlist_path}")
        return []

    try:
        with open(watchlist_path, 'r') as f:
            data = json.load(f)
        return data.get('tickers', [])
    except Exception as e:
        print(f"❌ Failed to load dynamic watchlist: {e}")
        return []


def save_alert_to_db(signal: dict, source: str) -> bool:
    """
    Save breakout signal to alerts table.

    Args:
        signal: Signal dictionary with ticker, pattern, price, etc.
        source: Signal source ('fixed' or 'dynamic')

    Returns:
        True if saved successfully
    """
    with get_cursor() as cursor:
        if cursor is None:
            print("❌ Database not connected")
            return False

        try:
            cursor.execute("""
                INSERT INTO alerts (ticker, market, pattern, source, alert_price, signal_data)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, pattern, source, alert_date) DO UPDATE SET
                    alert_price = EXCLUDED.alert_price,
                    signal_data = EXCLUDED.signal_data,
                    sent_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                signal['ticker'],
                "US",
                signal['pattern'],
                source,
                signal['current_price'],
                json.dumps({
                    'volume_surge_pct': signal.get('volume_surge'),
                    'breakout_pct': signal.get('breakout_pct'),
                    'resistance': signal.get('resistance'),
                })
            ))
            cursor.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Failed to save alert: {e}")
            return False


def has_open_position(ticker: str) -> bool:
    """Check if there's already an open position for the ticker."""
    with get_cursor() as cursor:
        if cursor is None:
            return False

        try:
            cursor.execute(
                "SELECT 1 FROM positions WHERE ticker = %s AND status = 'open'",
                (ticker,)
            )
            return cursor.fetchone() is not None
        except Exception:
            return False


def get_available_capital() -> float:
    """Calculate available capital for new positions."""
    initial_capital = float(os.getenv('INITIAL_CAPITAL', '100000'))
    position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '0.20'))
    max_positions = int(os.getenv('MAX_POSITIONS', '5'))

    with get_cursor() as cursor:
        if cursor is None:
            return 0

        try:
            # Get total invested in open positions
            cursor.execute("""
                SELECT
                    COUNT(*) as position_count,
                    COALESCE(SUM(investment_amount), 0) as total_invested
                FROM positions
                WHERE status = 'open'
            """)
            result = cursor.fetchone()
            position_count = result['position_count'] or 0
            total_invested = float(result['total_invested'] or 0)

            # Check max positions limit
            if position_count >= max_positions:
                return 0

            # Calculate available capital
            available = initial_capital - total_invested
            position_size = initial_capital * position_size_pct

            return min(available, position_size)

        except Exception:
            return 0


def save_position_to_db(signal: dict, source: str) -> bool:
    """
    Save position to positions table for Paper Trading.

    Args:
        signal: Signal dictionary with ticker, pattern, price, etc.
        source: Signal source ('fixed' or 'dynamic')

    Returns:
        True if saved successfully
    """
    # Skip if already has open position
    if has_open_position(signal['ticker']):
        print(f"   ⏭️  Position exists: {signal['ticker']}")
        return False

    # Check available capital
    available_capital = get_available_capital()
    if available_capital <= 0:
        print(f"   ⏭️  No capital available: {signal['ticker']}")
        return False

    with get_cursor() as cursor:
        if cursor is None:
            print("❌ Database not connected")
            return False

        try:
            entry_price = signal['current_price']
            stop_loss_pct = float(os.getenv('STOP_LOSS_PCT', '0.08'))
            take_profit_pct = float(os.getenv('TAKE_PROFIT_PCT', '0.20'))

            # Calculate position size
            investment_amount = available_capital
            quantity = investment_amount / entry_price

            cursor.execute("""
                INSERT INTO positions (
                    ticker, market, source, entry_price, quantity, investment_amount,
                    pattern, stop_loss, take_profit, signal_data, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'open')
                RETURNING id
            """, (
                signal['ticker'],
                "US",
                source,
                entry_price,
                round(quantity, 4),
                round(investment_amount, 2),
                signal['pattern'],
                round(entry_price * (1 - stop_loss_pct), 4),
                round(entry_price * (1 + take_profit_pct), 4),
                json.dumps({
                    'volume_surge_pct': signal.get('volume_surge'),
                    'breakout_pct': signal.get('breakout_pct'),
                    'resistance': signal.get('resistance'),
                })
            ))
            cursor.connection.commit()
            print(f"   💰 Invested ${investment_amount:,.0f} ({quantity:.2f} shares)")
            return True
        except Exception as e:
            print(f"❌ Failed to save position: {e}")
            return False


def run_scan(source: str = "dynamic"):
    """
    Run breakout signal scan.

    Args:
        source: 'fixed' for FIXED_WATCHLIST, 'dynamic' for watchlist.json
    """
    print("\n" + "=" * 60)
    print(f"🚀 Breakout Signal Scanner")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Source: {source}")
    print("=" * 60)

    # Load tickers
    if source == "fixed":
        tickers = FIXED_WATCHLIST
    else:
        tickers = load_dynamic_watchlist()

    if not tickers:
        print("❌ No tickers to scan")
        return

    print(f"\n📊 Loaded {len(tickers)} tickers")

    # Initialize detector
    detector = BreakoutDetector(
        min_volume_surge=float(os.getenv('MIN_VOLUME_SURGE', '50.0')),
        max_breakout_pct=float(os.getenv('MAX_BREAKOUT_PCT', '5.0'))
    )

    # Scan for signals
    signals = detector.scan_watchlist(tickers)

    # Save signals to database
    if signals:
        print(f"\n💾 Saving {len(signals)} signals to database...")
        alert_count = 0
        position_count = 0

        for signal in signals:
            # 1. Save to alerts table (시그널 기록)
            if save_alert_to_db(signal, source):
                alert_count += 1
                print(f"   ✅ Alert: {signal['ticker']}")
            else:
                print(f"   ❌ Alert failed: {signal['ticker']}")

            # 2. Save to positions table (Paper Trading)
            if save_position_to_db(signal, source):
                position_count += 1
                print(f"   📈 Position opened: {signal['ticker']}")

        print(f"\n📊 Summary:")
        print(f"   - Alerts saved: {alert_count}/{len(signals)}")
        print(f"   - Positions opened: {position_count}/{len(signals)}")
    else:
        print("\n⚪ No breakout signals found")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Breakout Signal Scanner")
    parser.add_argument(
        "--source",
        type=str,
        default="dynamic",
        choices=["fixed", "dynamic"],
        help="Watchlist source (fixed or dynamic)"
    )
    args = parser.parse_args()

    run_scan(source=args.source)


if __name__ == "__main__":
    main()
