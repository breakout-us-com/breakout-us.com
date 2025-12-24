# O'Neil Breakout - US Stock Trading Signals

미국 주식 O'Neil CAN SLIM 돌파매매 시그널 및 Paper Trading 웹사이트

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | Next.js 14, Tailwind CSS, TypeScript |
| Backend | FastAPI, Python 3.13, uvicorn (HTTPS) |
| Database | PostgreSQL |
| Hosting | Frontend: Vercel, Backend: Self-hosted |

## 배포 구조

```
┌─────────────────┐     ┌─────────────────────────────────┐
│     Vercel      │     │         Server (Ubuntu)         │
│  ┌───────────┐  │     │  ┌─────────────────────────┐   │
│  │  Next.js  │  │────▶│  │  FastAPI (uvicorn)      │   │
│  │  Frontend │  │     │  │  HTTPS :8800            │   │
│  └───────────┘  │     │  └─────────────────────────┘   │
└─────────────────┘     │  ┌─────────────────────────┐   │
                        │  │  PostgreSQL :5432       │   │
                        │  └─────────────────────────┘   │
                        └─────────────────────────────────┘
```

## 주요 기능

- **Today's Signals**: 오늘 발생한 돌파 시그널 (피벗돌파, 컵앤핸들, 베이스돌파)
- **Recent Signals**: 최근 7일간 시그널 히스토리
- **Paper Trading**: 가상 포지션 관리 및 성과 추적
- **Market Status**: 미국장 세션 표시 (프리마켓, 정규장, 애프터마켓)
- **Watchlist**: 듀얼 워치리스트
  - 고정: S&P 500 시총 상위 50개 고정 종목
  - 동적: S&P 500 + NASDAQ 100 동적 스크리닝 100개 종목
- **Backtest Results**: 과거 백테스트 결과 참조

## 설치

### 1. Backend 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 편집
```

### 2. Frontend 설정

```bash
cd frontend
npm install
```

### 3. 데이터베이스 초기화

```bash
cd backend
source venv/bin/activate
python scripts/init_db.py
```

## 실행

### 로컬 개발

```bash
./run.sh
```

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 프로덕션

| 서비스 | URL |
|--------|-----|
| Frontend | Vercel 배포 URL |
| Backend API | `https://<YOUR_DOMAIN>:8800` |

## 배포

### Frontend (Vercel)

GitHub 푸시 시 자동 배포

**Vercel 설정:**
- Root Directory: `frontend`
- Framework: Next.js
- Environment Variable: `NEXT_PUBLIC_API_URL`

### Backend (GitHub Actions)

`backend/**` 변경 시 자동 배포

**GitHub Secrets 필요:**

| Secret | 설명 |
|--------|------|
| `SSH_PRIVATE_KEY` | 서버 접속용 SSH 개인키 |
| `SERVER_IP` | 서버 IP 주소 |
| `SERVER_USER` | 서버 사용자명 |

## 동적 스크리너

S&P 500 + NASDAQ 100에서 조건에 맞는 종목을 자동 선별합니다.

### 스크리닝 조건

| 조건 | 기준 |
|------|------|
| 시가총액 | >= $500M |
| 주가 | >= $5 |
| 평균 거래량 | >= 50K |

### 수동 실행

```bash
cd backend
source venv/bin/activate
python scripts/run_screener.py --max-stocks 100
```

### Crontab 설정 (매일 자동 실행)

```bash
crontab -e
```

```
# 매일 오전 9시 (KST) 동적 스크리닝
0 9 * * * cd /var/www/breakout-us.com/backend && venv/bin/python scripts/run_screener.py >> /tmp/screener.log 2>&1
```

## 시그널 스캐너

워치리스트 종목을 스캔하여 돌파 시그널을 감지하고 DB에 저장합니다.

### 돌파 조건 (Pivot Breakout)

| 조건 | 기준 |
|------|------|
| 가격 | 20일 고점 돌파 |
| 거래량 | 평균 대비 +50% 이상 |
| 돌파폭 | 저항선 대비 0~5% |

### 수동 실행

```bash
cd backend
source venv/bin/activate

# 동적 워치리스트 스캔
python scripts/run_scanner.py --source dynamic

# 고정 워치리스트 스캔
python scripts/run_scanner.py --source fixed
```

### Crontab 설정 (정규장 중 30분마다)

```bash
crontab -e
```

```
# 미국 정규장 시간 (KST 23:30-06:00) 30분마다 스캔
30 23 * * 1-5 cd /var/www/breakout-us.com/backend && venv/bin/python scripts/run_scanner.py >> /tmp/scanner.log 2>&1
0,30 0-5 * * 2-6 cd /var/www/breakout-us.com/backend && venv/bin/python scripts/run_scanner.py >> /tmp/scanner.log 2>&1
```

## 포지션 관리 (Paper Trading)

시그널 발생 시 자동으로 포지션을 생성하고, 청산 조건을 체크합니다.

### 자동 흐름

```
run_scanner.py 실행
    ↓
시그널 감지 → alerts 테이블 저장 (시그널 기록)
    ↓
         → positions 테이블 저장 (Paper Trading 포지션 생성)
    ↓
run_position_manager.py 실행
    ↓
오픈 포지션 체크 → 청산 조건 확인 → 포지션 청산 (status='closed')
```

### 청산 조건

| 조건 | 기준 |
|------|------|
| 손절 (Stop Loss) | -8% |
| 익절 (Take Profit) | +20% |
| 최대 보유 | 30일 |

