"""Signal storage operations for alerts table"""
import json
import logging
from typing import Dict, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers.db import get_cursor

logger = logging.getLogger(__name__)


def save_signal(
    ticker: str,
    market: str,
    pattern: str,
    alert_price: float,
    signal_data: Optional[Dict] = None,
    source: str = "scanner"
) -> bool:
    """
    Save a breakout signal to the alerts table.
    Uses UPSERT to prevent duplicate alerts for same ticker/pattern on same day.

    Args:
        ticker: Stock ticker symbol
        market: Market identifier (e.g., 'US')
        pattern: Pattern type (e.g., 'Pivot Breakout')
        alert_price: Price at detection time
        signal_data: Additional signal data as dict
        source: Signal source identifier

    Returns:
        True if signal was saved (new), False if duplicate or error
    """
    with get_cursor() as cursor:
        if cursor is None:
            logger.error("Database not connected, cannot save signal")
            return False

        try:
            cursor.execute("""
                INSERT INTO alerts (ticker, market, pattern, source, alert_date, alert_price, signal_data)
                VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s)
                ON CONFLICT (ticker, pattern, alert_date) DO NOTHING
                RETURNING id
            """, (
                ticker,
                market,
                pattern,
                source,
                alert_price,
                json.dumps(signal_data) if signal_data else None
            ))

            result = cursor.fetchone()
            if result:
                logger.info(f"Signal saved: {ticker} - {pattern} @ ${alert_price:.2f}")
                return True
            else:
                logger.debug(f"Duplicate signal ignored: {ticker} - {pattern}")
                return False

        except Exception as e:
            logger.error(f"Error saving signal for {ticker}: {e}")
            return False


def has_alert_today(ticker: str, pattern: str) -> bool:
    """
    Check if alert already exists for today.

    Args:
        ticker: Stock ticker symbol
        pattern: Pattern type

    Returns:
        True if alert exists, False otherwise
    """
    with get_cursor() as cursor:
        if cursor is None:
            return False

        try:
            cursor.execute("""
                SELECT 1 FROM alerts
                WHERE ticker = %s AND pattern = %s AND alert_date = CURRENT_DATE
                LIMIT 1
            """, (ticker, pattern))

            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking alert for {ticker}: {e}")
            return False


def get_today_signal_count() -> int:
    """
    Get count of signals saved today.

    Returns:
        Number of signals saved today
    """
    with get_cursor() as cursor:
        if cursor is None:
            return 0

        try:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM alerts
                WHERE alert_date = CURRENT_DATE
            """)
            result = cursor.fetchone()
            return result['cnt'] if result else 0

        except Exception as e:
            logger.error(f"Error getting signal count: {e}")
            return 0
