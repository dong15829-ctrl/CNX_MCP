#!/usr/bin/env python3
"""
Samsung Global Dashboard 상세 분석: 메뉴별 페이지 구조, API, 자산, 공통 기능 수집.
다른 환경에서 동일 대시보드 재개발을 위한 분석 데이터 생성.
"""
from playwright.sync_api import sync_playwright
import json
import os
import re
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

BASE_URL = "https://www.globalsess.com"
LOGIN_URL = "http://www.globalsess.com/globaldashboard/"
EMAIL = "dongil.kim@concentrix.com"
PASSWORD = "Ssgdb001!"

# 메뉴 전체 (경로 -> 라벨)
MENUS = [
    ("/globaldashboard/main", "Main (Home)"),
    ("/globaldashboard/executiveSummary", "Executive Summary"),
    ("/globaldashboard/divisionSummary", "Division Summary"),
    ("/globaldashboard/sales_all2", "Sales Summary"),
    ("/globaldashboard/operation_all2", "Operation Summary"),
    ("/globaldashboard/shopapp_operation", "ShopApp Summary"),
    ("/globaldashboard/botjourney_operation", "Bot / AI Summary"),
    ("/globaldashboard/epp_operation", "EPP / SMB Summary"),
    ("/globaldashboard/retailer_operation", "Retailer Summary"),
    ("/globaldashboard/mxFlagshipSummary_pre", "MX Flagship Summary"),
    ("/globaldashboard/performanceSummary", "Performance Summary"),
]

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "analysis"
SCREENSHOTS_DIR = OUT_DIR / "screenshots"
HTML_DIR = OUT_DIR / "html"
ASSETS_DIR = OUT_DIR / "assets"
ASSETS_IMAGES = ASSETS_DIR / "images"
API_RESPONSES_DIR = OUT_DIR / "api_responses"


