# B2B Summary 시트 수식 분석

## 1. 요약

- **Summary** 시트의 국가별 행(약 50개)은 **PLP_BUSINESS** 시트를 **Country**·**Scoring Y/N = 'Y'** 기준으로 집계한 값과, **Product Category**·**Blog** 시트를 참조한 값으로 채워집니다.
- PLP_BUSINESS에서 오는 컬럼은 **국가별 평균**만 사용합니다.

---

## 2. PLP_BUSINESS ↔ Summary 컬럼 매핑 (엑셀 기준)

| Summary 열 | 엑셀 수식 (집계 방식) | PLP_BUSINESS 열 | 의미 |
|------------|------------------------|-----------------|------|
| **K** | `=IFERROR(AVERAGEIFS(PLP_BUSINESS!X:X, PLP_BUSINESS!$B:$B, Summary!$C행, PLP_BUSINESS!$H:$H, "Y"), 0)` | **X (24열)** | Title Tag Score 평균 |
| **L** | `AVERAGEIFS(PLP_BUSINESS!Y:Y, Country=$C행, Scoring Y/N="Y")` | **Y (25열)** | Description Tag Score 평균 |
| **M** | `AVERAGEIFS(PLP_BUSINESS!Z:Z, ...)` | **Z (26열)** | H1 Tag Score 평균 |
| **N** | `AVERAGEIFS(PLP_BUSINESS!AA:AA, ...)` | **AA (27열)** | Canonical Link Score 평균 |
| **O** | `AVERAGEIFS(PLP_BUSINESS!AB:AB, ...)` | **AB (28열)** | Feature Alt Score 평균 |
| **P** | `=HLOOKUP($C행, 'Product Category'!$E$7:$AS$68, 62, 0)` | — | Product Category 시트 참조 (PLP_BUSINESS 아님) |
| **Q** | `=IF(ISNUMBER(MATCH(C행,S:S,0)), NA(), IF(ISNA(P행), NA(), XLOOKUP(C행, Blog!C:C, Blog!G:G, 0)))` | — | Blog 시트 참조 |
| **R** | `=IF(ISNA(P10), "예외", "")` | — | P(Product Category)가 NA이면 "예외" |

- **조건**: `PLP_BUSINESS!$B:$B = Summary!$C행` (국가 일치), `PLP_BUSINESS!$H:$H = "Y"` (Scoring Y/N = Y).
- **행 9**: K9~Q9는 `=AVERAGEIF(K10:K59, "<>#N/A")` 등으로 **전체 국가 평균**만 계산.

---

## 3. PLP_BUSINESS 시트 컬럼 (헤더 행=2 기준, 0-based 인덱스)

| 인덱스 | 엑셀 열 | 헤더명 |
|--------|--------|--------|
| 0 | A | Region |
| 1 | B | Country |
| 2 | C | Locale |
| 3 | D | Page Type |
| 4 | E | CAT/PLP |
| 7 | H | Scoring Y/N |
| 23 | X | Title Tag Score |
| 24 | Y | Description Tag Score |
| 25 | Z | H1 Tag Score |
| 26 | AA | Canonical Link Score |
| 27 | AB | Feature Alt Score |

(Total Score는 PLP_BUSINESS에 별도 열이 있을 수 있으며, Summary의 Total Score는 위 5개 항목 점수로 계산된 비율일 수 있음.)

---

## 4. PLP_BUSINESS만으로 만들 수 있는 Summary 컬럼

- **Region**, **Country**: PLP_BUSINESS에서 그대로 사용 (집계 키).
- **title_avg (K)**: Country + Scoring Y/N='Y' 조건으로 **X열 평균**.
- **description_avg (L)**: **Y열 평균**.
- **h1_avg (M)**: **Z열 평균**.
- **canonical_avg (N)**: **AA열 평균**.
- **feature_alt_avg (O)**: **AB열 평균**.
- **total_score_pct**: (title_avg + description_avg + h1_avg + canonical_avg + feature_alt_avg) / 85 * 100 (만점 20+20+15+15+15=85 가정).

**Product Category(P)**, **Blog(Q)**, **예외(R)** 는 다른 시트/테이블이 필요하므로 PLP_BUSINESS 단일 소스로는 동일 복제 불가.
