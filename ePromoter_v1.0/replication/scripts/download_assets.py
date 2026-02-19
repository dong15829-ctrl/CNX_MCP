#!/usr/bin/env python3
"""
globalsess 대시보드 이미지/자산 다운로드.
asset_list.txt 또는 하드코딩 URL 목록을 기준으로 지정 폴더에 저장.
"""
import os
import re
import urllib.request
import urllib.parse
from pathlib import Path

# 기본 설정
BASE_URL = "https://www.globalsess.com/globaldashboard"
SCRIPT_DIR = Path(__file__).resolve().parent
REPLICATION_DIR = SCRIPT_DIR.parent
OUT_DIR = REPLICATION_DIR / "assets" / "img"
ASSET_LIST = REPLICATION_DIR / "config" / "asset_list.txt"


def safe_path(rel_path: str) -> Path:
    """상대 경로를 OUT_DIR 기준 안전 경로로."""
    p = Path(rel_path.strip())
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("Invalid path")
    return OUT_DIR / p


def download_one(url: str, out_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"  FAIL: {url} -> {e}")
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ASSET_LIST.exists():
        with open(ASSET_LIST, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    else:
        lines = [
            "img/new_logo.jpg",
            "img/login_02.png",
            "img/icon_hbg.png",
            "img/icon_user.png",
            "img/btn_down.png",
        ]
    ok = 0
    for rel in lines:
        url = urllib.parse.urljoin(BASE_URL + "/", rel)
        out_path = safe_path(rel)
        print(f"  {rel}")
        if download_one(url, out_path):
            ok += 1
    print(f"Done: {ok}/{len(lines)} saved under {OUT_DIR}")


if __name__ == "__main__":
    main()
