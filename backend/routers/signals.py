"""Today's Signals API 라우터"""
from datetime import date, datetime
from fastapi import APIRouter

from .db import get_cursor

router = APIRouter()

# 마지막 스캔 시간 추적
_last_scan_time: datetime | None = None


@router.get("/signals/today")
async def get_today_signals():
    """오늘 발생한 시그널 목록"""
    with get_cursor() as cursor:
        if cursor is None:
            return {"signals": [], "count": 0, "last_scan": None, "error": "Database not connected"}

        try:
            cursor.execute("""
                SELECT ticker, market, pattern, source, alert_price, signal_data, sent_at
                FROM alerts
                WHERE alert_date = CURRENT_DATE
                ORDER BY sent_at DESC
            """)
            results = cursor.fetchall()

            signals = []
            last_scan_time = None
            for r in results:
                signal_data = r.get('signal_data') or {}
                sent_at = r['sent_at']
                if sent_at and (last_scan_time is None or sent_at > last_scan_time):
                    last_scan_time = sent_at
                # Support both old (volume_surge) and new (volume_surge_pct) key names
                volume_surge = signal_data.get('volume_surge_pct') or signal_data.get('volume_surge')
                signals.append({
                    "ticker": r['ticker'],
                    "market": r['market'],
                    "pattern": r['pattern'],
                    "source": r['source'],
                    "price": float(r['alert_price']),
                    "time": sent_at.strftime("%H:%M:%S") if sent_at else None,
                    "volume_surge": volume_surge,
                    "breakout_pct": signal_data.get('breakout_pct'),
                    "resistance": signal_data.get('resistance'),
                })

            # 마지막 스캔 시간 (가장 최근 시그널 시간 또는 전체 최근 시그널)
            if last_scan_time is None:
                cursor.execute("""
                    SELECT MAX(sent_at) as last_sent
                    FROM alerts
                """)
                result = cursor.fetchone()
                if result and result['last_sent']:
                    last_scan_time = result['last_sent']

            return {
                "date": date.today().isoformat(),
                "count": len(signals),
                "signals": signals,
                "last_scan": last_scan_time.isoformat() if last_scan_time else None,
            }
        except Exception as e:
            return {"signals": [], "count": 0, "last_scan": None, "error": str(e)}


@router.get("/signals/recent")
async def get_recent_signals(days: int = 7):
    """최근 N일간의 시그널 목록"""
    with get_cursor() as cursor:
        if cursor is None:
            return {"signals": [], "count": 0, "error": "Database not connected"}

        try:
            cursor.execute("""
                SELECT ticker, market, pattern, source, alert_date, alert_price, signal_data, sent_at
                FROM alerts
                WHERE alert_date >= CURRENT_DATE - INTERVAL '%s days'
                  AND alert_date < CURRENT_DATE
                ORDER BY alert_date DESC, sent_at DESC
            """, (days,))
            results = cursor.fetchall()

            signals = []
            for r in results:
                signal_data = r.get('signal_data') or {}
                # Support both old (volume_surge) and new (volume_surge_pct) key names
                volume_surge = signal_data.get('volume_surge_pct') or signal_data.get('volume_surge')
                signals.append({
                    "ticker": r['ticker'],
                    "market": r['market'],
                    "pattern": r['pattern'],
                    "source": r['source'],
                    "date": r['alert_date'].isoformat() if r['alert_date'] else None,
                    "price": float(r['alert_price']),
                    "time": r['sent_at'].strftime("%H:%M:%S") if r['sent_at'] else None,
                    "volume_surge": volume_surge,
                    "breakout_pct": signal_data.get('breakout_pct'),
                })

            return {
                "days": days,
                "count": len(signals),
                "signals": signals
            }
        except Exception as e:
            return {"signals": [], "count": 0, "error": str(e)}
