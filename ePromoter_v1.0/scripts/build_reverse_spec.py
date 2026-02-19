#!/usr/bin/env python3
"""
테이블/그래프 → API 역참조 명세서 생성.
- menu_config.json + analysis/menu_*.json + analysis/api_responses/*.json 사용
- 출력: analysis/table_api_spec.json, analysis/graph_api_spec.json, docs/테이블_그래프_API_역참조_명세.md
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
DOCS = ROOT / "docs"
CONFIG = ROOT / "replication" / "config" / "menu_config.json"
API_RESPONSES = ANALYSIS / "api_responses"


def load_json(path: Path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def safe_filename(s: str) -> str:
    import re
    return re.sub(r"[^\w\-.]", "_", (s or "").strip().replace("/", "_")) or "index"


def main():
    menu_config = load_json(CONFIG)
    if not menu_config:
        print("menu_config.json not found")
        return

    menus_by_path = {}
    for m in menu_config.get("menus", []):
        full = m.get("fullPath") or ""
        path = full.replace("/globaldashboard", "") or "/main"
        menus_by_path[path] = m

    table_specs = []
    graph_specs = []
    response_schemas = {}  # api_short_name -> top-level keys

    if API_RESPONSES.exists():
        for f in API_RESPONSES.glob("*.json"):
            data = load_json(f)
            if not data:
                continue
            name = f.stem
            if isinstance(data, dict):
                response_schemas[name] = list(data.keys())[:30]
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                response_schemas[name] = list(data[0].keys())[:30]

    for path in sorted(ANALYSIS.glob("menu_globaldashboard_*.json")):
        data = load_json(path)
        if not data:
            continue
        slug = path.stem.replace("menu_", "")
        path_key = data.get("path") or ""
        label = data.get("label") or slug
        path_norm = path_key.replace("/globaldashboard", "").strip() or "/main"
        if not path_norm.startswith("/"):
            path_norm = "/" + path_norm
        cfg = menus_by_path.get(path_norm) or {}
        slug_short = path_norm.strip("/").split("/")[-1] or slug.replace("globaldashboard_", "")

        # 테이블 → Data/Table API
        for block in data.get("table_headers") or []:
            if isinstance(block, dict) and block.get("_error"):
                continue
            headers = block.get("headers") or []
            if not headers:
                continue
            table_id = block.get("id") or ""
            table_class = (block.get("class") or "").strip() or "—"
            data_api = cfg.get("dataApi") or cfg.get("tableApi") or ""
            data_apis = cfg.get("dataApis") or []
            if data_api:
                data_apis = [data_api] + list(data_apis)
            if not data_apis:
                apis_this = [a for a in data.get("apis_this_page") or [] if a.get("post_data") and ("Data" in (a.get("url") or "") or "TableData" in (a.get("url") or ""))]
                data_apis = list(dict.fromkeys([a.get("url", "").split("/")[-1] for a in apis_this if a.get("url")]))
            for api_path in (data_apis or ["—"]):
                if isinstance(api_path, dict):
                    continue
                api_short = api_path.split("/")[-1] if api_path else "—"
                req_schema = "from apis_this_page.post_data"
                resp_schema = response_schemas.get(f"{slug_short}_{api_short}") or response_schemas.get(api_short) or "—"
                table_specs.append({
                    "menu": label,
                    "menu_path": path_key,
                    "table_id": table_id,
                    "table_class": table_class,
                    "headers": headers[:20],
                    "data_api": api_path,
                    "api_short_name": api_short,
                    "request_note": req_schema,
                    "response_schema_sample": resp_schema,
                })

        # 그래프 → Graph API
        chart_spec = data.get("chart_spec") or []
        structure_charts = (data.get("structure") or {}).get("chart_containers") or []
        graph_api = cfg.get("graphApi") or ""
        api_short = graph_api.split("/")[-1] if graph_api else "—"
        resp_schema = response_schemas.get(f"{slug_short}_{api_short}") or "—" if graph_api else "—"
        added_graph = 0
        for i, ch in enumerate(chart_spec if chart_spec else structure_charts):
            if isinstance(ch, dict) and ch.get("_error"):
                continue
            section_title = ch.get("section_title") if isinstance(ch, dict) else ""
            cid = ch.get("id") if isinstance(ch, dict) else (ch.get("id") if isinstance(ch, dict) else "")
            cclass = ch.get("class") if isinstance(ch, dict) else (ch.get("class") if isinstance(ch, dict) else "")
            graph_specs.append({
                "menu": label,
                "menu_path": path_key,
                "chart_id": cid or "—",
                "chart_class": cclass or "—",
                "section_title": (section_title or "").strip()[:200],
                "graph_api": graph_api or "—",
                "api_short_name": api_short,
                "response_schema_sample": resp_schema,
            })
            added_graph += 1
        if graph_api and added_graph == 0:
            graph_specs.append({
                "menu": label,
                "menu_path": path_key,
                "chart_id": "—",
                "chart_class": "—",
                "section_title": "(메뉴별 차트 영역)",
                "graph_api": graph_api,
                "api_short_name": api_short,
                "response_schema_sample": resp_schema,
            })

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    with open(ANALYSIS / "table_api_spec.json", "w", encoding="utf-8") as f:
        json.dump({"specs": table_specs, "source": "menu_*.json + menu_config.json + api_responses"}, f, ensure_ascii=False, indent=2)
    with open(ANALYSIS / "graph_api_spec.json", "w", encoding="utf-8") as f:
        json.dump({"specs": graph_specs, "source": "menu_*.json + menu_config.json + api_responses"}, f, ensure_ascii=False, indent=2)

    # 마크다운 명세서
    md = [
        "# 테이블·그래프 → API 역참조 명세서",
        "",
        "대시보드 **테이블/그래프**가 **어느 API**를 참조하는지, 요청/응답 구조 샘플을 역추적한 명세입니다.",
        "",
        "---",
        "",
        "## 1. 테이블 → API 참조",
        "",
        "| 메뉴 | 테이블(class/id) | 컬럼(헤더) | Data/Table API | 요청 | 응답 스키마 샘플 |",
        "|------|------------------|------------|----------------|------|------------------|",
    ]
    for t in table_specs[:80]:
        menu = (t.get("menu") or "").replace("|", "\\|")
        tc = ((t.get("table_class") or "") + " " + (t.get("table_id") or "")).strip() or "—"
        headers = ", ".join((t.get("headers") or [])[:5]).replace("|", "\\|")
        api = (t.get("data_api") or "—").replace("|", "\\|")
        req = t.get("request_note") or "—"
        resp = ", ".join((t.get("response_schema_sample") or [])[:8]) if isinstance(t.get("response_schema_sample"), list) else (t.get("response_schema_sample") or "—")
        md.append(f"| {menu} | {tc[:40]} | {headers[:50]} | {api[:50]} | {req} | {str(resp)[:60]} |")
    if len(table_specs) > 80:
        md.append(f"| … | … | … | … | … | 외 {len(table_specs) - 80}건은 `analysis/table_api_spec.json` 참고 |")

    md.extend([
        "",
        "---",
        "",
        "## 2. 그래프 → API 참조",
        "",
        "| 메뉴 | 차트(id/class) | 섹션 제목(그래프 설명) | Graph API | 응답 스키마 샘플 |",
        "|------|----------------|-------------------------|-----------|------------------|",
    ])
    for g in graph_specs[:60]:
        menu = (g.get("menu") or "").replace("|", "\\|")
        chart = ((g.get("chart_class") or "") + " " + (g.get("chart_id") or "")).strip() or "—"
        title = (g.get("section_title") or "—").replace("|", "\\|")[:50]
        api = (g.get("graph_api") or "—").replace("|", "\\|")
        resp = ", ".join((g.get("response_schema_sample") or [])[:8]) if isinstance(g.get("response_schema_sample"), list) else (g.get("response_schema_sample") or "—")
        md.append(f"| {menu} | {chart[:35]} | {title} | {api[:45]} | {str(resp)[:50]} |")
    if len(graph_specs) > 60:
        md.append(f"| … | … | … | … | 외 {len(graph_specs) - 60}건은 `analysis/graph_api_spec.json` 참고 |")

    md.extend([
        "",
        "---",
        "",
        "## 3. 파이프라인 요약",
        "",
        "- **테이블**: 메뉴별 Data/Table API (`menu_config.json`의 `dataApi`, `tableApi`, `dataApis`) → 요청 body는 `menu_*.json`의 `apis_this_page[].post_data` 참고.",
        "- **그래프**: 메뉴별 Graph API (`menu_config.json`의 `graphApi`) → 동일한 필터 body 사용.",
        "- **응답 스키마**: `analysis/api_responses/*.json` 수집 시 해당 파일의 최상위 키가 응답 필드 샘플로 사용됨.",
        "",
        f"*생성: scripts/build_reverse_spec.py | 테이블 {len(table_specs)}건, 그래프 {len(graph_specs)}건*",
    ])
    with open(DOCS / "테이블_그래프_API_역참조_명세.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Table specs: {len(table_specs)} -> analysis/table_api_spec.json")
    print(f"Graph specs: {len(graph_specs)} -> analysis/graph_api_spec.json")
    print(f"Doc: docs/테이블_그래프_API_역참조_명세.md")


if __name__ == "__main__":
    main()
