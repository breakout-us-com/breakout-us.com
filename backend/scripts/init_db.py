"""데이터베이스 초기화 스크립트"""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2
from psycopg2.extras import RealDictCursor
from sshtunnel import SSHTunnelForwarder

def main():
    print("=" * 50)
    print("Database Connection Test & Initialization")
    print("=" * 50)

    # 환경변수 확인
    print("\n[1] 환경변수 확인")
    ssh_host = os.environ.get('SSH_HOST', '')
    ssh_port = int(os.environ.get('SSH_PORT', '22'))
    ssh_user = os.environ.get('SSH_USER', '')
    ssh_key_path = os.path.expanduser(os.environ.get('SSH_KEY_PATH', '~/.ssh/id_rsa'))
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    db_name = os.environ.get('DB_NAME', '')
    db_user = os.environ.get('DB_USER', '')
    db_password = os.environ.get('DB_PASSWORD', '')

    print(f"  SSH_HOST: {ssh_host}")
    print(f"  SSH_USER: {ssh_user}")
    print(f"  DB_NAME: {db_name}")
    print(f"  DB_USER: {db_user}")

    # SSH 터널 시작
    print("\n[2] SSH 터널 연결...")
    try:
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_pkey=ssh_key_path,
            remote_bind_address=(db_host, db_port),
            local_bind_address=('127.0.0.1', 0),
        )
        tunnel.start()
        print(f"  ✅ SSH 터널 연결 성공! (로컬 포트: {tunnel.local_bind_port})")
    except Exception as e:
        print(f"  ❌ SSH 터널 연결 실패: {e}")
        return

    # PostgreSQL 연결
    print("\n[3] PostgreSQL 연결...")
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=tunnel.local_bind_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        print("  ✅ PostgreSQL 연결 성공!")
    except Exception as e:
        print(f"  ❌ PostgreSQL 연결 실패: {e}")
        tunnel.stop()
        return

    # 연결 테스트
    print("\n[4] 연결 테스트...")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT version()")
            result = cur.fetchone()
            print(f"  {result['version'][:60]}...")
    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")

    # 테이블 생성
    print("\n[5] 테이블 생성...")
    try:
        with conn.cursor() as cur:
            # positions 테이블 (Paper Trading용)
            # - us-dynamic: positions + trades 분리
            # - us-oneil-simple: positions에 status로 통합
            # - 취합: positions에 source 추가, status로 open/closed 관리
            # - 자금 기반: quantity, investment_amount 추가
            cur.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    market VARCHAR(10) NOT NULL DEFAULT 'US',
                    source VARCHAR(20) NOT NULL DEFAULT 'dynamic',
                    entry_price DECIMAL(15, 4) NOT NULL,
                    quantity DECIMAL(15, 4),
                    investment_amount DECIMAL(15, 2),
                    entry_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    pattern VARCHAR(50) NOT NULL,
                    stop_loss DECIMAL(15, 4),
                    take_profit DECIMAL(15, 4),
                    signal_data JSONB,
                    status VARCHAR(20) NOT NULL DEFAULT 'open',
                    exit_price DECIMAL(15, 4),
                    exit_date TIMESTAMP,
                    exit_reason VARCHAR(100),
                    profit_pct DECIMAL(10, 4),
                    profit_amount DECIMAL(15, 2),
                    holding_days INTEGER,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # positions 인덱스
            cur.execute("CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_positions_source ON positions(source)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_positions_entry_date ON positions(entry_date)")

            # alerts 테이블 (시그널 기록용)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20) NOT NULL,
                    market VARCHAR(10) NOT NULL DEFAULT 'US',
                    pattern VARCHAR(50) NOT NULL,
                    source VARCHAR(20) NOT NULL DEFAULT 'dynamic',
                    alert_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    alert_price DECIMAL(15, 4) NOT NULL,
                    signal_data JSONB,
                    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, pattern, source, alert_date)
                )
            """)

            # alerts 인덱스
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ticker ON alerts(ticker)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_source ON alerts(source)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_alert_date ON alerts(alert_date)")

            conn.commit()
        print("  ✅ 테이블 생성 완료!")
    except Exception as e:
        print(f"  ❌ 테이블 생성 실패: {e}")
        conn.rollback()

    # 테이블 확인
    print("\n[6] 테이블 확인...")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            for t in tables:
                print(f"  ✓ {t['table_name']}")
    except Exception as e:
        print(f"  ❌ 테이블 확인 실패: {e}")

    # 연결 종료
    conn.close()
    tunnel.stop()

    print("\n" + "=" * 50)
    print("✅ 초기화 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()
