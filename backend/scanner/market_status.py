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

    # KST 기준 미국장 매핑:
    # - 밤 세션 (22:00-23:59): 월-금만 유효 (당일 ET 장 시작)
    # - 새벽 세션 (00:00-07:00): 화-토만 유효 (전날 ET 장 마감)
    # - 일요일 밤 / 월요일 새벽은 ET 기준 일요일이므로 휴장
    is_open = False
    if weekday <= 4 and current_time >= us_open_night:
        is_open = True
    elif 1 <= weekday <= 5 and current_time <= us_close_morning:
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
