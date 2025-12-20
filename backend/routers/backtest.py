"""백테스트 결과 API 라우터"""
import csv
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()

# 백테스트 결과 파일 경로
BACKTEST_RESULTS_PATH = Path(
    "/Users/pink-spider/Code/github/dev-minimalism/us-oneil-simple-breakout-notifier/us_backtest_results.csv"
)


def load_backtest_results():
    """백테스트 결과 CSV 파일 로드"""
    results = []
    if not BACKTEST_RESULTS_PATH.exists():
        return results

    with open(BACKTEST_RESULTS_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "ticker": row["ticker"],
                "market": row["market"],
                "pattern": row["pattern"],
                "entry_date": row["entry_date"].split(" ")[0] if row["entry_date"] else None,
                "entry_price": float(row["entry_price"]) if row["entry_price"] else 0,
                "exit_date": row["exit_date"].split(" ")[0] if row["exit_date"] else None,
                "exit_price": float(row["exit_price"]) if row["exit_price"] else 0,
                "shares": int(row["shares"]) if row["shares"] else 0,
                "cost": float(row["cost"]) if row["cost"] else 0,
                "proceeds": float(row["proceeds"]) if row["proceeds"] else 0,
                "profit": float(row["profit"]) if row["profit"] else 0,
                "profit_pct": float(row["profit_pct"]) if row["profit_pct"] else 0,
                "holding_days": int(row["holding_days"]) if row["holding_days"] else 0,
                "reason": row["reason"]
            })
    return results


@router.get("/backtest/results")
async def get_backtest_results(
    pattern: Optional[str] = Query(None, description="패턴 필터 (컵앤핸들, 피벗돌파, 베이스돌파)"),
    ticker: Optional[str] = Query(None, description="종목 필터"),
    limit: int = Query(100, description="결과 개수 제한")
):
    """백테스트 거래 결과 반환"""
    results = load_backtest_results()

    # 필터링
    if pattern:
        results = [r for r in results if r["pattern"] == pattern]
    if ticker:
        results = [r for r in results if r["ticker"] == ticker.upper()]

    # 최신순 정렬
    results = sorted(results, key=lambda x: x["entry_date"] or "", reverse=True)

    return {
        "total": len(results),
        "results": results[:limit]
    }


@router.get("/backtest/stats")
async def get_backtest_stats():
    """백테스트 성과 통계 반환"""
    results = load_backtest_results()

    if not results:
        return {"error": "No backtest results found"}

    # 전체 통계
    total_trades = len(results)
    winning_trades = len([r for r in results if r["profit"] > 0])
    losing_trades = len([r for r in results if r["profit"] < 0])

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    total_profit = sum(r["profit"] for r in results)
    avg_profit_pct = sum(r["profit_pct"] for r in results) / total_trades if total_trades > 0 else 0

    # 승리/패배 평균
    winning_results = [r for r in results if r["profit"] > 0]
    losing_results = [r for r in results if r["profit"] < 0]

    avg_win_pct = sum(r["profit_pct"] for r in winning_results) / len(winning_results) if winning_results else 0
    avg_loss_pct = sum(r["profit_pct"] for r in losing_results) / len(losing_results) if losing_results else 0

    # 최대 수익/손실
    max_profit_pct = max(r["profit_pct"] for r in results) if results else 0
    max_loss_pct = min(r["profit_pct"] for r in results) if results else 0

    # 패턴별 통계
    pattern_stats = {}
    patterns = set(r["pattern"] for r in results)
    for pattern in patterns:
        pattern_results = [r for r in results if r["pattern"] == pattern]
        pattern_wins = len([r for r in pattern_results if r["profit"] > 0])
        pattern_stats[pattern] = {
            "total": len(pattern_results),
            "wins": pattern_wins,
            "losses": len(pattern_results) - pattern_wins,
            "win_rate": (pattern_wins / len(pattern_results) * 100) if pattern_results else 0,
            "avg_profit_pct": sum(r["profit_pct"] for r in pattern_results) / len(pattern_results) if pattern_results else 0
        }

    # 청산 사유별 통계
    reason_stats = {}
    reasons = set(r["reason"] for r in results)
    for reason in reasons:
        reason_results = [r for r in results if r["reason"] == reason]
        reason_stats[reason] = {
            "count": len(reason_results),
            "avg_profit_pct": sum(r["profit_pct"] for r in reason_results) / len(reason_results) if reason_results else 0
        }

    # 기간 계산
    entry_dates = [r["entry_date"] for r in results if r["entry_date"]]
    exit_dates = [r["exit_date"] for r in results if r["exit_date"]]
    all_dates = entry_dates + exit_dates

    start_date = min(all_dates) if all_dates else None
    end_date = max(all_dates) if all_dates else None

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 2),
        "total_profit": round(total_profit, 2),
        "avg_profit_pct": round(avg_profit_pct, 2),
        "avg_win_pct": round(avg_win_pct, 2),
        "avg_loss_pct": round(avg_loss_pct, 2),
        "max_profit_pct": round(max_profit_pct, 2),
        "max_loss_pct": round(max_loss_pct, 2),
        "pattern_stats": pattern_stats,
        "reason_stats": reason_stats,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get("/backtest/patterns")
async def get_available_patterns():
    """사용 가능한 패턴 목록 반환"""
    return {
        "patterns": [
            {
                "name": "컵앤핸들",
                "description": "Cup-and-Handle 패턴. 컵 깊이 12-40%, 핸들 깊이 12% 미만",
                "volume_requirement": "거래량 급증 필요"
            },
            {
                "name": "피벗돌파",
                "description": "Pivot Point Breakout. 20일 저항선 돌파",
                "volume_requirement": "거래량 50% 이상 급증"
            },
            {
                "name": "베이스돌파",
                "description": "Base Breakout. 30일 저변동성 베이스 형성 후 돌파",
                "volume_requirement": "거래량 40% 이상 급증"
            }
        ]
    }
