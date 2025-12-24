import sys
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import watchlist, backtest, signals, paper_trading
from routers.db import close_db_connection
from scanner import get_scanner
from logging_config import setup_logging

# Setup logging for API
logger = setup_logging("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting O'Neil Breakout API server...")
    scanner = get_scanner()
    await scanner.start()
    logger.info("API server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    await scanner.stop()
    close_db_connection()
    logger.info("API server shutdown complete")


app = FastAPI(
    title="O'Neil Breakout API",
    description="미국장 O'Neil Breakout 전략 및 백테스트 결과 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://breakout-uscom.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(watchlist.router, prefix="/api", tags=["Watchlist"])
app.include_router(backtest.router, prefix="/api", tags=["Backtest"])
app.include_router(signals.router, prefix="/api", tags=["Signals"])
app.include_router(paper_trading.router, prefix="/api", tags=["Paper Trading"])


@app.get("/")
async def root():
    return {"message": "O'Neil Breakout API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
