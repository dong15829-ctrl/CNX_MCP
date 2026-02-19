import os
import socket
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.db.connection import get_db_connection
from src.config import DB_HOST, DB_PORT
import logging

def check_port_reachable(host, port, timeout_seconds=5):
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            print(f"[OK] TCP reachable: {host}:{port}")
            return True
    except OSError as e:
        print(f"[ERROR] TCP unreachable: {host}:{port} ({e})")
        return False

def verify_tables():
    conn = None
    try:
        if not check_port_reachable(DB_HOST, DB_PORT):
            print("[HINT] Check firewall/IP allowlist or network access.")
            return

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check report_es
            print("\n--- Checking report_es ---")
            cursor.execute("SELECT * FROM report_es LIMIT 2")
            rows = cursor.fetchall()
            if rows:
                print(f"Success! Retrieved {len(rows)} rows.")
                print("Sample Data:", rows[0])
            else:
                print("Table 'report_es' is empty or accessible but yielded no rows.")
            
            # Check reportbusiness_es
            print("\n--- Checking reportbusiness_es ---")
            cursor.execute("SELECT * FROM reportbusiness_es LIMIT 2")
            rows = cursor.fetchall()
            if rows:
                print(f"Success! Retrieved {len(rows)} rows.")
                print("Sample Data:", rows[0])
            else:
                print("Table 'reportbusiness_es' is empty or accessible but yielded no rows.")

    except Exception as e:
        print(f"\n[CRITICAL] Tests failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_tables()
