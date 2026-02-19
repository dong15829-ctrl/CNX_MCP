#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
원격 MySQL → 로컬 MySQL 동기화.
업데이트 여부를 테이블별 행 수로 체크하고, 차이 있을 때만 해당 테이블 복사.
사용: .venv/bin/python scripts/sync_remote_to_local.py [--force]
"""
import os
import sys
import argparse

# 프로젝트 루트
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# .env 로드
_env = os.path.join(ROOT, ".env")
if os.path.isfile(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().replace('"', "").replace("'", ""))

# 테이블명 (db.py와 동일)
TABLE_B2B = os.environ.get("TABLE_B2B", "reportbusiness_es_old_v2")
TABLE_B2C = os.environ.get("TABLE_B2C", "report_es_old")
TABLES = [TABLE_B2B, TABLE_B2C]


def get_remote_conn():
    import pymysql
    return pymysql.connect(
        host=os.environ.get("REMOTE_MYSQL_HOST", os.environ.get("MYSQL_HOST", "mysql.cnxkr.com")),
        port=int(os.environ.get("REMOTE_MYSQL_PORT", os.environ.get("MYSQL_PORT", "10080"))),
        user=os.environ.get("REMOTE_MYSQL_USER", os.environ.get("MYSQL_USER", "lg_ha")),
        password=os.environ.get("REMOTE_MYSQL_PASSWORD", os.environ.get("MYSQL_PASSWORD", "")),
        database=os.environ.get("REMOTE_MYSQL_DATABASE", os.environ.get("MYSQL_DATABASE", "lg_ha")),
        charset="utf8mb4",
    )


def get_local_conn():
    import pymysql
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "lg_ha"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "lg_ha"),
        charset="utf8mb4",
    )


def table_count(conn, table):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        return cur.fetchone()[0]


def table_exists(conn, table):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s", (table,))
        return cur.fetchone() is not None


def sync_table(remote_conn, local_conn, table):
    """원격 테이블 전체를 읽어 로컬에 TRUNCATE + INSERT."""
    with remote_conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{table}`")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    if not rows:
        with local_conn.cursor() as c:
            c.execute(f"TRUNCATE TABLE `{table}`")
        local_conn.commit()
        print(f"  {table}: 0 rows (truncated)")
        return 0
    placeholders = ",".join(["%s"] * len(cols))
    col_list = ",".join(f"`{c}`" for c in cols)
    sql = f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"
    with local_conn.cursor() as c:
        c.execute(f"TRUNCATE TABLE `{table}`")
        c.executemany(sql, rows)
    local_conn.commit()
    print(f"  {table}: {len(rows)} rows synced")
    return len(rows)


def _mysql_type_from_desc(desc):
    """cursor.description 한 컬럼으로 MySQL 타입 문자열 추정 (VIEW/테이블 공통)."""
    import pymysql
    name, type_code = desc[0], desc[1]
    if type_code in (pymysql.constants.FIELD_TYPE.TINY, pymysql.constants.FIELD_TYPE.SHORT,
                     pymysql.constants.FIELD_TYPE.LONG, pymysql.constants.FIELD_TYPE.LONGLONG,
                     pymysql.constants.FIELD_TYPE.INT24):
        return "BIGINT"
    if type_code in (pymysql.constants.FIELD_TYPE.FLOAT, pymysql.constants.FIELD_TYPE.DOUBLE,
                     pymysql.constants.FIELD_TYPE.DECIMAL, pymysql.constants.FIELD_TYPE.NEWDECIMAL):
        return "DOUBLE"
    if type_code in (pymysql.constants.FIELD_TYPE.DATE, pymysql.constants.FIELD_TYPE.DATETIME,
                     pymysql.constants.FIELD_TYPE.TIMESTAMP):
        return "DATETIME"
    return "TEXT"


def ensure_local_table(local_conn, remote_conn, table):
    """로컬에 테이블이 없으면 원격 SELECT 결과 구조로 CREATE TABLE (VIEW 대응)."""
    if table_exists(local_conn, table):
        return
    with remote_conn.cursor() as cur:
        cur.execute(f"SELECT * FROM `{table}` LIMIT 0")
        desc = cur.description
    if not desc:
        raise RuntimeError(f"Could not get columns for {table}")
    cols = []
    for d in desc:
        name, type_code = d[0], d[1]
        try:
            typ = _mysql_type_from_desc(d)
        except Exception:
            typ = "TEXT"
        cols.append(f"`{name}` {typ}")
    create_sql = f"CREATE TABLE `{table}` (" + ", ".join(cols) + ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    with local_conn.cursor() as c:
        c.execute(create_sql)
    local_conn.commit()
    print(f"  {table}: created from remote structure ({len(cols)} columns)")


def main():
    parser = argparse.ArgumentParser(description="Sync remote MySQL tables to local MySQL.")
    parser.add_argument("--force", action="store_true", help="Skip count check, sync all tables.")
    args = parser.parse_args()

    remote_password = os.environ.get("REMOTE_MYSQL_PASSWORD", os.environ.get("MYSQL_PASSWORD", ""))
    local_password = os.environ.get("MYSQL_PASSWORD", "")
    if not remote_password and not local_password:
        print("Set REMOTE_MYSQL_* and MYSQL_* (or MYSQL_*) in .env", file=sys.stderr)
        sys.exit(1)

    print("Connecting to remote and local MySQL...")
    remote_conn = get_remote_conn()
    local_conn = get_local_conn()

    try:
        for table in TABLES:
            if not table_exists(remote_conn, table):
                print(f"  {table}: skip (not found on remote)")
                continue
            ensure_local_table(local_conn, remote_conn, table)
            if not args.force:
                try:
                    rc = table_count(remote_conn, table)
                    lc = table_count(local_conn, table)
                    if rc == lc:
                        print(f"  {table}: up to date ({rc} rows)")
                        continue
                except Exception as e:
                    print(f"  {table}: count check failed ({e}), syncing anyway")
            sync_table(remote_conn, local_conn, table)
    finally:
        remote_conn.close()
        local_conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
