#!/usr/bin/env python3
"""
Position Manager - Check and close positions based on exit conditions.

Checks open positions for:
- Stop Loss (-8%)
- Take Profit (+20%)
- Max Holding Period (30 days)

Usage:
    python scripts/run_position_manager.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers.db import get_cursor
from screener.dynamic_screener import USStockProvider


def get_open_positions() -> list:
    """Get all open positions from database."""
    with get_cursor() as cursor:
        if cursor is None:
            return []

        try:
            cursor.execute("""
                SELECT id, ticker, market, source, entry_price, entry_date,
                       pattern, stop_loss, take_profit, signal_data
                FROM positions
                WHERE status = 'open'
                ORDER BY entry_date
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Failed to get positions: {e}")
            return []


def close_position(
    position_id: int,
    exit_price: float,
    exit_reason: str,
    profit_pct: float,
    holding_days: int
) -> bool:
    """Close a position with exit details."""
    with get_cursor() as cursor:
        if cursor is None:
            return False

        try:
            cursor.execute("""
                UPDATE positions
                SET status = 'closed',
                    exit_price = %s,
                    exit_date = CURRENT_TIMESTAMP,
                    exit_reason = %s,
                    profit_pct = %s,
                    holding_days = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (exit_price, exit_reason, profit_pct, holding_days, position_id))
            cursor.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Failed to close position: {e}")
            return False


def check_exit_conditions(
    position: dict,
    current_price: float,
    low_price: float,
    max_holding_days: int = 30
) -> tuple:
    """
    Check if position should be closed.

    Returns:
        (exit_reason, profit_pct) or (None, None) if should stay open
    """
    entry_price = float(position['entry_price'])
    stop_loss = float(position['stop_loss']) if position['stop_loss'] else entry_price * 0.92
    take_profit = float(position['take_profit']) if position['take_profit'] else entry_price * 1.20

    entry_date = position['entry_date']
    holding_days = (datetime.now() - entry_date).days if entry_date else 0

    # Calculate P&L
    profit_pct = ((current_price - entry_price) / entry_price) * 100

    # Check low price for stop loss (intraday stop)
    check_price = min(current_price, low_price) if low_price else current_price

    # Stop Loss check
    if check_price <= stop_loss:
        loss_pct = ((check_price - entry_price) / entry_price) * 100
        return "Stop Loss (-8%)", round(loss_pct, 2), holding_days

    # Take Profit check
    if current_price >= take_profit:
        return "Take Profit (+20%)", round(profit_pct, 2), holding_days

    # Max Holding Period check
    if holding_days >= max_holding_days:
        return f"Max Holding ({max_holding_days} days)", round(profit_pct, 2), holding_days

    return None, None, holding_days


def run_position_check():
    """Check all open positions and close if exit conditions met."""
    print("\n" + "=" * 60)
    print("📊 Position Manager")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Get open positions
    positions = get_open_positions()

    if not positions:
        print("\n⚪ No open positions")
        print("=" * 60 + "\n")
        return

    print(f"\n📈 Checking {len(positions)} open positions...")

    max_holding_days = int(os.getenv('MAX_HOLDING_DAYS', '30'))
    closed_count = 0

    for pos in positions:
        ticker = pos['ticker']
        entry_price = float(pos['entry_price'])

        print(f"\n   🔍 {ticker} (Entry: ${entry_price:.2f})")

        # Get current price
        try:
            df = USStockProvider.get_stock_data(ticker, period='5d')
            if df is None or len(df) == 0:
                print(f"      ⚠️  No data available")
                continue

            current_price = df['Close'].iloc[-1]
            low_price = df['Low'].iloc[-1]

            print(f"      Current: ${current_price:.2f}")

        except Exception as e:
            print(f"      ❌ Error: {e}")
            continue

        # Check exit conditions
        exit_reason, profit_pct, holding_days = check_exit_conditions(
            pos, current_price, low_price, max_holding_days
        )

        if exit_reason:
            # Close position
            if close_position(pos['id'], current_price, exit_reason, profit_pct, holding_days):
                emoji = "🟢" if profit_pct > 0 else "🔴"
                print(f"      {emoji} CLOSED: {exit_reason} ({profit_pct:+.2f}%)")
                closed_count += 1
            else:
                print(f"      ❌ Failed to close position")
        else:
            # Still holding
            current_pnl = ((current_price - entry_price) / entry_price) * 100
            emoji = "📈" if current_pnl > 0 else "📉"
            print(f"      {emoji} Holding: {current_pnl:+.2f}% ({holding_days} days)")

    print(f"\n📊 Summary:")
    print(f"   - Positions checked: {len(positions)}")
    print(f"   - Positions closed: {closed_count}")
    print("=" * 60 + "\n")


def main():
    run_position_check()


if __name__ == "__main__":
    main()
