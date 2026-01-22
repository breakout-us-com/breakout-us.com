# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

O'Neil Breakout Trading Strategy dashboard for US stocks. Monorepo with:
- **Frontend**: Next.js 16 + React 19 + TypeScript (deployed on Vercel)
- **Backend**: FastAPI + Python 3.13 (self-hosted on Ubuntu with PM2)
- **Database**: PostgreSQL

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

### Backend Scripts
```bash
python scripts/init_db.py                    # Initialize database
python scripts/run_screener.py --max-stocks 100  # Dynamic stock screening
python scripts/run_scanner.py --source dynamic   # Run signal scanner
python scripts/run_position_manager.py       # Check/close positions
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

### Key Backend Components
- `main.py` - FastAPI app entry with lifespan management
- `routers/` - API endpoints (watchlist, signals, paper_trading, backtest)
- `scanner/background_scanner.py` - Async background scanner with scheduled screening
- `detector/breakout_detector.py` - 20-day pivot breakout detection algorithm
- `screener/dynamic_screener.py` - S&P 500 + NASDAQ 100 stock screening

### Key Frontend Components
- `src/app/page.tsx` - Main dashboard
- `src/components/` - TodaySignals, RecentSignals, WatchlistPanel, etc.
- `src/lib/config.ts` - API URL configuration

### Database Connection
Backend supports both direct PostgreSQL and SSH-tunneled connections (controlled by `USE_SSH_TUNNEL` env var). Use `with get_cursor() as cursor:` pattern.

## Time Zone Handling (Critical)

All scheduling uses **KST (UTC+9)**:
- US Regular market: 23:30-06:00 KST
- Log rotation: midnight KST
- Dynamic screening: 23:30 KST daily

Custom `KSTTimedRotatingFileHandler` in `logging_config.py` handles this.

## Environment Variables

### Backend (.env)
- `USE_SSH_TUNNEL` - true for local dev with SSH tunnel
- `DB_HOST/PORT/NAME/USER/PASSWORD` - PostgreSQL connection
- `SCANNER_ENABLED` - Enable background scanner
- `MIN_VOLUME_SURGE` - Volume surge threshold (default 50%)
- `MAX_BREAKOUT_PCT` - Max breakout % from resistance (default 5%)

### Frontend (.env.local / .env.production)
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Deployment

- **Frontend**: Auto-deploys to Vercel on push to `main`
- **Backend**: GitHub Actions deploys on changes to `backend/**` via SSH + PM2 restart

Required GitHub Secrets: `SSH_PRIVATE_KEY`, `SERVER_IP`, `SERVER_USER`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET `/api/watchlist` | Combined watchlist |
| GET `/api/signals/today` | Today's breakout signals |
| GET `/api/signals/recent?days=7` | Recent N days signals |
| GET `/api/paper-trading/positions` | Open positions |
| GET `/api/paper-trading/stats` | Trading statistics |
| GET `/health` | Health check |

## Notes

- Documentation and comments are in Korean - maintain this for consistency
- Backend uses async/await throughout - avoid blocking operations
- yfinance fetches real-time pricing - external API availability matters
- Breakout conditions: price > 20-day high, volume surge >= 50%, breakout within 0-5% of resistance
