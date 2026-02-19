#!/usr/bin/env python3
"""
analysis/menu_*.json 에서 table_headers, filter_elements를 읽어
지표/데이터 항목 목록(이름 기준)을 추출하고, 정의·단위는 비워 둔 데이터 사전 생성.
"""
import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
ANALYSIS_DIR = ROOT / "analysis"
OUT_JSON = ANALYSIS_DIR / "indicator_list.json"
OUT_MD = ROOT / "docs" / "데이터_지표_정의_가이드.md"


def _definitions_from_tooltips(menu_files, analysis_dir):
    """header_tooltips에서 text -> title/tooltip 매핑 (정의 보강)."""
    text_to_def = defaultdict(list)
    for path in menu_files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        label = data.get("label") or path.stem
        for item in data.get("header_tooltips") or []:
            if isinstance(item, dict) and item.get("_error"):
                continue
            text = (item.get("text") or "").strip().replace("\n", " ")[:150]
            title = (item.get("title") or "").strip()
            tooltip = (item.get("tooltip") or "").strip()
            defn = title or tooltip
            if text and defn:
                text_to_def[text].append({"menu": label, "definition": defn[:500]})
    return text_to_def


def _definitions_from_api_responses(analysis_dir):
    """api_responses/*.json에서 응답 필드명 수집 (데이터 항목 = API 필드)."""
    api_dir = analysis_dir / "api_responses"
    fields = defaultdict(list)
    if not api_dir.exists():
        return fields
    for f in api_dir.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            continue
        api_name = f.stem
        if isinstance(data, dict):
            for k in data.keys():
                fields[k].append({"source_api": api_name, "definition": "API 응답 필드"})
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            for k in data[0].keys():
                fields[k].append({"source_api": api_name, "definition": "API 응답 필드"})
    return fields


def main():
    indicators_by_name = defaultdict(list)
    definition_by_name = {}
    filter_names = set()
    menu_files = sorted(ANALYSIS_DIR.glob("menu_globaldashboard_*.json"))

    tooltip_defs = _definitions_from_tooltips(menu_files, ANALYSIS_DIR)
    api_field_defs = _definitions_from_api_responses(ANALYSIS_DIR)

    for path in menu_files:
        slug = path.stem.replace("menu_", "")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        label = data.get("label") or slug

        for block in data.get("table_headers") or []:
            if isinstance(block, dict) and block.get("_error"):
                continue
            for h in (block.get("headers") or []):
                t = (h or "").strip().replace("\n", " ")
                if not t or len(t) > 200 or t in ("-", "date", "Rank"):
                    continue
                indicators_by_name[t].append({"menu": label, "type": "table_header", "source": slug})
                if t not in definition_by_name and t in tooltip_defs:
                    definition_by_name[t] = tooltip_defs[t][0].get("definition", "")

        for block in data.get("filter_elements") or []:
            if isinstance(block, dict) and block.get("_error"):
                continue
            name = block.get("name") or block.get("id") or ""
            if name and name not in filter_names:
                filter_names.add(name)
                key = f"[필터] {name}"
                indicators_by_name[key].append({"menu": label, "type": "filter", "source": slug})

    for field_name, infos in api_field_defs.items():
        if field_name not in indicators_by_name:
            indicators_by_name[field_name].append({"menu": "API", "type": "api_field", "source": infos[0].get("source_api", "")})
        definition_by_name[field_name] = infos[0].get("definition", "API 응답 필드")

    unique_indicators = []
    seen = set()
    for name in sorted(indicators_by_name.keys()):
        if name in seen:
            continue
        seen.add(name)
        entries = indicators_by_name[name]
        menus = list(dict.fromkeys([e["menu"] for e in entries]))
        unique_indicators.append({
            "name": name,
            "menus": menus,
            "definition": definition_by_name.get(name, ""),
            "unit": "",
            "notes": "",
        })

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"indicators": unique_indicators, "source": "table_headers + filter_elements from menu_*.json"}, f, ensure_ascii=False, indent=2)

    # 마크다운 가이드
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)
    lines = [
        "# 데이터 항목 및 지표 정의 가이드",
        "",
        "## 1. 현재 파악된 범위",
        "",
        "| 구분 | 파악 여부 | 설명 |",
        "|------|-----------|------|",
        "| **지표/컬럼 이름** | ✅ 수집됨 | 각 메뉴 테이블 헤더·필터 이름 (`analysis/indicator_list.json`, `menu_*.json` 내 `table_headers`) |",
        "| **지표 정의** (의미·산식) | ⚠️ 부분 | `header_tooltips`(툴팁)·API 응답 필드명에서 보강; 매뉴얼로 추가 보강 권장 |",
        "| **단위** | ❌ 미수집 | %건, 달러 등 — 수집 데이터에 없음 |",
        "| **API 요청 파라미터** | ✅ 수집됨 | `all_apis.json`, `menu_*.json` 내 `apis_this_page` (post_data) |",
        "| **API 응답 필드/스키마** | ✅ 수집됨 | `analysis/api_responses/*.json` 캡처 시 필드명 반영 |",
        "",
        "---",
        "",
        "## 2. 지표 이름 목록 (정의·단위는 보강용)",
        "",
        "아래는 수집된 **지표/컬럼 이름**입니다. `정의`는 툴팁·API 필드에서 채운 부분이 있으며, 나머지는 매뉴얼·FAQ로 보강하세요.",
        "",
        "| 지표/항목 이름 | 사용 메뉴 | 정의 | 단위 | 비고 |",
        "|----------------|-----------|------|------|------|",
    ]
    for ind in unique_indicators[:120]:  # 상위 120개만 표로
        name = (ind["name"] or "").replace("|", "\\|")[:50]
        menus = ", ".join((ind.get("menus") or [])[:3])
        if len(ind.get("menus") or []) > 3:
            menus += " …"
        defn = ind.get("definition") or "—"
        unit = ind.get("unit") or "—"
        notes = ind.get("notes") or "—"
        lines.append(f"| {name} | {menus} | {defn} | {unit} | {notes} |")
    if len(unique_indicators) > 120:
        lines.append(f"| … | … | … | … | 외 {len(unique_indicators) - 120}개는 `analysis/indicator_list.json` 참고 |")
    lines.extend([
        "",
        "---",
        "",
        "## 3. 정의 보강 방법",
        "",
        "1. **Manual & FAQ Download**: 대시보드에서 \"Manual & FAQ Download\" (`fileDown()`)로 내려받은 문서에 지표 정의가 있을 수 있습니다.",
        "2. **API 응답 캡처**: `dashboard_deep_analysis.py`에서 Data API 응답 body를 저장하면 필드명·단위 추론에 활용할 수 있습니다.",
        "3. **화면 툴팁/도움말**: 각 지표에 마우스 오버 시 나오는 툴팁이 있다면, 추후 크롤에 `title`/`data-*` 속성 수집을 추가할 수 있습니다.",
        "",
        "---",
        "",
        f"*생성: `scripts/build_indicator_list.py` | 지표 수: {len(unique_indicators)}*",
    ])
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Indicators: {len(unique_indicators)} -> {OUT_JSON}")
    print(f"Guide: {OUT_MD}")


if __name__ == "__main__":
    main()
