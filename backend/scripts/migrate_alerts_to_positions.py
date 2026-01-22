#!/usr/bin/env python3
"""
Migrate alerts to positions table for Paper Trading.

Converts existing alerts into paper trading positions.

Usage:
    python scripts/migrate_alerts_to_positions.py [--dry-run]
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers.db import get_cursor, get_db_connection

# Paper Trading settings
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '100000'))
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', '0.20'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))
STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', '0.08'))
TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', '0.20'))


def fetch_alerts_without_positions() -> list:
    """Fetch alerts that don't have corresponding positions."""
    with get_cursor() as cursor:
        if cursor is None:
            print("Database not connected")
            return []

        try:
            # Find alerts that don't have a matching position
            cursor.execute("""
                SELECT a.id, a.ticker, a.market, a.pattern, a.source,
                       a.alert_date, a.alert_price, a.signal_data
                FROM alerts a
                LEFT JOIN positions p
                    ON a.ticker = p.ticker
                    AND a.alert_date::date = p.entry_date::date
                WHERE p.id IS NULL
                ORDER BY a.alert_date ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return []


def create_position_from_alert(alert: dict, dry_run: bool = False) -> bool:
    """Create a position from an alert."""
    ticker = alert['ticker']
    entry_price = float(alert['alert_price'])

    # Calculate position size
    position_size = INITIAL_CAPITAL * POSITION_SIZE_PCT
    quantity = position_size / entry_price

    # Calculate stop loss and take profit
    stop_loss = entry_price * (1 - STOP_LOSS_PCT)
    take_profit = entry_price * (1 + TAKE_PROFIT_PCT)

    if dry_run:
        print(f"   [DRY RUN] Would create: {ticker} @ ${entry_price:.2f} "
              f"(${position_size:,.0f}, {quantity:.2f} shares)")
        return True

    with get_cursor() as cursor:
        if cursor is None:
            return False

        try:
            # Convert signal_data
            signal_data = alert.get('signal_data')
            if isinstance(signal_data, dict):
                signal_data = json.dumps(signal_data)
            elif signal_data is None:
                signal_data = None

            cursor.execute("""
                INSERT INTO positions (
                    ticker, market, source, entry_price, quantity, investment_amount,
                    entry_date, pattern, stop_loss, take_profit, signal_data, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'open')
                RETURNING id
            """, (
                ticker,
                alert.get('market', 'US'),
                alert.get('source', 'background_scanner'),
                entry_price,
                round(quantity, 4),
                round(position_size, 2),
                alert['alert_date'],
                alert['pattern'],
                round(stop_loss, 4),
                round(take_profit, 4),
                signal_data
            ))

            result = cursor.fetchone()
            if result:
                print(f"   Created: {ticker} @ ${entry_price:.2f} "
                      f"(${position_size:,.0f}, {quantity:.2f} shares)")
                return True
            return False

        except Exception as e:
            print(f"   Error creating position for {ticker}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Migrate alerts to positions")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Migrate Alerts to Positions")
    print("=" * 60)
    print(f"\nSettings:")
    print(f"  - Initial Capital: ${INITIAL_CAPITAL:,.0f}")
    print(f"  - Position Size: {POSITION_SIZE_PCT * 100:.0f}% (${INITIAL_CAPITAL * POSITION_SIZE_PCT:,.0f})")
    print(f"  - Stop Loss: -{STOP_LOSS_PCT * 100:.0f}%")
    print(f"  - Take Profit: +{TAKE_PROFIT_PCT * 100:.0f}%")

    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    # Connect to database
    print("\nConnecting to database...")
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to database")
        return

    # Fetch alerts without positions
    print("\nFetching alerts without positions...")
    alerts = fetch_alerts_without_positions()

    if not alerts:
        print("No alerts to migrate!")
        return

    print(f"Found {len(alerts)} alerts to migrate\n")

    # Create positions
    created = 0
    failed = 0

    for alert in alerts:
        if create_position_from_alert(alert, dry_run=args.dry_run):
            created += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  - Total alerts: {len(alerts)}")
    print(f"  - Positions created: {created}")
    print(f"  - Failed: {failed}")
    if args.dry_run:
        print("  (DRY RUN - no actual changes made)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
