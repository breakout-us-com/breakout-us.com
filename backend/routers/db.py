"""데이터베이스 연결 관리"""
import os
from pathlib import Path
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")


_tunnel = None
_connection = None


def get_db_config():
    """환경변수에서 DB 설정 반환"""
    return {
        'ssh_host': os.environ.get('SSH_HOST', ''),
        'ssh_port': int(os.environ.get('SSH_PORT', '22')),
        'ssh_user': os.environ.get('SSH_USER', ''),
        'ssh_key_path': os.path.expanduser(os.environ.get('SSH_KEY_PATH', '~/.ssh/id_rsa')),
        'db_host': os.environ.get('DB_HOST', 'localhost'),
        'db_port': int(os.environ.get('DB_PORT', '5432')),
        'db_name': os.environ.get('DB_NAME', ''),
        'db_user': os.environ.get('DB_USER', ''),
        'db_password': os.environ.get('DB_PASSWORD', ''),
    }


def init_db_connection():
    """SSH 터널 및 DB 연결 초기화"""
    global _tunnel, _connection

    config = get_db_config()
    use_ssh_tunnel = os.environ.get('USE_SSH_TUNNEL', 'true').lower() == 'true'

    if not config['db_name']:
        print("Warning: DB configuration incomplete")
        return None

    try:
        if use_ssh_tunnel:
            if not config['ssh_host']:
                print("Warning: SSH_HOST not configured for tunnel")
                return None

            # SSH 터널 시작
            _tunnel = SSHTunnelForwarder(
                (config['ssh_host'], config['ssh_port']),
                ssh_username=config['ssh_user'],
                ssh_pkey=config['ssh_key_path'],
                remote_bind_address=(config['db_host'], config['db_port']),
                local_bind_address=('127.0.0.1', 0),
            )
            _tunnel.start()
            print(f"SSH tunnel connected (local port: {_tunnel.local_bind_port})")
            db_port = _tunnel.local_bind_port
        else:
            # 직접 연결 (서버에서 로컬 DB 접속)
            print("Direct DB connection (no SSH tunnel)")
            db_port = config['db_port']

        # PostgreSQL 연결
        _connection = psycopg2.connect(
            host='127.0.0.1',
            port=db_port,
            database=config['db_name'],
            user=config['db_user'],
            password=config['db_password'],
        )
        _connection.autocommit = False
        print("PostgreSQL connected successfully")

        return _connection

    except Exception as e:
        print(f"Database connection failed: {e}")
        close_db_connection()
        return None


def get_db_connection():
    """현재 DB 연결 반환 (없으면 초기화)"""
    global _connection

    if _connection is None or _connection.closed:
        init_db_connection()

    return _connection


def close_db_connection():
    """데이터베이스 연결 종료"""
    global _tunnel, _connection

    if _connection is not None:
        try:
            _connection.close()
        except:
            pass
        _connection = None

    if _tunnel is not None:
        try:
            _tunnel.stop()
        except:
            pass
        _tunnel = None


@contextmanager
def get_cursor():
    """DB 커서 컨텍스트 매니저"""
    conn = get_db_connection()
    if conn is None:
        yield None
        return

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def is_connected():
    """DB 연결 상태 확인"""
    global _connection
    return _connection is not None and not _connection.closed
