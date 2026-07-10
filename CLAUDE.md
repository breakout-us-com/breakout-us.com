# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

O'Neil Breakout Trading Strategy dashboard for US stocks. Monorepo with:
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind 4 (deployed on Vercel)
- **Backend**: FastAPI + Python 3.13 (self-hosted on Ubuntu with PM2)
- **Database**: PostgreSQL

There is no test suite in this repo.

## Common Commands

### Frontend (in `/frontend`)
```bash
npm run dev      # Dev server at http://localhost:3000
npm run build    # Production build
npm run lint     # ESLint
```

### Backend (in `/backend`)
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000  # API at http://localhost:8000/docs
```

### Quick Start (both services)
```bash
./run.sh
```

### Backend Scripts (in `/backend`, venv activated)
```bash
python scripts/init_db.py                        # Initialize database
python scripts/run_screener.py --max-stocks 100  # Dynamic stock screening
python scripts/run_scanner.py --source dynamic   # Signal scan (--source fixed|dynamic)
python scripts/run_position_manager.py           # Check/close open positions
```

## Architecture

### Signal Detection Flow
```
BackgroundScanner (30min interval during market hours)
    ↓
BreakoutDetector analyzes watchlist stocks
    ↓
Signal detected → saves to `alerts` table
    ↓
Auto-creates paper trading position in `positions` table
    ↓
PositionManager checks exit conditions (stop loss -8%, take profit +20%, max 30 days)
```

Scanning runs two ways: the in-process `BackgroundScanner` (started via FastAPI lifespan in `main.py`) and the standalone `scripts/run_scanner.py` / `run_position_manager.py`, which the production server also runs via crontab. Both write to the same tables.

### Dual Watchlist
- **Fixed**: `ONEIL_WATCHLIST` dict hardcoded in `routers/watchlist.py`
- **Dynamic**: `watchlist.json` written by the screener (path from `DYNAMIC_WATCHLIST_PATH`), refreshed daily at 23:30 KST from S&P 500 + NASDAQ 100

The scanner scans the deduplicated union of both.

### Key Backend Components
- `main.py` - FastAPI app entry with lifespan management (starts/stops scanner, closes DB)
- `routers/` - API endpoints (watchlist, signals, paper_trading, backtest) + `db.py` connection management
- `scanner/background_scanner.py` - Async background scanner with scheduled screening
- `scanner/signal_storage.py` - Saves signals to `alerts` and auto-creates `positions`
- `detector/breakout_detector.py` - 20-day pivot breakout detection algorithm
- `screener/dynamic_screener.py` - S&P 500 + NASDAQ 100 stock screening

### Key Frontend Components
- `src/app/page.tsx` - Main dashboard
- `src/components/` - TodaySignals, RecentSignals, CurrentPositions, TradingHistory, etc.
- `src/lib/config.ts` - `API_URL` from `NEXT_PUBLIC_API_URL` (falls back to localhost:8000)

### Database Connection
`routers/db.py` keeps a module-level singleton connection, optionally through an SSH tunnel (`USE_SSH_TUNNEL` env var; tunnel for local dev, direct on the server). Always use the `with get_cursor() as cursor:` pattern — it commits on success and rolls back on exception. The cursor is a `RealDictCursor` (rows are dicts).

## Time Zone Handling (Critical)

All scheduling uses **KST (UTC+9)**:
- US Regular market: 23:30-06:00 KST
- Log rotation: midnight KST
- Dynamic screening: 23:30 KST daily

Custom `KSTTimedRotatingFileHandler` in `logging_config.py` handles this.

## Logging

Both sides log to files with KST midnight rotation, 30-day retention:
- Backend: `logger = setup_logging("scanner")` from `logging_config.py` → `backend/logs/*.log`
- Frontend (server-side): `import logger from '@/lib/logger'` (winston) → `frontend/logs/`

## Environment Variables

### Backend (.env — see .env.example)
- `USE_SSH_TUNNEL` - SSH tunnel for DB (default: true; set false for direct connection on server)
- `DB_HOST/PORT/NAME/USER/PASSWORD` - PostgreSQL connection
- `SSH_HOST/PORT/USER/KEY_PATH` - SSH tunnel settings (required if USE_SSH_TUNNEL=true)
- `DYNAMIC_WATCHLIST_PATH` - Path to dynamic watchlist JSON
- `SCANNER_ENABLED` - Enable background scanner (default: true)
- `SCAN_INTERVAL_SECONDS` - Scan interval (default: 1800)
- `MIN_VOLUME_SURGE` - Volume surge threshold (default: 50.0 = +50%)
- `MAX_BREAKOUT_PCT` - Max breakout % above resistance (default: 5.0)
- `INITIAL_CAPITAL` - Paper trading initial capital (default: 100000)
- `POSITION_SIZE_PCT` - Position size as **fraction** of capital (default: 0.20, not 20)
- `STOP_LOSS_PCT` / `TAKE_PROFIT_PCT` - Exit thresholds as **fractions** (defaults: 0.08 / 0.20)
- `MAX_HOLDING_DAYS` - Max position holding period (default: 30)

### Frontend (.env.local / .env.production)
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Deployment

- **Frontend**: Auto-deploys to Vercel on push to `main`
- **Backend**: GitHub Actions (`.github/workflows/deploy-backend.yml`) deploys on changes to `backend/**` or `ecosystem.config.js`: SSH to server, `git reset --hard origin/main` in `/var/www/breakout-us.com`, pip install, `pm2 restart breakout-backend`
- Production backend runs under PM2 (`ecosystem.config.js`) with uvicorn on **port 8800 with HTTPS** (SSL certs on server); local dev uses port 8000 plain HTTP

Required GitHub Secrets: `SSH_PRIVATE_KEY`, `SERVER_IP`, `SERVER_USER`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/watchlist` | Combined watchlist |
| GET `/api/signals/today` | Today's breakout signals |
| GET `/api/signals/recent?days=7` | Recent N days signals |
| GET `/api/paper-trading/positions` | Open positions with unrealized P&L |
| GET `/api/paper-trading/closed` | Closed positions (trading history) |
| GET `/api/paper-trading/stats` | Trading statistics |
| GET `/api/paper-trading/monthly` | Monthly performance |
| GET `/api/backtest/results` | Backtest results |
| GET `/api/backtest/stats` | Backtest statistics |
| GET `/health` | Health check |

## Portfolio Return Calculation

Returns are calculated as **portfolio return** (not sum of trade percentages):
```
Realized P&L = investment_amount × profit_pct / 100
Portfolio Return = Total Realized P&L / INITIAL_CAPITAL × 100
```
Example: 5 trades × $20,000 × +10% avg = $10,000 profit → **+10%** portfolio return

## Notes

- Documentation and comments are in Korean - maintain this for consistency
- Backend uses async/await throughout - avoid blocking operations
- yfinance fetches real-time pricing - external API availability matters
- Breakout conditions: price > 20-day high, volume surge >= 50%, breakout within 0-5% of resistance
- README.md still says Next.js 14; the codebase is on Next.js 16