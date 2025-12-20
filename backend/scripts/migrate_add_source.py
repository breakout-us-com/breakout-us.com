"""alerts 테이블에 source 컬럼 추가 마이그레이션"""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import psycopg2
from sshtunnel import SSHTunnelForwarder


def main():
    print("=" * 50)
    print("Migration: Add 'source' column to alerts table")
    print("=" * 50)

    # 환경변수
    ssh_host = os.environ.get('SSH_HOST', '')
    ssh_port = int(os.environ.get('SSH_PORT', '22'))
    ssh_user = os.environ.get('SSH_USER', '')
    ssh_key_path = os.path.expanduser(os.environ.get('SSH_KEY_PATH', '~/.ssh/id_rsa'))
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    db_name = os.environ.get('DB_NAME', '')
    db_user = os.environ.get('DB_USER', '')
    db_password = os.environ.get('DB_PASSWORD', '')

    # SSH 터널
    print("\n[1] SSH 터널 연결...")
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
    print("\n[2] PostgreSQL 연결...")
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

    # 마이그레이션 실행
    print("\n[3] 마이그레이션 실행...")
    try:
        with conn.cursor() as cur:
            # source 컬럼 존재 여부 확인
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'alerts' AND column_name = 'source'
            """)
            if cur.fetchone():
                print("  ℹ️  'source' 컬럼이 이미 존재합니다.")
            else:
                # source 컬럼 추가
                cur.execute("""
                    ALTER TABLE alerts
                    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'oneil'
                """)
                print("  ✅ 'source' 컬럼 추가 완료!")

            # 기존 UNIQUE 제약조건 삭제 (있으면)
            cur.execute("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'alerts' AND constraint_type = 'UNIQUE'
            """)
            constraints = cur.fetchall()
            for (constraint_name,) in constraints:
                print(f"  🔄 기존 UNIQUE 제약조건 삭제: {constraint_name}")
                cur.execute(f"ALTER TABLE alerts DROP CONSTRAINT IF EXISTS {constraint_name}")

            # 새 UNIQUE 제약조건 추가
            cur.execute("""
                ALTER TABLE alerts
                ADD CONSTRAINT alerts_ticker_pattern_source_date_unique
                UNIQUE (ticker, pattern, source, alert_date)
            """)
            print("  ✅ 새 UNIQUE 제약조건 추가 완료!")

            # source 인덱스 추가
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_source ON alerts(source)")
            print("  ✅ 'source' 인덱스 추가 완료!")

            conn.commit()
    except Exception as e:
        print(f"  ❌ 마이그레이션 실패: {e}")
        conn.rollback()

    # 연결 종료
    conn.close()
    tunnel.stop()

    print("\n" + "=" * 50)
    print("✅ 마이그레이션 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
