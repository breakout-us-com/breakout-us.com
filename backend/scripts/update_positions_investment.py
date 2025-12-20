#!/usr/bin/env python3
"""
Update existing positions with investment amounts.

Migrated positions have NULL values for quantity and investment_amount.
This script calculates and updates these values based on entry_price.

Usage:
    python scripts/update_positions_investment.py [--dry-run]
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2
from psycopg2.extras import RealDictCursor
from sshtunnel import SSHTunnelForwarder


def get_ssh_tunnel():
    """Create SSH tunnel to database server."""
    ssh_host = os.environ.get('SSH_HOST', '')
    ssh_port = int(os.environ.get('SSH_PORT', '22'))
    ssh_user = os.environ.get('SSH_USER', '')
    ssh_key_path = os.path.expanduser(os.environ.get('SSH_KEY_PATH', '~/.ssh/id_rsa'))
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', '5432'))

    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_pkey=ssh_key_path,
        remote_bind_address=(db_host, db_port),
        local_bind_address=('127.0.0.1', 0),
    )
    tunnel.start()
    return tunnel


def get_connection(tunnel):
    """Get database connection."""
    db_name = os.environ.get('DB_NAME', 'breakout_us_db')
    db_user = os.environ.get('DB_USER', '')
    db_password = os.environ.get('DB_PASSWORD', '')

    return psycopg2.connect(
        host='127.0.0.1',
        port=tunnel.local_bind_port,
        database=db_name,
        user=db_user,
        password=db_password,
        cursor_factory=RealDictCursor
    )


def main():
    parser = argparse.ArgumentParser(description="Update positions with investment amounts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    # Paper Trading settings
    initial_capital = float(os.getenv('INITIAL_CAPITAL', '100000'))
    position_size_pct = float(os.getenv('POSITION_SIZE_PCT', '0.20'))
    position_size = initial_capital * position_size_pct

    print("\n" + "=" * 60)
    print("📊 Update Positions with Investment Amounts")
    print("=" * 60)
    print(f"   Initial Capital: ${initial_capital:,.0f}")
    print(f"   Position Size: {position_size_pct * 100:.0f}% = ${position_size:,.0f}")

    if args.dry_run:
        print("   (DRY RUN - no changes will be made)")

    # Create SSH tunnel
    print("\n🔗 Connecting via SSH tunnel...")
    try:
        tunnel = get_ssh_tunnel()
        print(f"   Connected (local port: {tunnel.local_bind_port})")
    except Exception as e:
        print(f"❌ SSH tunnel failed: {e}")
        return

    try:
        conn = get_connection(tunnel)

        with conn.cursor() as cur:
            # Find positions without investment_amount
            cur.execute("""
                SELECT id, ticker, entry_price, quantity, investment_amount
                FROM positions
                WHERE investment_amount IS NULL OR quantity IS NULL
                ORDER BY entry_date
            """)
            positions = cur.fetchall()

            print(f"\n📦 Found {len(positions)} positions to update")

            if not positions:
                print("   Nothing to update!")
                return

            updated = 0
            for pos in positions:
                entry_price = float(pos['entry_price'])
                investment_amount = position_size
                quantity = investment_amount / entry_price

                print(f"   {pos['ticker']}: ${investment_amount:,.0f} / ${entry_price:.2f} = {quantity:.2f} shares")

                if not args.dry_run:
                    cur.execute("""
                        UPDATE positions
                        SET quantity = %s,
                            investment_amount = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        round(quantity, 4),
                        round(investment_amount, 2),
                        pos['id']
                    ))
                    updated += 1

            if not args.dry_run:
                conn.commit()

            print("\n" + "=" * 60)
            print(f"📊 Summary:")
            print(f"   - Positions found: {len(positions)}")
            print(f"   - Updated: {updated if not args.dry_run else 'N/A (dry run)'}")
            if args.dry_run:
                print("   (DRY RUN - no actual changes made)")
            print("=" * 60 + "\n")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        tunnel.stop()
        print("🔌 Connection closed")


if __name__ == "__main__":
    main()
