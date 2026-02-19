#!/usr/bin/env python3
"""
globalsess.com globaldashboard 로그인 후 메뉴/기능 추출.
ePromoter_v1.0 전용. Playwright 사용. 실행: pip install playwright && playwright install chromium
"""
from playwright.sync_api import sync_playwright, expect
import re
import json
import os

URL = "http://www.globalsess.com/globaldashboard/"
EMAIL = "dongil.kim@concentrix.com"
PASSWORD = "Ssgdb001!"

# 스크립트 위치 기준 출력 경로 (ePromoter_v1.0 폴더)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def extract_texts(el):
    """요소 내 텍스트만 수집 (공백 정리)."""
    if el is None:
        return []
    text = (el.inner_text() or "").strip()
    return [t.strip() for t in text.split("\n") if t.strip()]


def extract_menu_and_features(page):
    """대시보드 페이지에서 메뉴·기능 구조 추출."""
    result = {"menus": [], "links": [], "headings": [], "buttons": [], "sections": []}

    # 네비게이션 / 사이드바: nav, aside, [role=navigation], .sidebar, .menu, .nav
    for selector in [
        "nav a",
        "aside a",
        "[role='navigation'] a",
        ".sidebar a",
        ".menu a",
        ".nav a",
        ".navbar a",
        "header a",
        "[class*='menu'] a",
        "[class*='sidebar'] a",
        "[class*='nav'] a",
    ]:
        try:
            for el in page.query_selector_all(selector):
                href = el.get_attribute("href") or ""
                text = (el.inner_text() or "").strip()
                if text and (href or text):
                    item = {"text": text, "href": href}
                    if item not in result["menus"]:
                        result["menus"].append(item)
        except Exception:
            pass

    # 메인 링크 (중복 제거용 set)
    seen_links = set()
    for a in page.query_selector_all("a[href]"):
        try:
            text = (a.inner_text() or "").strip()
            href = (a.get_attribute("href") or "").strip()
            if not href or href.startswith("#") or len(text) > 100:
                continue
            key = (text[:80], href[:200])
            if key not in seen_links:
                seen_links.add(key)
                result["links"].append({"text": text[:100], "href": href[:200]})
        except Exception:
            pass

    # 헤딩
    for tag in ["h1", "h2", "h3", "h4"]:
        for el in page.query_selector_all(tag):
            try:
                t = (el.inner_text() or "").strip()
                if t:
                    result["headings"].append({"tag": tag, "text": t})
            except Exception:
                pass

    # 버튼
    for el in page.query_selector_all("button, [role='button'], input[type='submit'], .btn"):
        try:
            t = (el.inner_text() or el.get_attribute("value") or "").strip()
            if t and len(t) < 100:
                result["buttons"].append(t)
        except Exception:
            pass

    # 섹션/카드 제목
    for sel in [".card-title", ".section-title", "[class*='title']", ".panel-title"]:
        try:
            for el in page.query_selector_all(sel):
                t = (el.inner_text() or "").strip()
                if t and len(t) < 150:
                    result["sections"].append(t)
        except Exception:
            pass

    return result


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        try:
            page.goto(URL, wait_until="networkidle", timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500)

            # 로그인 폼: 이 사이트는 #user_id, #user_pw 사용
            email_input = page.query_selector("#user_id, input[name='id'], input[type='email']")
            password_input = page.query_selector("#user_pw, input[name='user_pw'], input[type='password']")

            if email_input and password_input:
                email_input.fill(EMAIL)
                password_input.fill(PASSWORD)
                # 로그인 버튼 클릭 (javascript:login() 호출)
                submit = page.query_selector("a.login_btn_img, a[href='javascript:login()']")
                if submit:
                    submit.click()
                else:
                    page.keyboard.press("Enter")
                # AJAX 로그인 후 /globaldashboard/main 으로 이동 대기
                page.wait_for_url("**/main**", timeout=15000)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(4000)
            else:
                print("로그인 폼을 찾지 못했습니다.")
                if not email_input:
                    print("  - ID 입력 필드 없음")
                if not password_input:
                    print("  - 비밀번호 입력 필드 없음")

            # 메인 대시보드에서 메뉴/기능 추출
            data = extract_menu_and_features(page)
            data["current_url"] = page.url
            data["page_title"] = page.title()

            # Executive Summary 페이지로 이동해 추가 헤딩·섹션 수집
            try:
                page.goto("https://www.globalsess.com/globaldashboard/executiveSummary", wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(3000)
                sub = extract_menu_and_features(page)
                data["headings"] = sub["headings"]
                data["sections"] = sub["sections"]
                data["buttons"] = sub["buttons"]
                if sub["links"]:
                    data["executive_links"] = sub["links"][:30]
            except Exception:
                pass

            # 마크다운 리포트 출력
            print("\n# GlobalSess 대시보드 메뉴·기능 정리\n")
            print(f"- **페이지 제목:** {data['page_title']}")
            print(f"- **현재 URL:** {data['current_url']}\n")

            if data["menus"]:
                print("## 메뉴 (네비게이션/사이드바)\n")
                for m in data["menus"][:50]:
                    print(f"- {m['text']}  \n  `{m['href']}`")
                if len(data["menus"]) > 50:
                    print(f"\n... 외 {len(data['menus']) - 50}개\n")

            if data["headings"]:
                print("\n## 헤딩\n")
                for h in data["headings"][:30]:
                    print(f"- **{h['tag']}** {h['text']}")

            if data["sections"]:
                print("\n## 섹션/카드 제목\n")
                seen = set()
                for s in data["sections"][:30]:
                    if s not in seen:
                        seen.add(s)
                        print(f"- {s}")

            if data["buttons"]:
                print("\n## 버튼/액션\n")
                for b in list(dict.fromkeys(data["buttons"]))[:25]:
                    print(f"- {b}")

            # JSON 저장 (스크립트와 동일 폴더)
            out_path = os.path.join(SCRIPT_DIR, "globalsess_dashboard_result.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n---\n전체 데이터: `{out_path}`")

        except Exception as e:
            print(f"오류: {e}")
            import traceback

            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
