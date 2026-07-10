-- =============================================================
-- Paper Trading 데이터 리셋
-- =============================================================
-- positions(페이퍼 트레이딩 포지션)와 alerts(시그널 기록)를 모두 비우고
-- ID 시퀀스를 1부터 다시 시작한다.
--
-- 실행 시점부터 Paper Trading Stats / Monthly Performance /
-- Trading History가 새로 쌓인다.
--
-- 주의: 실행하면 기존 시그널/포지션/청산 내역이 전부 삭제된다. 복구 불가.
--
-- 실행 방법 (서버에서):
--   psql -U <DB_USER> -d <DB_NAME> -f docs/reset_paper_trading.sql
-- =============================================================

BEGIN;

TRUNCATE TABLE positions RESTART IDENTITY;
TRUNCATE TABLE alerts RESTART IDENTITY;

COMMIT;

-- 확인용: 두 테이블 모두 0이어야 한다
SELECT
    (SELECT COUNT(*) FROM positions) AS positions_count,
    (SELECT COUNT(*) FROM alerts) AS alerts_count;
