# -*- coding: utf-8 -*-
"""
대시보드 사용자·역할 관리.
- users 테이블: id, email, password_hash, role(admin|user), is_active, created_at, updated_at
- 비밀번호는 bcrypt 해시 저장
"""
import re
from datetime import datetime

TABLE_USERS = "dashboard_users"


def _hash_password(password: str) -> str:
    try:
        import bcrypt
        # bcrypt.hashpw returns bytes
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")
    except ImportError:
        raise RuntimeError("bcrypt package required: pip install bcrypt")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def ensure_users_table(conn):
    """users 테이블이 없으면 생성."""
    with conn.cursor() as cur:
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboard_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_role (role),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e


def get_user_by_email(conn, email: str) -> dict | None:
    """이메일로 사용자 조회. 없으면 None."""
    if not email or not isinstance(email, str):
        return None
    email = email.strip().lower()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, password_hash, role, is_active, created_at, updated_at FROM dashboard_users WHERE email = %s LIMIT 1",
            (email,),
        )
        row = cur.fetchone()
    if not row:
        return None
    # is_active: 0/"0" → False, 1/"1" → True (DB 타입/드라이버 차이 대비)
    try:
        is_active = bool(int(row[4])) if row[4] is not None else False
    except (TypeError, ValueError):
        is_active = False
    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": is_active,
        "created_at": row[5],
        "updated_at": row[6],
    }


def is_user_active(conn, user_id: int) -> bool:
    """해당 사용자가 활성(승인됨)인지. is_active=1 이어야 True."""
    with conn.cursor() as cur:
        cur.execute("SELECT is_active FROM dashboard_users WHERE id = %s LIMIT 1", (user_id,))
        row = cur.fetchone()
    if not row:
        return False
    try:
        return int(row[0]) == 1
    except (TypeError, ValueError):
        return False


def get_user_by_id(conn, user_id: int) -> dict | None:
    """id로 사용자 조회."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, password_hash, role, is_active, created_at, updated_at FROM dashboard_users WHERE id = %s LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        is_active = bool(int(row[4])) if row[4] is not None else False
    except (TypeError, ValueError):
        is_active = False
    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": is_active,
        "created_at": row[5],
        "updated_at": row[6],
    }


def create_user(conn, email: str, password: str, role: str = "user", is_active: bool = True) -> dict:
    """회원가입. role은 admin|user. is_active=False면 승인 대기. 중복 이메일 시 예외."""
    email = _normalize_email(email)
    _validate_email(email)
    _validate_password(password)
    password_hash = _hash_password(password)
    role = "admin" if (role or "").strip().lower() == "admin" else "user"
    # 명시적으로 0/1 사용 (DB 기본값 영향 없도록)
    active_val = 0 if not is_active else 1
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO dashboard_users (email, password_hash, role, is_active) VALUES (%s, %s, %s, %s)",
            (email, password_hash, role, active_val),
        )
        conn.commit()
        uid = cur.lastrowid
    return {"id": uid, "email": email, "role": role, "is_active": bool(active_val)}


def list_users(conn, role_filter: str | None = None, active_only: bool = False, pending_only: bool = False, limit: int = 500, offset: int = 0) -> list[dict]:
    """사용자 목록. role_filter: admin|user|None(전체), active_only: is_active=1만, pending_only: is_active=0(승인대기)만."""
    conditions = []
    args = []
    if role_filter and role_filter.strip().lower() in ("admin", "user"):
        conditions.append("role = %s")
        args.append(role_filter.strip().lower())
    if pending_only:
        conditions.append("is_active = 0")
    elif active_only:
        conditions.append("is_active = 1")
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    args.extend([limit, offset])
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT id, email, role, is_active, created_at, updated_at FROM dashboard_users{where} ORDER BY id ASC LIMIT %s OFFSET %s",
            args,
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "email": r[1],
            "role": r[2],
            "is_active": bool(r[3]),
            "created_at": r[4].isoformat() if hasattr(r[4], "isoformat") else str(r[4]),
            "updated_at": r[5].isoformat() if hasattr(r[5], "isoformat") else str(r[5]),
        }
        for r in rows
    ]


def count_users(conn, role_filter: str | None = None, active_only: bool = False, pending_only: bool = False) -> int:
    conditions = []
    args = []
    if role_filter and role_filter.strip().lower() in ("admin", "user"):
        conditions.append("role = %s")
        args.append(role_filter.strip().lower())
    if pending_only:
        conditions.append("is_active = 0")
    elif active_only:
        conditions.append("is_active = 1")
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM dashboard_users{where}", args)
        return cur.fetchone()[0] or 0


def update_user(conn, user_id: int, *, role: str | None = None, is_active: bool | None = None, password: str | None = None) -> dict | None:
    """역할·활성·비밀번호 수정. 반환: 수정된 사용자 정보 또는 None."""
    user = get_user_by_id(conn, user_id)
    if not user:
        return None
    updates = []
    args = []
    if role is not None and role.strip().lower() in ("admin", "user"):
        updates.append("role = %s")
        args.append(role.strip().lower())
    if is_active is not None:
        updates.append("is_active = %s")
        args.append(1 if is_active else 0)
    if password is not None and password != "":
        _validate_password(password)
        updates.append("password_hash = %s")
        args.append(_hash_password(password))
    if not updates:
        return user
    args.append(user_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE dashboard_users SET {', '.join(updates)} WHERE id = %s",
            args,
        )
        conn.commit()
    return get_user_by_id(conn, user_id)


def delete_user(conn, user_id: int) -> bool:
    """사용자 삭제. 성공 시 True, 해당 id 없으면 False."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM dashboard_users WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _validate_email(email: str) -> None:
    if not email or len(email) > 255:
        raise ValueError("이메일을 입력해 주세요.")
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise ValueError("올바른 이메일 형식이 아닙니다.")


def _validate_password(password: str) -> None:
    if not password or len(password) < 6:
        raise ValueError("비밀번호는 6자 이상이어야 합니다.")
