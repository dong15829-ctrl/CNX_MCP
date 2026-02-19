#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build feature-style report from parsed daily data and output HTML + PDF.
--llm 옵션 사용 시 LLM으로 기사 본문을 생성해 퀄리티를 높일 수 있습니다 (OPENAI_API_KEY 필요).
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
PARSED = ROOT / "data" / "parsed"
OUT_DIR = ROOT / "output"


def load_data():
    with open(PARSED / "all_days.json", "r", encoding="utf-8") as f:
        return json.load(f)


def k_to_int(s):
    if not s:
        return 0
    s = str(s).strip().upper().replace("M", "000K")
    if "K" in s:
        return int(float(s.replace("K", "").strip()) * 1000)
    return int(float(s))


def _table_rows_html(data: list) -> str:
    """일별 버즈 테이블 행 HTML."""
    html = ""
    for d in data:
        html += f"        <tr><td>{d.get('date', '')}</td><td>{d.get('d_day', '')}</td><td class=\"number\">{d.get('buzz_total', '')}</td><td class=\"number\">{d.get('buzz_total_yoy', '')}</td><td class=\"number\">{d.get('buzz_ultra', '')}</td><td class=\"number\">{d.get('buzz_ultra_yoy', '')}</td></tr>\n"
    return html


def write_html_report(data: list, out_path: Path, llm_content: dict | None = None):
    """Write 기획기사-style HTML report. llm_content가 있으면 LLM 생성 본문 사용."""
    first = data[0]
    last = data[-1]
    table_body = _table_rows_html(data)

    if llm_content:
        title = (llm_content.get("title") or "").strip() or "2026.1H 데일리 모니터링 주간 분석"
        lead_raw = (llm_content.get("lead") or "").strip().replace("\\n", "\n")
        lead = lead_raw.replace("\n", "<br>\n  ")
        sections = llm_content.get("sections") or []
    else:
        total_buzz_start = k_to_int(first.get("buzz_total"))
        total_buzz_end = k_to_int(last.get("buzz_total"))
        growth_pct = ((total_buzz_end - total_buzz_start) / total_buzz_start * 100) if total_buzz_start else 0
        title = f"한 주간 소셜 버즈, D-25에서 D-20까지 약 {growth_pct:.0f}% 증가"
        lead = (
            f"2026년 상반기 Galaxy Unpacked(26.1H)를 앞두고 2월 1일(D-25)부터 2월 6일(D-20)까지 6일간의 데일리 모니터링 데이터를 종합한 결과, "
            f"전체 버즈량은 <strong>{first.get('buzz_total')}</strong>에서 <strong>{last.get('buzz_total')}</strong>로 확대되었으며, "
            f"전년 동기 대비 약 <strong>{last.get('buzz_total_yoy')}</strong> 수준으로 관심이 높아진 상태다. "
            "특히 D-21·D-20 구간에서 올림픽·ENHYPEN 협업 및 참여형 이벤트가 겹치며 일일 버즈가 7만 건을 넘어선 날이 이어졌다."
        )
        sections = []

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{title[:80]} (2/1~2/6)</title>
  <style>
    body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; margin: 40px auto; max-width: 720px; line-height: 1.7; color: #222; }}
    h1 {{ font-size: 1.5rem; border-bottom: 2px solid #1a1a2e; padding-bottom: 8px; margin-top: 2rem; }}
    h2 {{ font-size: 1.2rem; color: #16213e; margin-top: 1.8rem; }}
    .lead {{ font-size: 1.05rem; color: #444; margin: 1rem 0; }}
    .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.95rem; }}
    th, td {{ border: 1px solid #ddd; padding: 10px 12px; text-align: left; }}
    th {{ background: #f2f4f7; font-weight: 600; }}
    .number {{ text-align: right; }}
    ul {{ margin: 0.5rem 0; padding-left: 1.4rem; }}
    .highlight {{ background: #f0f7ff; padding: 1rem; border-left: 4px solid #2563eb; margin: 1rem 0; }}
    .section {{ margin-bottom: 2rem; }}
    @media print {{ body {{ max-width: 100%; }} }}
  </style>
</head>
<body>
  <p class="meta">2026.1H Galaxy Unpacked 데일리 모니터링 · 2월 1일~6일 통합 분석</p>
  <h1>{title}</h1>
  <p class="lead">{lead}</p>

  <div class="section">
    <h2>1. 일별 버즈 요약</h2>
    <p>아래는 분석 기간 중 일자별 전체 버즈량·Ultra 버즈량 및 전년 대비 비율이다.</p>
    <table>
      <thead><tr><th>기준일</th><th>D-Day</th><th>전체 버즈</th><th>전년대비</th><th>Ultra 버즈</th><th>전년대비</th></tr></thead>
      <tbody>
{table_body}      </tbody>
    </table>
  </div>
"""
    if llm_content and sections:
        for i, sec in enumerate(sections, start=2):
            h = (sec.get("heading") or "").strip()
            b = (sec.get("body") or "").strip().replace("\\n", "\n").replace("\n", "<br>\n    ")
            if not h:
                continue
            html += f"""  <div class="section">
    <h2>{i}. {h}</h2>
    <p>{b}</p>
  </div>
"""
    else:
        # 템플릿 폴백
        all_drivers = []
        seen = set()
        for d in data:
            for s in (d.get("driver_summaries") or [])[:3]:
                if s and s not in seen:
                    seen.add(s)
                    all_drivers.append(s)
        html += """    <div class="highlight">
      <strong>인사이트:</strong> 2/4(D-22) 이후 일일 버즈가 20만 건을 넘었고, 2/5(D-21)에는 약 28만 건, 2/6(D-20)에는 약 39만 건으로 급증했다.
      수원(공식)·로컬 채널 모두 전년 대비 비중이 커졌으며, D-20 전날까지 '올림픽·ENHYPEN 협업', '경품·참여 이벤트', '프라이버시 티저'가 공통 드라이버로 작용했다.
    </div>
  </div>
  <div class="section">
    <h2>2. 트렌드 턴닝포인트</h2>
    <p>시계열 상 D-25~D-24 구간은 상대적으로 완만했으나, D-22(2/4)에 일일 약 3.9만 건으로 소폭 봉우리를 이룬 뒤, D-21(2/5) 약 7.4만 건, D-20(2/6) 약 10.3만 건으로 두드러지게 증가했다.
    이는 올림픽 카운트다운·ENHYPEN 협업 게시물과 #ExploreGalaxy·#GalaxyUnpacked 참여형·경품형 이벤트가 겹친 시점과 맞닿아 있다.</p>
  </div>
  <div class="section">
    <h2>3. 채널·드라이버 인사이트</h2>
    <p>기간 내 주요 반응을 이끈 콘텐츠·이슈는 다음과 같이 정리할 수 있다.</p>
    <ul>
"""
        for dr in all_drivers[:12]:
            html += f"      <li>{dr}</li>\n"
        html += """    </ul>
    <p>수원(공식) 채널은 개인정보 보호·프라이버시 티저, 올림픽·ENHYPEN 협업 등으로 버즈를 확대했고, 로컬은 경품·참여 이벤트, Galaxy Unpacked 예측·S26 Ultra 비교 등이 반복 언급되었다.
    미디어·소비자 채널은 전년 대비 상승한 반면, 커뮤니티는 D-20 근접 시점에서 전년 대비 수준(x0.9)으로 소강된 것으로 집계되었다.</p>
  </div>
  <div class="section">
    <h2>4. 제품·라인별 관심</h2>
    <p>Event 누적 기준 2/6(D-20) 시점 2026.1H 버즈는 Total 약 0.4M, Product는 Family 68K·Ultra 41K·Baseline 27K·Buds 5K, AI 관련은 Total 37K·Pure 32K 수준이다.
    Ultra는 전년 대비 x1.4로 성장했고, 전체 버즈 증가폭이 Ultra보다 커서 Family·Baseline 등으로 관심이 분산된 양상이다.</p>
  </div>

  <div class="section">
    <h2>5. 요약 및 전망</h2>
    <p>2월 1일~6일 구간에서 2026.1H Galaxy Unpacked 관련 소셜 버즈는 <strong>전체 약 1.3배 이상 성장</strong>했으며, D-20을 기점으로 일일 버즈가 10만 건대에 진입했다.
    공식 채널의 프라이버시·올림픽·ENHYPEN 메시지와 로컬의 참여·경품 이벤트가 동시에 작용했고, 언팩 D-day가 다가올수록 이 조합이 유지될 가능성이 있다.
    향후 D-19 이후 일별 버즈 추이와 채널별 감성·리스크 지표를 이어서 모니터링하면, 이벤트 직전·직후 인사이트를 정리하는 데 도움이 될 것이다.</p>
  </div>

  <p class="meta" style="margin-top: 2rem;">본 리포트는 2/1~2/6 데일리 모니터링 HTML 데이터를 파싱·집계하여 작성되었으며, 2026.1H Daily Monitoring Report 기준일(D-25~D-20)을 반영하였다.</p>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"HTML report written: {out_path}")


def _register_cjk_font():
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for path in [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CJK", path))
                return "CJK"
            except Exception:
                continue
    return None


def write_pdf_report(data: list, out_path: Path, llm_content: dict | None = None):
    """Write PDF using reportlab (Korean with CJK font). llm_content가 있으면 LLM 생성 본문 사용."""
    if not HAS_REPORTLAB:
        print("reportlab not installed. Install with: pip install reportlab")
        return False

    font_name = _register_cjk_font() or "Helvetica"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=25 * mm,
        leftMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        name="ReportHeading2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold" if font_name == "Helvetica" else font_name,
        fontSize=11,
        spaceAfter=6,
        spaceBefore=14,
    )
    body_style = ParagraphStyle(
        name="ReportBody",
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )

    story = []
    first = data[0]
    last = data[-1]

    if llm_content:
        title = (llm_content.get("title") or "").strip() or "2026.1H 데일리 모니터링 주간 분석"
        lead = (llm_content.get("lead") or "").strip().replace("\\n", "\n")
        sections = llm_content.get("sections") or []
    else:
        total_start = k_to_int(first.get("buzz_total"))
        total_end = k_to_int(last.get("buzz_total"))
        growth_pct = ((total_end - total_start) / total_start * 100) if total_start else 0
        title = f"한 주간 소셜 버즈, D-25에서 D-20까지 약 {growth_pct:.0f}% 증가"
        lead = (
            f"2월 1일(D-25)에서 2월 6일(D-20)까지 6일간 데이터를 통합한 결과, "
            f"전체 버즈량은 {first.get('buzz_total')}에서 {last.get('buzz_total')}로 확대 "
            f"(약 {growth_pct:.0f}% 증가). 전년 대비 {last.get('buzz_total_yoy')} 수준. "
            "D-21에서 일일 버즈 7만 건, D-20에서 10만 건을 넘었고, "
            "올림픽·ENHYPEN 프로모와 참여형 이벤트가 겹치며 관심이 높아졌다."
        )
        sections = []

    story.append(Paragraph("2026.1H Galaxy Unpacked · 데일리 모니터링 주간 리포트", body_style))
    story.append(Paragraph("2월 1일~2월 6일 (D-25 ~ D-20) 통합 분석", body_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(title, heading_style))
    for para in lead.replace("\\n", "\n").split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    story.append(Spacer(1, 16))

    story.append(Paragraph("1. 일별 버즈 요약", heading_style))
    table_data = [["기준일", "D-Day", "전체", "전년대비", "Ultra", "전년대비"]]
    for d in data:
        table_data.append([
            d.get("date", ""),
            d.get("d_day", ""),
            d.get("buzz_total", ""),
            d.get("buzz_total_yoy", ""),
            d.get("buzz_ultra", ""),
            d.get("buzz_ultra_yoy", ""),
        ])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    if llm_content and sections:
        for i, sec in enumerate(sections, start=2):
            h = (sec.get("heading") or "").strip()
            b = (sec.get("body") or "").strip().replace("\\n", "\n")
            if not h:
                continue
            story.append(Paragraph(f"{i}. {h}", heading_style))
            for p in b.split("\n"):
                if p.strip():
                    story.append(Paragraph(p.strip(), body_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("2. 트렌드 턴닝포인트", heading_style))
        story.append(Paragraph(
            "D-25~D-24는 완만했고, D-22(2/4) 일일 약 3.9만 건, D-21(2/5) 약 7.4만 건, "
            "D-20(2/6) 약 10.3만 건으로 증가. 올림픽 카운트다운·ENHYPEN 공개문과 참여 이벤트 시점과 맞닿아 있다.",
            body_style,
        ))
        story.append(Spacer(1, 12))
        story.append(Paragraph("3. 채널 및 드라이버 인사이트", heading_style))
        drivers = []
        seen = set()
        for d in data:
            for s in (d.get("driver_summaries") or [])[:2]:
                if s and s not in seen:
                    seen.add(s)
                    drivers.append(s)
        for s in drivers[:8]:
            story.append(Paragraph("· " + s, body_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("4. 제품 라인 및 AI", heading_style))
        story.append(Paragraph(
            "D-20 기준: Total 약 0.4M, Family 68K, Ultra 41K, Baseline 27K, Buds 5K; AI Total 37K, Pure 32K. Ultra 전년대비 x1.4.",
            body_style,
        ))
        story.append(Spacer(1, 12))
        story.append(Paragraph("5. 요약 및 전망", heading_style))
        story.append(Paragraph(
            "주간 버즈가 1.3배 이상 증가. 공식 프라이버시·올림픽·ENHYPEN 메시지와 로컬 참여·경품 이벤트가 작동. D-19 이후 지속 모니터링 권장.",
            body_style,
        ))

    doc.build(story)
    print(f"PDF report written: {out_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="주간 데일리 모니터링 리포트 생성 (HTML/PDF)")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="LLM으로 기사 본문 생성 (OPENAI_API_KEY 필요). 미사용 시 고정 템플릿 사용.",
    )
    args = parser.parse_args()

    data = load_data()
    if not data:
        print("No data in all_days.json")
        return

    llm_content = None
    if args.llm:
        try:
            import sys
            sys.path.insert(0, str(SCRIPT_DIR))
            from llm_report_writer import generate_report
            llm_content = generate_report(data)
            print("LLM 기사 본문 생성 완료.")
        except Exception as e:
            print(f"LLM 생성 실패 (템플릿으로 진행): {e}")
            llm_content = None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = "2026.1H_데일리모니터링_주간분석_2월1일-6일"
    write_html_report(data, OUT_DIR / f"{base}.html", llm_content=llm_content)

    if HAS_REPORTLAB:
        write_pdf_report(data, OUT_DIR / f"{base}.pdf", llm_content=llm_content)
    else:
        try:
            from weasyprint import HTML
            HTML(filename=str(OUT_DIR / f"{base}.html")).write_pdf(OUT_DIR / f"{base}.pdf")
            print(f"PDF (weasyprint) written: {OUT_DIR / (base + '.pdf')}")
        except Exception as e:
            print(f"PDF not generated. Open the HTML file and use Print to PDF. Error: {e}")


if __name__ == "__main__":
    main()
