# -*- coding: utf-8 -*-
"""사용자 인증·관리. dashboard_users 테이블."""
import re
from datetime import datetime

TABLE_USERS = "dashboard_users"


def _hash_password(password: str) -> str:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.verify(plain, hashed)
    except Exception:
        return False


def ensure_users_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin','user') NOT NULL DEFAULT 'user',
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email), INDEX idx_role (role), INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()


def get_user_by_email(conn, email: str) -> dict | None:
    if not email:
        return None
    email = email.strip().lower()
    with conn.cursor() as cur:
        cur.execute("SELECT id,email,password_hash,role,is_active,created_at,updated_at FROM dashboard_users WHERE email=%s LIMIT 1", (email,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        is_active = bool(int(row[4])) if row[4] is not None else False
    except (TypeError, ValueError):
        is_active = False
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3], "is_active": is_active, "created_at": row[5], "updated_at": row[6]}


def is_user_active(conn, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT is_active FROM dashboard_users WHERE id=%s LIMIT 1", (user_id,))
        row = cur.fetchone()
    if not row:
        return False
    try:
        return int(row[0]) == 1
    except (TypeError, ValueError):
        return False


def get_user_by_id(conn, user_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id,email,password_hash,role,is_active,created_at,updated_at FROM dashboard_users WHERE id=%s LIMIT 1", (user_id,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        is_active = bool(int(row[4])) if row[4] is not None else False
    except (TypeError, ValueError):
        is_active = False
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3], "is_active": is_active, "created_at": row[5], "updated_at": row[6]}


def create_user(conn, email: str, password: str, role: str = "user", is_active: bool = True) -> dict:
    email = (email or "").strip().lower()
    if not email or len(email) > 255:
        raise ValueError("이메일을 입력해 주세요.")
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise ValueError("올바른 이메일 형식이 아닙니다.")
    if not password or len(password) < 6:
        raise ValueError("비밀번호는 6자 이상이어야 합니다.")
    password_hash = _hash_password(password)
    role = "admin" if (role or "").strip().lower() == "admin" else "user"
    active_val = 1 if is_active else 0
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dashboard_users (email,password_hash,role,is_active) VALUES (%s,%s,%s,%s)", (email, password_hash, role, active_val))
        conn.commit()
        uid = cur.lastrowid
    return {"id": uid, "email": email, "role": role, "is_active": bool(active_val)}


def list_users(conn, role_filter=None, active_only=False, pending_only=False, limit=500, offset=0):
    conds, args = [], []
    if role_filter and role_filter.strip().lower() in ("admin", "user"):
        conds.append("role=%s"); args.append(role_filter.strip().lower())
    if pending_only:
        conds.append("is_active=0")
    elif active_only:
        conds.append("is_active=1")
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    args.extend([limit, offset])
    with conn.cursor() as cur:
        cur.execute(f"SELECT id,email,role,is_active,created_at,updated_at FROM dashboard_users{where} ORDER BY id ASC LIMIT %s OFFSET %s", args)
        rows = cur.fetchall()
    return [{"id": r[0], "email": r[1], "role": r[2], "is_active": bool(r[3]), "created_at": r[4].isoformat() if hasattr(r[4], "isoformat") else str(r[4]), "updated_at": r[5].isoformat() if hasattr(r[5], "isoformat") else str(r[5])} for r in rows]


def count_users(conn, role_filter=None, active_only=False, pending_only=False):
    conds, args = [], []
    if role_filter and role_filter.strip().lower() in ("admin", "user"):
        conds.append("role=%s"); args.append(role_filter.strip().lower())
    if pending_only:
        conds.append("is_active=0")
    elif active_only:
        conds.append("is_active=1")
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM dashboard_users{where}", args)
        return cur.fetchone()[0] or 0


def update_user(conn, user_id, *, role=None, is_active=None, password=None):
    user = get_user_by_id(conn, user_id)
    if not user:
        return None
    updates, args = [], []
    if role is not None and role.strip().lower() in ("admin", "user"):
        updates.append("role=%s"); args.append(role.strip().lower())
    if is_active is not None:
        updates.append("is_active=%s"); args.append(1 if is_active else 0)
    if password:
        if len(password) < 6:
            raise ValueError("비밀번호는 6자 이상이어야 합니다.")
        updates.append("password_hash=%s"); args.append(_hash_password(password))
    if not updates:
        return user
    args.append(user_id)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE dashboard_users SET {', '.join(updates)} WHERE id=%s", args)
        conn.commit()
    return get_user_by_id(conn, user_id)


def delete_user(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM dashboard_users WHERE id=%s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
