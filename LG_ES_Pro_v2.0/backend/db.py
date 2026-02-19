# -*- coding: utf-8 -*-
"""MySQL 연결. 환경 변수 기반."""
import os

MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql.cnxkr.com")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "10080"))
MYSQL_USER = os.environ.get("MYSQL_USER", "lg_ha")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "lg_ha")

TABLE_B2B = "reportbusiness_es_old_v2"
TABLE_B2C = "report_es_old"


def is_db_configured() -> bool:
    return bool(os.environ.get("MYSQL_PASSWORD", "").strip())


def get_connection():
    try:
        import pymysql
        return pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
            password=MYSQL_PASSWORD, database=MYSQL_DATABASE, charset="utf8mb4",
        )
    except ImportError:
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
            )
        except ImportError:
            raise RuntimeError("pymysql 또는 mysql-connector-python 설치 필요")
