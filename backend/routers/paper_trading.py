"""Paper Trading API 라우터"""
import os
from datetime import datetime
from typing import Dict
from fastapi import APIRouter

import pandas as pd
import yfinance as yf

from .db import get_cursor, is_connected

router = APIRouter()

# Paper Trading 설정
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '100000'))
POSITION_SIZE_PCT = float(os.getenv('POSITION_SIZE_PCT', '0.20'))
MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', '5'))


def get_current_prices(tickers: list) -> Dict[str, float]:
    """Fetch current prices for multiple tickers."""
    if not tickers:
        return {}

    prices = {}
    try:
        # Batch download for efficiency
        data = yf.download(tickers, period='1d', progress=False, threads=True)

        if len(tickers) == 1:
            # Single ticker returns Series
            if not data.empty:
                prices[tickers[0]] = float(data['Close'].iloc[-1])
        else:
            # Multiple tickers returns DataFrame with MultiIndex columns
            if not data.empty and 'Close' in data.columns.get_level_values(0):
                for ticker in tickers:
                    try:
                        close = data['Close'][ticker].iloc[-1]
                        if not pd.isna(close):
                            prices[ticker] = float(close)
                    except (KeyError, IndexError):
                        pass
    except Exception:
        pass

    return prices


@router.get("/paper-trading/positions")
async def get_open_positions():
    """현재 오픈 포지션 목록 (현재가, 수익률, 투자금액 포함)"""
    if not is_connected():
        pass

    with get_cursor() as cursor:
        if cursor is None:
            return {"positions": [], "count": 0, "total_pnl_pct": 0, "error": "Database not connected"}

        try:
            cursor.execute("""
                SELECT id, ticker, market, source, entry_price, quantity, investment_amount,
                       entry_date, pattern, stop_loss, take_profit, signal_data
                FROM positions
                WHERE status = 'open'
                ORDER BY entry_date DESC
            """)
            results = cursor.fetchall()

            if not results:
                return {
                    "positions": [],
                    "count": 0,
                    "winning": 0,
                    "losing": 0,
                    "total_invested": 0,
                    "total_value": 0,
                    "total_pnl_amount": 0,
                    "total_pnl_pct": 0,
                    "available_capital": INITIAL_CAPITAL,
                }

            # Get current prices for all tickers
            tickers = [r['ticker'] for r in results]
            current_prices = get_current_prices(tickers)

            positions = []
            total_invested = 0
            total_value = 0
            winning = 0
            losing = 0

            for r in results:
                ticker = r['ticker']
                entry_price = float(r['entry_price'])
                quantity = float(r['quantity']) if r['quantity'] else 0
                investment_amount = float(r['investment_amount']) if r['investment_amount'] else 0
                entry_date = r['entry_date']
                holding_days = (datetime.now() - entry_date).days if entry_date else 0

                # If no investment data, estimate from entry price
                if investment_amount == 0:
                    investment_amount = INITIAL_CAPITAL * POSITION_SIZE_PCT
                    quantity = investment_amount / entry_price

                total_invested += investment_amount

                # Calculate P&L
                current_price = current_prices.get(ticker)
                if current_price:
                    current_value = quantity * current_price
                    pnl_amount = current_value - investment_amount
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    total_value += current_value

                    if pnl_pct > 0:
                        winning += 1
                    else:
                        losing += 1
                else:
                    current_price = None
                    current_value = investment_amount
                    pnl_amount = 0
                    pnl_pct = None
                    total_value += investment_amount

                positions.append({
                    "id": r['id'],
                    "ticker": ticker,
                    "market": r['market'],
                    "source": r.get('source', 'dynamic'),
                    "entry_price": entry_price,
                    "current_price": round(current_price, 2) if current_price else None,
                    "quantity": round(quantity, 2),
                    "investment_amount": round(investment_amount, 2),
                    "current_value": round(current_value, 2),
                    "pnl_amount": round(pnl_amount, 2),
                    "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
                    "entry_date": entry_date.strftime("%Y-%m-%d") if entry_date else None,
                    "pattern": r['pattern'],
                    "stop_loss": float(r['stop_loss']) if r['stop_loss'] else None,
                    "take_profit": float(r['take_profit']) if r['take_profit'] else None,
                    "holding_days": holding_days,
                })

            # Sort by P&L (highest first)
            positions.sort(key=lambda x: x['pnl_pct'] if x['pnl_pct'] is not None else -999, reverse=True)

            total_pnl_amount = total_value - total_invested
            total_pnl_pct = (total_pnl_amount / total_invested * 100) if total_invested > 0 else 0
            available_capital = INITIAL_CAPITAL - total_invested

            return {
                "count": len(positions),
                "winning": winning,
                "losing": losing,
                "total_invested": round(total_invested, 2),
                "total_value": round(total_value, 2),
                "total_pnl_amount": round(total_pnl_amount, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "available_capital": round(available_capital, 2),
                "positions": positions
            }
        except Exception as e:
            return {"positions": [], "count": 0, "total_pnl_pct": 0, "error": str(e)}


@router.get("/paper-trading/closed")
async def get_closed_positions(limit: int = 50):
    """청산된 포지션 목록 (Paper Trading 거래 내역)"""
    with get_cursor() as cursor:
        if cursor is None:
            return {"trades": [], "count": 0, "error": "Database not connected"}

        try:
            cursor.execute("""
                SELECT id, ticker, market, source, entry_price, entry_date, pattern,
                       exit_price, exit_date, exit_reason, profit_pct, holding_days
                FROM positions
                WHERE status = 'closed'
                ORDER BY exit_date DESC
                LIMIT %s
            """, (limit,))
            results = cursor.fetchall()

            trades = []
            for r in results:
                entry_date = r['entry_date']
                exit_date = r['exit_date']
                holding_days = r.get('holding_days') or (
                    (exit_date - entry_date).days if entry_date and exit_date else 0
                )

                trades.append({
                    "id": r['id'],
                    "ticker": r['ticker'],
                    "market": r['market'],
                    "source": r.get('source', 'dynamic'),
                    "entry_price": float(r['entry_price']),
                    "entry_date": entry_date.strftime("%Y-%m-%d") if entry_date else None,
                    "exit_price": float(r['exit_price']) if r['exit_price'] else None,
                    "exit_date": exit_date.strftime("%Y-%m-%d") if exit_date else None,
                    "pattern": r['pattern'],
                    "exit_reason": r['exit_reason'],
                    "profit_pct": float(r['profit_pct']) if r['profit_pct'] else 0,
                    "holding_days": holding_days,
                })

            return {
                "count": len(trades),
                "trades": trades
            }
        except Exception as e:
            return {"trades": [], "count": 0, "error": str(e)}


@router.get("/paper-trading/stats")
async def get_trading_stats():
    """Paper Trading 통계 (오픈 포지션 현재 수익률 포함)"""
    with get_cursor() as cursor:
        if cursor is None:
            return {"error": "Database not connected"}

        try:
            # Get start date (first position entry date)
            cursor.execute("""
                SELECT MIN(entry_date) as start_date
                FROM positions
            """)
            start_result = cursor.fetchone()
            start_date = start_result['start_date'] if start_result else None

            # Closed trades stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_pct > 0 THEN 1 END) as win_count,
                    COUNT(CASE WHEN profit_pct <= 0 THEN 1 END) as loss_count,
                    COALESCE(AVG(profit_pct), 0) as avg_profit,
                    COALESCE(AVG(CASE WHEN profit_pct > 0 THEN profit_pct END), 0) as avg_win,
                    COALESCE(AVG(CASE WHEN profit_pct <= 0 THEN profit_pct END), 0) as avg_loss,
                    COALESCE(MAX(profit_pct), 0) as max_profit,
                    COALESCE(MIN(profit_pct), 0) as max_loss,
                    COALESCE(SUM(profit_pct), 0) as total_profit
                FROM positions
                WHERE status = 'closed'
            """)
            closed_stats = cursor.fetchone()

            # Open positions
            cursor.execute("""
                SELECT ticker, entry_price
                FROM positions
                WHERE status = 'open'
            """)
            open_positions = cursor.fetchall()
            open_count = len(open_positions)

            # Calculate unrealized P&L for open positions
            open_pnl = 0
            open_winning = 0
            open_losing = 0

            if open_positions:
                tickers = [p['ticker'] for p in open_positions]
                current_prices = get_current_prices(tickers)

                for pos in open_positions:
                    ticker = pos['ticker']
                    entry_price = float(pos['entry_price'])
                    current_price = current_prices.get(ticker)

                    if current_price:
                        pnl = ((current_price - entry_price) / entry_price) * 100
                        open_pnl += pnl
                        if pnl > 0:
                            open_winning += 1
                        else:
                            open_losing += 1

            total = closed_stats['total_trades'] or 0
            wins = closed_stats['win_count'] or 0

            # Calculate trading days
            trading_days = None
            if start_date:
                trading_days = (datetime.now() - start_date).days

            return {
                # Trading period
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "trading_days": trading_days,

                # Open positions stats
                "open_positions": open_count,
                "open_winning": open_winning,
                "open_losing": open_losing,
                "open_pnl_pct": round(open_pnl, 2),
                "open_avg_pnl_pct": round(open_pnl / open_count, 2) if open_count > 0 else 0,

                # Closed trades stats
                "total_trades": total,
                "winning_trades": wins,
                "losing_trades": closed_stats['loss_count'] or 0,
                "win_rate": round((wins / total * 100), 2) if total > 0 else 0,
                "avg_profit_pct": round(float(closed_stats['avg_profit'] or 0), 2),
                "avg_win_pct": round(float(closed_stats['avg_win'] or 0), 2),
                "avg_loss_pct": round(float(closed_stats['avg_loss'] or 0), 2),
                "max_profit_pct": round(float(closed_stats['max_profit'] or 0), 2),
                "max_loss_pct": round(float(closed_stats['max_loss'] or 0), 2),
                "total_profit_pct": round(float(closed_stats['total_profit'] or 0), 2),
            }

        except Exception as e:
            return {"error": str(e)}


@router.get("/paper-trading/monthly")
async def get_monthly_performance():
    """월간 수익률"""
    with get_cursor() as cursor:
        if cursor is None:
            return {"monthly": [], "error": "Database not connected"}

        try:
            cursor.execute("""
                SELECT
                    TO_CHAR(exit_date, 'YYYY-MM') as month,
                    COUNT(*) as trades,
                    COUNT(CASE WHEN profit_pct > 0 THEN 1 END) as wins,
                    COALESCE(SUM(profit_pct), 0) as total_profit,
                    COALESCE(AVG(profit_pct), 0) as avg_profit
                FROM positions
                WHERE status = 'closed' AND exit_date IS NOT NULL
                GROUP BY TO_CHAR(exit_date, 'YYYY-MM')
                ORDER BY month DESC
                LIMIT 12
            """)
            results = cursor.fetchall()

            monthly = []
            for r in results:
                trades = r['trades'] or 0
                wins = r['wins'] or 0
                monthly.append({
                    "month": r['month'],
                    "trades": trades,
                    "wins": wins,
                    "losses": trades - wins,
                    "win_rate": round((wins / trades * 100), 2) if trades > 0 else 0,
                    "total_profit_pct": round(float(r['total_profit'] or 0), 2),
                    "avg_profit_pct": round(float(r['avg_profit'] or 0), 2),
                })

            return {
                "count": len(monthly),
                "monthly": monthly
            }
        except Exception as e:
            return {"monthly": [], "error": str(e)}
