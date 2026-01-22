"""Signal storage operations for alerts and positions tables"""
import json
import os
from typing import Dict, Optional, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from routers.db import get_cursor
from logging_config import setup_logging

logger = setup_logging("scanner")

# Paper Trading settings
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '100000'))
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', '0.20'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))
STOP_LOSS_PCT = float(os.getenv('STOP_LOSS_PCT', '0.08'))
TAKE_PROFIT_PCT = float(os.getenv('TAKE_PROFIT_PCT', '0.20'))


def _convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for DB/JSON compatibility."""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    return obj


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
            # Convert numpy types to native Python types
            safe_price = _convert_numpy_types(alert_price)
            safe_signal_data = _convert_numpy_types(signal_data) if signal_data else None

            cursor.execute("""
                INSERT INTO alerts (ticker, market, pattern, source, alert_date, alert_price, signal_data)
                VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s)
                ON CONFLICT (ticker, pattern, source, alert_date) DO NOTHING
                RETURNING id
            """, (
                ticker,
                market,
                pattern,
                source,
                safe_price,
                json.dumps(safe_signal_data) if safe_signal_data else None
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


def has_alert_today(ticker: str, pattern: str, source: str = "background_scanner") -> bool:
    """
    Check if alert already exists for today.

    Args:
        ticker: Stock ticker symbol
        pattern: Pattern type
        source: Signal source identifier

    Returns:
        True if alert exists, False otherwise
    """
    with get_cursor() as cursor:
        if cursor is None:
            return False

        try:
            cursor.execute("""
                SELECT 1 FROM alerts
                WHERE ticker = %s AND pattern = %s AND source = %s AND alert_date = CURRENT_DATE
                LIMIT 1
            """, (ticker, pattern, source))

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
        except Exception as e:
            logger.error(f"Error checking position for {ticker}: {e}")
            return False


def get_available_capital() -> float:
    """Calculate available capital for new positions."""
    with get_cursor() as cursor:
        if cursor is None:
            return 0

        try:
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
            if position_count >= MAX_POSITIONS:
                logger.debug(f"Max positions reached: {position_count}/{MAX_POSITIONS}")
                return 0

            # Calculate available capital
            available = INITIAL_CAPITAL - total_invested
            position_size = INITIAL_CAPITAL * POSITION_SIZE_PCT

            return min(available, position_size)

        except Exception as e:
            logger.error(f"Error getting available capital: {e}")
            return 0


def save_position(
    ticker: str,
    market: str,
    pattern: str,
    entry_price: float,
    signal_data: Optional[Dict] = None,
    source: str = "background_scanner"
) -> bool:
    """
    Save a position to the positions table for Paper Trading.

    Args:
        ticker: Stock ticker symbol
        market: Market identifier (e.g., 'US')
        pattern: Pattern type (e.g., 'Pivot Breakout')
        entry_price: Entry price
        signal_data: Additional signal data as dict
        source: Signal source identifier

    Returns:
        True if position was created, False otherwise
    """
    # Skip if already has open position
    if has_open_position(ticker):
        logger.debug(f"Position already exists for {ticker}")
        return False

    # Check available capital
    available_capital = get_available_capital()
    if available_capital <= 0:
        logger.debug(f"No capital available for {ticker}")
        return False

    with get_cursor() as cursor:
        if cursor is None:
            logger.error("Database not connected, cannot save position")
            return False

        try:
            # Convert numpy types
            safe_price = _convert_numpy_types(entry_price)
            safe_signal_data = _convert_numpy_types(signal_data) if signal_data else None

            # Calculate position size
            investment_amount = available_capital
            quantity = investment_amount / safe_price

            cursor.execute("""
                INSERT INTO positions (
                    ticker, market, source, entry_price, quantity, investment_amount,
                    pattern, stop_loss, take_profit, signal_data, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'open')
                RETURNING id
            """, (
                ticker,
                market,
                source,
                safe_price,
                round(quantity, 4),
                round(investment_amount, 2),
                pattern,
                round(safe_price * (1 - STOP_LOSS_PCT), 4),
                round(safe_price * (1 + TAKE_PROFIT_PCT), 4),
                json.dumps(safe_signal_data) if safe_signal_data else None
            ))

            result = cursor.fetchone()
            if result:
                logger.info(
                    f"Position opened: {ticker} @ ${safe_price:.2f} "
                    f"(${investment_amount:,.0f}, {quantity:.2f} shares)"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Error saving position for {ticker}: {e}")
            return False
