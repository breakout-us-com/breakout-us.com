"""워치리스트 API 라우터"""
import os
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

# Dynamic Scanner 워치리스트 파일 경로 (환경변수 또는 기본값)
DYNAMIC_WATCHLIST_PATH = Path(
    os.getenv(
        "DYNAMIC_WATCHLIST_PATH",
        "/var/www/breakout-us.com/watchlist.json"
    )
)

# S&P 500 시총 상위 50개 종목 (2024년 기준) - O'Neil Scanner
ONEIL_WATCHLIST = {
    "Tech": [
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "CSCO", "ACN", "ADBE", "AMD"
    ],
    "Communication": [
        "GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ"
    ],
    "Consumer": [
        "AMZN", "TSLA", "HD", "MCD", "COST", "WMT", "PG", "KO", "PEP", "NKE"
    ],
    "Financial": [
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK"
    ],
    "Healthcare": [
        "UNH", "JNJ", "LLY", "MRK", "ABBV", "TMO", "ABT", "PFE"
    ],
    "Energy": [
        "XOM", "CVX"
    ],
    "Industrial": [
        "GE", "CAT", "UNP", "RTX", "HON"
    ]
}


def load_dynamic_watchlist():
    """Dynamic Scanner 워치리스트 로드"""
    if not DYNAMIC_WATCHLIST_PATH.exists():
        return None

    with open(DYNAMIC_WATCHLIST_PATH, "r") as f:
        return json.load(f)


@router.get("/watchlist")
async def get_watchlist():
    """현재 모니터링 중인 종목 목록 반환 (O'Neil + Dynamic)"""
    # O'Neil 워치리스트
    oneil_stocks = []
    for stocks in ONEIL_WATCHLIST.values():
        oneil_stocks.extend(stocks)

    # Dynamic 워치리스트
    dynamic_data = load_dynamic_watchlist()
    dynamic_stocks = dynamic_data.get("tickers", []) if dynamic_data else []
    dynamic_updated = dynamic_data.get("updated_at") if dynamic_data else None

    # Dynamic에서 고정 종목 제외
    oneil_set = set(oneil_stocks)
    dynamic_only = [s for s in dynamic_stocks if s not in oneil_set]

    return {
        "fixed": {
            "total": len(oneil_stocks),
            "by_sector": ONEIL_WATCHLIST,
            "all": sorted(set(oneil_stocks)),
            "source": "oneil",
            "label": "고정",
            "description": "S&P 500 시총 상위 50개 고정 종목"
        },
        "dynamic": {
            "total": len(dynamic_only),
            "all": dynamic_only,
            "source": "dynamic",
            "label": "동적",
            "description": "S&P 500 + NASDAQ 100 동적 스크리닝 (고정 제외)",
            "updated_at": dynamic_updated
        },
        "total": len(set(oneil_stocks + dynamic_stocks))
    }


@router.get("/watchlist/oneil")
async def get_oneil_watchlist():
    """O'Neil Scanner 워치리스트"""
    all_stocks = []
    for stocks in ONEIL_WATCHLIST.values():
        all_stocks.extend(stocks)

    return {
        "total": len(all_stocks),
        "by_sector": ONEIL_WATCHLIST,
        "all": sorted(set(all_stocks))
    }


@router.get("/watchlist/dynamic")
async def get_dynamic_watchlist():
    """Dynamic Scanner 워치리스트"""
    data = load_dynamic_watchlist()
    if not data:
        return {"total": 0, "all": [], "error": "Dynamic watchlist not found"}

    return {
        "total": len(data.get("tickers", [])),
        "all": data.get("tickers", []),
        "updated_at": data.get("updated_at"),
        "screening_mode": data.get("screening_mode")
    }


@router.get("/watchlist/sectors")
async def get_sectors():
    """O'Neil 섹터별 종목 분류 반환"""
    return ONEIL_WATCHLIST