def ensure_dirs():
    for d in (OUT_DIR, SCREENSHOTS_DIR, HTML_DIR, ASSETS_DIR, ASSETS_IMAGES, API_RESPONSES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def safe_filename(path: str) -> str:
    return re.sub(r"[^\w\-.]", "_", path.strip("/").replace("/", "_")) or "index"


def extract_page_structure(page) -> dict:
    """현재 페이지의 DOM 구조 요약: 스크립트, 스타일, 이미지, 폼, 차트 영역 등."""
    structure = {
        "scripts": [],
        "stylesheets": [],
        "images": [],
        "forms": [],
        "tables": [],
        "chart_containers": [],
        "data_tables": [],
        "selects": [],
        "inputs": [],
    }
    try:
        for el in page.query_selector_all("script[src]"):
            structure["scripts"].append(el.get_attribute("src") or "")
        for el in page.query_selector_all("link[rel='stylesheet']"):
            structure["stylesheets"].append(el.get_attribute("href") or "")
        for el in page.query_selector_all("img[src]"):
            src = el.get_attribute("src") or ""
            alt = el.get_attribute("alt") or ""
            structure["images"].append({"src": src, "alt": alt})
        for form in page.query_selector_all("form"):
            action = form.get_attribute("action") or ""
            method = (form.get_attribute("method") or "get").lower()
            structure["forms"].append({"action": action, "method": method})
        for el in page.query_selector_all("table"):
            structure["tables"].append({"id": el.get_attribute("id"), "class": el.get_attribute("class")})
        for sel in ["[id*='chart']", "[class*='chart']", ".google-chart", "[id*='Chart']"]:
            for el in page.query_selector_all(sel):
                structure["chart_containers"].append({
                    "tag": el.evaluate("e => e.tagName"),
                    "id": el.get_attribute("id"),
                    "class": el.get_attribute("class"),
                })
        for el in page.query_selector_all("select"):
            structure["selects"].append({
                "name": el.get_attribute("name"),
                "id": el.get_attribute("id"),
            })
        for el in page.query_selector_all("input"):
            structure["inputs"].append({
                "type": el.get_attribute("type"),
                "name": el.get_attribute("name"),
                "id": el.get_attribute("id"),
            })
    except Exception as e:
        structure["_error"] = str(e)
    return structure


def extract_js_nav_and_apis(page) -> dict:
    """인라인 스크립트에서 내비게이션 함수명·API 호출 패턴 추출."""
    result = {"nav_functions": [], "ajax_or_fetch_patterns": []}
    try:
        scripts = page.query_selector_all("script:not([src])")
        full_js = ""
        for s in scripts:
            full_js += (s.inner_text() or "") + "\n"
        # moveMain(), moveExecutive(), location.href, ajax.post 등
        for m in re.finditer(r"(move\w+)\s*\(", full_js):
            result["nav_functions"].append(m.group(1))
        for m in re.finditer(r"ajax\.(get|post)\s*\(\s*[\"']([^\"']+)[\"']", full_js):
            result["ajax_or_fetch_patterns"].append({"method": m.group(1).upper(), "path": m.group(2)})
        for m in re.finditer(r"[\"']/([a-zA-Z0-9_/]+)[\"']", full_js):
            result["ajax_or_fetch_patterns"].append({"path": "/" + m.group(1)})
    except Exception as e:
        result["_error"] = str(e)
    return result


def extract_table_headers(page) -> list:
    """페이지 내 테이블의 thead/헤더 셀 수집."""
    result = []
    try:
        for table in page.query_selector_all("table"):
            tid = table.get_attribute("id") or ""
            tclass = (table.get_attribute("class") or "").strip()
            headers = []
            for th in table.query_selector_all("thead th, thead td, tr:first-child th, tr:first-child td"):
                t = (th.inner_text() or "").strip()
                if t and len(t) < 200:
                    headers.append(t)
            if headers:
                result.append({"id": tid, "class": tclass, "headers": headers})
    except Exception as e:
        result = [{"_error": str(e)}]
    return result


def extract_header_tooltips(page) -> list:
    """테이블 헤더/셀의 title(툴팁) 수집 → 지표 정의 보강용."""
    result = []
    try:
        for el in page.query_selector_all("th[title], td[title], .data_type_table th[title], .data_type_table td[title]"):
            title = (el.get_attribute("title") or "").strip()
            text = (el.inner_text() or "").strip().replace("\n", " ")[:150]
            if title or text:
                result.append({"text": text, "title": title})
        for el in page.query_selector_all("[data-tooltip], [data-original-title]"):
            tip = el.get_attribute("data-tooltip") or el.get_attribute("data-original-title") or ""
            text = (el.inner_text() or "").strip()[:100]
            if tip or text:
                result.append({"text": text, "tooltip": tip.strip()[:500]})
    except Exception as e:
        result = [{"_error": str(e)}]
    return result


def extract_chart_spec(page) -> list:
    """차트 영역별: 컨테이너 id/class, 상단 섹션 제목(그래프가 무엇인지)."""
    result = []
    try:
        for el in page.query_selector_all("[id*='chart'], [id*='Chart'], [class*='chart'], .google-chart"):
            cid = el.get_attribute("id")
            cclass = (el.get_attribute("class") or "").strip()
            section_title = ""
            try:
                section_title = el.evaluate("""
                    el => {
                        const wrap = el.closest('.section_wrap, .section, .data_type');
                        if (wrap) {
                            const t = wrap.querySelector('.tit, .title, h2, h3');
                            return t ? (t.innerText || '').trim().slice(0, 120) : (wrap.innerText || '').trim().split('\\n')[0].slice(0, 120);
                        }
                        const prev = el.previousElementSibling;
                        return prev ? (prev.innerText || '').trim().slice(0, 120) : '';
                    }
                """) or ""
            except Exception:
                pass
            result.append({
                "id": cid,
                "class": cclass,
                "section_title": (section_title or "").strip()[:120],
            })
    except Exception as e:
        result = [{"_error": str(e)}]
    return result


def extract_filter_elements(page) -> list:
    """필터 영역: 기간, select, 체크박스 등 라벨·name·옵션 스냅샷."""
    result = []
    try:
        # date inputs
        for el in page.query_selector_all("input[type='date'], input[type='text'][id*='date'], input[name*='from'], input[name*='to']"):
            result.append({
                "type": "date_or_range",
                "id": el.get_attribute("id"),
                "name": el.get_attribute("name"),
                "placeholder": (el.get_attribute("placeholder") or "")[:80],
            })
        # selects
        for el in page.query_selector_all("select"):
            opts = []
            for opt in el.query_selector_all("option"):
                v = opt.get_attribute("value")
                t = (opt.inner_text() or "").strip()
                opts.append({"value": v, "text": t[:80] if t else None})
            result.append({
                "type": "select",
                "id": el.get_attribute("id"),
                "name": el.get_attribute("name"),
                "options_count": len(opts),
                "options_sample": opts[:15],
            })
        # checkbox/radio 그룹 (라벨만)
        for el in page.query_selector_all("input[type='checkbox'], input[type='radio']"):
            name = el.get_attribute("name")
            if name and not any(r.get("name") == name for r in result):
                result.append({"type": el.get_attribute("type"), "name": name, "id": el.get_attribute("id")})
    except Exception as e:
        result = [{"_error": str(e)}]
    return result


def collect_network_requests(requests_log: list, responses_log: list) -> list:
    """수집된 요청/응답에서 API 목록 정리."""
    apis = []
    seen = set()
    for req in requests_log:
        url = req.get("url", "")
        if not url or "globalsess" not in url:
            continue
        method = req.get("method", "GET")
        if url.endswith(".js") or url.endswith(".css") or "chrome-extension" in url:
            continue
        key = (method, url)
        if key in seen:
            continue
        seen.add(key)
        apis.append({
            "method": method,
            "url": url,
            "post_data": req.get("post_data"),
        })
    return apis


def main():
    ensure_dirs()
    crawl_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_path = OUT_DIR / "crawl_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"crawl_started_at": crawl_timestamp, "status": "running"}, f, ensure_ascii=False, indent=2)

    all_menus_analysis = []
    all_apis = []
    requests_log = []
    responses_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        def on_request(request):
            try:
                post = request.post_data if request.post_data else None
                requests_log.append({
                    "url": request.url,
                    "method": request.method,
                    "post_data": post[:2000] if post else None,
                })
            except Exception:
                pass

        def on_response(response):
            try:
                responses_log.append({"url": response.url, "status": response.status})
                url = response.url
                if "globalsess" not in url or "/ajax/" not in url or response.status != 200:
                    return
                if "getCountry" in url or "getSiteCode" in url:
                    return
                if "Data" not in url and "GraphData" not in url and "TableData" not in url and "FunnelData" not in url and "TrafficTableData" not in url and "MissedChatTableData" not in url and "HandledChatTableData" not in url and "FlagshipPreTableData" not in url:
                    return
                ct = (response.headers.get("content-type") or "").lower()
                if "json" not in ct:
                    return
                body = response.body()
                if not body or len(body) > 2 * 1024 * 1024:
                    return
                parsed = urllib.parse.urlparse(url)
                path = (parsed.path or "").strip("/")
                parts = path.split("/")
                if "ajax" in parts:
                    idx = parts.index("ajax")
                    menu_part = parts[idx - 1] if idx > 0 else "unknown"
                    api_name = parts[idx + 1] if idx + 1 < len(parts) else "unknown"
                else:
                    menu_part = safe_filename(path.split("/")[0]) if path else "unknown"
                    api_name = path.replace("/", "_")[-50:]
                fname = f"{safe_filename(menu_part)}_{safe_filename(api_name)}.json"
                out_path = API_RESPONSES_DIR / fname
                try:
                    data = json.loads(body.decode("utf-8", errors="replace"))
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    out_path.write_bytes(body)
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            # ----- 로그인 -----
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            email_input = page.query_selector("#user_id, input[name='id'], input[type='email']")
            password_input = page.query_selector("#user_pw, input[name='user_pw'], input[type='password']")
            if email_input and password_input:
                email_input.fill(EMAIL)
                password_input.fill(PASSWORD)
                submit = page.query_selector("a.login_btn_img, a[href='javascript:login()']")
                if submit:
                    submit.click()
                page.wait_for_url("**/main**", timeout=15000)
                page.wait_for_timeout(2000)

            # 로그인 시 API 기록
            login_apis = [r for r in requests_log if "login" in r.get("url", "").lower()]
            with open(OUT_DIR / "login_api.json", "w", encoding="utf-8") as f:
                json.dump(login_apis, f, ensure_ascii=False, indent=2)

            # ----- 각 메뉴 페이지 방문 -----
            for path, label in MENUS:
                url = BASE_URL + path
                slug = safe_filename(path)
                print(f"Analyzing: {label} -> {url}")
                requests_log.clear()
                responses_log.clear()
                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(3500)
                except Exception as e:
                    print(f"  Load error: {e}")
                    all_menus_analysis.append({"path": path, "label": label, "error": str(e)})
                    continue

                # 스크린샷
                try:
                    page.screenshot(path=SCREENSHOTS_DIR / f"{slug}.png", full_page=False)
                except Exception:
                    pass

                # HTML 저장
                try:
                    html = page.content()
                    with open(HTML_DIR / f"{slug}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                except Exception:
                    pass

                structure = extract_page_structure(page)
                js_info = extract_js_nav_and_apis(page)
                apis = collect_network_requests(requests_log, responses_log)
                table_headers = extract_table_headers(page)
                filter_elements = extract_filter_elements(page)
                header_tooltips = extract_header_tooltips(page)
                chart_spec = extract_chart_spec(page)

                for a in apis:
                    if a not in all_apis and (a.get("url") or "").strip():
                        all_apis.append(a)

                menu_data = {
                    "path": path,
                    "label": label,
                    "url": page.url,
                    "title": page.title(),
                    "structure": structure,
                    "js_nav_and_apis": js_info,
                    "apis_this_page": apis,
                    "table_headers": table_headers,
                    "filter_elements": filter_elements,
                    "header_tooltips": header_tooltips,
                    "chart_spec": chart_spec,
                }
                all_menus_analysis.append(menu_data)
                with open(OUT_DIR / f"menu_{slug}.json", "w", encoding="utf-8") as f:
                    json.dump(menu_data, f, ensure_ascii=False, indent=2)

            # ----- 공통 UI: 메인 페이지에서 헤더/버튼/서브내비 상세 추출 -----
            page.goto(BASE_URL + "/globaldashboard/main", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)
            common = {
                "buttons": [],
                "subnav_links": [],
                "header_html_snippet": None,
            }
            for el in page.query_selector_all("button, [role='button'], input[type='submit'], .btn, a.btn"):
                common["buttons"].append({
                    "text": (el.inner_text() or el.get_attribute("value") or "").strip()[:80],
                    "class": el.get_attribute("class"),
                    "onclick": (el.get_attribute("onclick") or "")[:200],
                })
            for el in page.query_selector_all("a[href^='javascript:']"):
                common["subnav_links"].append({
                    "text": (el.inner_text() or "").strip()[:80],
                    "href": el.get_attribute("href"),
                })
            with open(OUT_DIR / "common_ui.json", "w", encoding="utf-8") as f:
                json.dump(common, f, ensure_ascii=False, indent=2)

            # ----- 이미지 다운로드 (선택: 메인 페이지 기준) -----
            page.goto(BASE_URL + "/globaldashboard/main", wait_until="networkidle", timeout=10000)
            for el in page.query_selector_all("img[src]"):
                try:
                    src = el.get_attribute("src")
                    if not src or not src.strip():
                        continue
                    if src.startswith("data:"):
                        continue
                    full_url = urllib.parse.urljoin(page.url, src)
                    name = safe_filename(Path(urllib.parse.urlparse(full_url).path).name or "img") + ".png"
                    r = page.request.get(full_url)
                    if r.ok:
                        (ASSETS_IMAGES / name).write_bytes(r.body())
                except Exception:
                    pass

        finally:
            browser.close()

    # ----- 전체 API 목록 및 분석 요약 저장 -----
    with open(OUT_DIR / "all_apis.json", "w", encoding="utf-8") as f:
        json.dump(all_apis, f, ensure_ascii=False, indent=2)
    with open(OUT_DIR / "all_menus_analysis.json", "w", encoding="utf-8") as f:
        json.dump(all_menus_analysis, f, ensure_ascii=False, indent=2)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "crawl_started_at": crawl_timestamp,
            "crawl_finished_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "completed",
            "menus_count": len(all_menus_analysis),
            "apis_count": len(all_apis),
        }, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Output: {OUT_DIR}")
    print(f"  - screenshots: {SCREENSHOTS_DIR}")
    print(f"  - html: {HTML_DIR}")
    print(f"  - apis: {OUT_DIR / 'all_apis.json'}")
    print(f"  - common_ui: {OUT_DIR / 'common_ui.json'}")


if __name__ == "__main__":
    main()
