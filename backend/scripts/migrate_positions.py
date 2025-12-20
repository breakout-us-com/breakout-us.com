#!/usr/bin/env python3
"""
Migrate positions from us_dynamic_breakout_notifier_db to breakout_us_db.

Usage:
    python scripts/migrate_positions.py [--dry-run]
"""

import argparse
import json
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


def get_connection(tunnel, db_name: str):
    """Get database connection."""
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


def fetch_source_positions(tunnel) -> list:
    """Fetch positions from us_dynamic_breakout_notifier_db."""
    source_db = "us_dynamic_breakout_notifier_db"

    print(f"\n📖 Reading from: {source_db}")

    try:
        conn = get_connection(tunnel, source_db)
        with conn.cursor() as cur:
            # Check table structure first
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'positions'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print(f"   Source columns: {[c['column_name'] for c in columns]}")

            # Fetch all positions
            cur.execute("""
                SELECT * FROM positions ORDER BY entry_date
            """)
            positions = cur.fetchall()
            print(f"   Found {len(positions)} positions")

        conn.close()
        return positions

    except Exception as e:
        print(f"❌ Error reading source DB: {e}")
        return []


def insert_positions(tunnel, positions: list, dry_run: bool = False) -> int:
    """Insert positions into breakout_us_db."""
    target_db = os.environ.get('DB_NAME', 'breakout_us_db')

    print(f"\n📝 Writing to: {target_db}")

    if dry_run:
        print("   (DRY RUN - no changes will be made)")

    try:
        conn = get_connection(tunnel, target_db)
        inserted = 0
        skipped = 0

        with conn.cursor() as cur:
            for pos in positions:
                ticker = pos.get('ticker')
                entry_date = pos.get('entry_date')

                # Check if already exists
                cur.execute("""
                    SELECT id FROM positions
                    WHERE ticker = %s AND entry_date = %s
                """, (ticker, entry_date))

                if cur.fetchone():
                    print(f"   ⏭️  Skip (exists): {ticker}")
                    skipped += 1
                    continue

                if not dry_run:
                    # Convert signal_data to JSON string if it's a dict
                    signal_data = pos.get('signal_data')
                    if isinstance(signal_data, dict):
                        signal_data = json.dumps(signal_data)

                    # Insert position
                    cur.execute("""
                        INSERT INTO positions (
                            ticker, market, source, entry_price, entry_date,
                            pattern, stop_loss, take_profit, signal_data, status,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            COALESCE(%s, CURRENT_TIMESTAMP),
                            CURRENT_TIMESTAMP
                        )
                    """, (
                        ticker,
                        pos.get('market', 'US'),
                        'dynamic',  # source
                        pos.get('entry_price'),
                        entry_date,
                        pos.get('pattern'),
                        pos.get('stop_loss'),
                        pos.get('take_profit'),
                        signal_data,
                        'open',  # status
                        entry_date,  # created_at
                    ))

                print(f"   ✅ Insert: {ticker} @ ${float(pos.get('entry_price', 0)):.2f}")
                inserted += 1

            if not dry_run:
                conn.commit()

        conn.close()
        return inserted, skipped

    except Exception as e:
        print(f"❌ Error writing to target DB: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0


def main():
    parser = argparse.ArgumentParser(description="Migrate positions between databases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("📦 Position Migration")
    print("   From: us_dynamic_breakout_notifier_db")
    print("   To:   breakout_us_db")
    print("=" * 60)

    # Create SSH tunnel
    print("\n🔗 Connecting via SSH tunnel...")
    try:
        tunnel = get_ssh_tunnel()
        print(f"   Connected (local port: {tunnel.local_bind_port})")
    except Exception as e:
        print(f"❌ SSH tunnel failed: {e}")
        return

    try:
        # Fetch source positions
        positions = fetch_source_positions(tunnel)

        if not positions:
            print("\n⚠️  No positions to migrate")
            return

        # Insert into target
        inserted, skipped = insert_positions(tunnel, positions, dry_run=args.dry_run)

        print("\n" + "=" * 60)
        print("📊 Summary:")
        print(f"   - Total in source: {len(positions)}")
        print(f"   - Inserted: {inserted}")
        print(f"   - Skipped (already exists): {skipped}")
        if args.dry_run:
            print("   (DRY RUN - no actual changes made)")
        print("=" * 60 + "\n")

    finally:
        tunnel.stop()
        print("🔌 Connection closed")


if __name__ == "__main__":
    main()
