"""Market status checking for US stocks (based on KST timezone)"""
from datetime import datetime, time as dt_time
from typing import TypedDict


class MarketStatus(TypedDict):
    is_open: bool
    time: str
    weekday: int


def get_market_status() -> MarketStatus:
    """
    Check US market status based on Korea Standard Time (KST).

    US market hours in KST:
    - Summer (DST): 22:30 - 05:00 next day
    - Winter: 23:30 - 06:00 next day
    - Using wider window: 22:00 - 07:00 for margin

    Returns:
        MarketStatus dict with is_open, time, weekday
    """
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()

    # Weekend check (Saturday=5, Sunday=6)
    is_weekend = weekday >= 5

    # US market hours in KST (with buffer)
    us_open_night = dt_time(22, 0)
    us_close_morning = dt_time(7, 0)

    is_open = False
    if not is_weekend:
        # Night session (22:00 - 23:59)
        if current_time >= us_open_night:
            is_open = True
        # Morning session (00:00 - 07:00)
        elif current_time <= us_close_morning:
            # Check if previous day was not Sunday (weekday would be 0 for Monday morning)
            # Monday 00:00-07:00 is valid (Sunday night trading)
            is_open = True

    # Special case: Sunday night after 22:00 is Monday's trading
    if weekday == 6 and current_time >= us_open_night:
        is_open = True

    # Saturday morning before 07:00 is Friday's trading end
    if weekday == 5 and current_time <= us_close_morning:
        is_open = True

    return {
        'is_open': is_open,
        'time': now.strftime('%H:%M:%S'),
        'weekday': weekday
    }


def format_market_status_message(
    status: MarketStatus,
    watchlist_count: int = 0
) -> str:
    """
    Format market status for display.

    Args:
        status: MarketStatus dict
        watchlist_count: Number of stocks in watchlist

    Returns:
        Formatted status message
    """
    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    weekday_name = weekday_names[status['weekday']]

    if status['is_open']:
        market_text = "US Market OPEN"
    else:
        market_text = "US Market CLOSED"

    return f"{market_text} | {weekday_name} {status['time']} KST | {watchlist_count} stocks"