### 수동 실행

```bash
cd backend
source venv/bin/activate

# 포지션 체크 및 청산
python scripts/run_position_manager.py
```

### Crontab 설정 (정규장 중 30분마다)

```
# 포지션 관리 (스캔 후 5분 뒤 실행)
35 23 * * 1-5 cd /var/www/breakout-us.com/backend && venv/bin/python scripts/run_position_manager.py >> /tmp/position.log 2>&1
5,35 0-5 * * 2-6 cd /var/www/breakout-us.com/backend && venv/bin/python scripts/run_position_manager.py >> /tmp/position.log 2>&1
```

## 환경변수

### Backend (.env)

```bash
# Database (서버에서 직접 연결 시)
USE_SSH_TUNNEL=false
DB_HOST=localhost
DB_PORT=5432
DB_NAME=breakout_us_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Database (SSH 터널 사용 시 - 로컬 개발)
USE_SSH_TUNNEL=true
SSH_HOST=your_ssh_host
SSH_PORT=22
SSH_USER=your_user
SSH_KEY_PATH=~/.ssh/your_key

# Dynamic Watchlist Path
DYNAMIC_WATCHLIST_PATH=/var/www/breakout-us.com/watchlist.json

# Scanner Settings
MIN_VOLUME_SURGE=50.0
MAX_BREAKOUT_PCT=5.0

# Paper Trading Settings
STOP_LOSS_PCT=0.08
TAKE_PROFIT_PCT=0.20
MAX_HOLDING_DAYS=30
```

### Frontend (.env.production)

```bash
NEXT_PUBLIC_API_URL=https://<YOUR_DOMAIN>:8800
```

## 프로젝트 구조

```
breakout-us.com/
├── .github/
│   └── workflows/
│       └── deploy-backend.yml  # 백엔드 자동 배포
│
├── backend/
│   ├── main.py                 # FastAPI 앱
│   ├── logging_config.py       # 로깅 설정 (KST 1일 롤링)
│   ├── logs/                   # 로그 파일 디렉토리
│   ├── routers/
│   │   ├── watchlist.py        # 워치리스트 API
│   │   ├── signals.py          # 시그널 API
│   │   ├── paper_trading.py    # Paper Trading API
│   │   ├── backtest.py         # 백테스트 API
│   │   └── db.py               # DB 연결 관리
│   ├── scanner/
│   │   ├── background_scanner.py  # 백그라운드 스캐너
│   │   ├── signal_storage.py      # 시그널 DB 저장
│   │   └── market_status.py       # 마켓 상태 체크
│   ├── screener/
│   │   └── dynamic_screener.py # 동적 스크리너
│   ├── detector/
│   │   └── breakout_detector.py # 돌파 시그널 감지
│   ├── scripts/
│   │   ├── init_db.py          # DB 초기화
│   │   ├── run_screener.py     # 스크리너 실행
│   │   ├── run_scanner.py      # 시그널 스캐너 실행
│   │   └── run_position_manager.py  # 포지션 관리
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx        # 메인 페이지
│   │   ├── components/         # React 컴포넌트
│   │   └── lib/
│   │       ├── config.ts       # API URL 설정
│   │       └── logger.ts       # 로깅 설정 (KST 1일 롤링)
│   ├── logs/                   # 로그 파일 디렉토리
│   └── package.json
│
├── ecosystem.config.js         # PM2 설정
├── run.sh                      # 로컬 실행 스크립트
└── README.md
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/watchlist` | 모니터링 종목 목록 |
| GET | `/api/signals/today` | 오늘 시그널 |
| GET | `/api/signals/recent?days=7` | 최근 N일 시그널 |
| GET | `/api/paper-trading/positions` | 오픈 포지션 |
| GET | `/api/paper-trading/closed` | 청산 내역 |
| GET | `/api/paper-trading/stats` | 트레이딩 통계 |
| GET | `/api/paper-trading/monthly` | 월간 수익률 |
| GET | `/api/backtest/results` | 백테스트 결과 |
| GET | `/api/backtest/stats` | 백테스트 통계 |
| GET | `/health` | 헬스체크 |

## 시장 세션 (KST 기준)

| 세션 | 시간 (KST) |
|------|------------|
| 프리마켓 | 18:00 - 23:30 |
| 정규장 | 23:30 - 06:00 |
| 애프터마켓 | 06:00 - 10:00 |

## 로깅

백엔드/프론트엔드 모두 파일 로깅을 지원하며, 한국 시간(KST) 자정 기준으로 1일 롤링됩니다.

### Backend (Python)

| 로그 파일 | 내용 |
|----------|------|
| `backend/logs/api.log` | API 서버 로그 |
| `backend/logs/scanner.log` | 스캐너/시그널 로그 |

```python
from logging_config import setup_logging

logger = setup_logging("scanner")
logger.info("Scan started")
```

### Frontend (Next.js)

| 로그 파일 | 내용 |
|----------|------|
| `frontend/logs/frontend-YYYY-MM-DD.log` | 서버사이드 로그 |

```typescript
import logger from '@/lib/logger';

logger.info('Request received');
```

### 로그 보관

- 최대 30일간 보관
- 롤링 시 `scanner.log.2025-12-24` 형식으로 백업

## 트레이딩 규칙

- **손절**: -8%
- **익절**: +20%
- **최대 보유**: 30일
- **포지션 크기**: 포트폴리오의 20% 이하
