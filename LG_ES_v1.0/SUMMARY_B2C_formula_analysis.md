# B2C Summary by Country 시트 수식 분석

## 1. 요약

- **Summary by Country** 시트의 국가별 행은 **PDP_Raw** 시트를 **Country(B)** · **Division(E)** · **Monitoring(F) = 'Y'** 기준으로 집계한 값으로 채워집니다.
- B2B(PLP_BUSINESS)와 **다른 점**: 소스 시트가 **PDP_Raw**, 조건에 **Division(E)** 포함, **Scoring Y/N** 대신 **Monitoring(F)** 사용, 점수 컬럼이 **10개**(AK~AT, 각 만점 10).

---

## 2. PDP_Raw ↔ Summary by Country 컬럼 매핑 (엑셀 기준)

| Summary 열 | 엑셀 수식 (집계 방식) | PDP_Raw 열 | 의미 |
|------------|------------------------|------------|------|
| **K** | `=IFERROR(AVERAGEIFS(PDP_Raw!$AK:$AK, PDP_Raw!$B:$B, Summary!$C행, PDP_Raw!$F:$F, "Y", PDP_Raw!$E:$E, Summary!$D행), 0)` | **AK (37열)** | 1. UFN 평균 |
| **L** | `AVERAGEIFS(PDP_Raw!$AL:$AL, Country=$C행, Monitoring="Y", Division=$D행)` | **AL (38열)** | 2. Basic Assets 평균 |
| **M** | `AVERAGEIFS(PDP_Raw!$AM:$AM, ...)` | **AM (39열)** | 3. Spec Summary 평균 |
| **N** | `AVERAGEIFS(PDP_Raw!$AN:$AN, ...)` | **AN (40열)** | 4. FAQ 평균 |
| **O** | `AVERAGEIFS(PDP_Raw!$AO:$AO, ...)` | **AO (41열)** | 5. Tag \<Title\> 평균 |
| **P** | `AVERAGEIFS(PDP_Raw!$AP:$AP, ...)` | **AP (42열)** | 6. Tag \<Description\> 평균 |
| **Q** | `AVERAGEIFS(PDP_Raw!$AQ:$AQ, ...)` | **AQ (43열)** | 7. Tag \<H1\> 평균 |
| **R** | `AVERAGEIFS(PDP_Raw!$AR:$AR, ...)` | **AR (44열)** | 8. Tag \<Canonical Link\> 평균 |
| **S** | `AVERAGEIFS(PDP_Raw!$AS:$AS, ...)` | **AS (45열)** | 9. Tag \<Alt text\>_(Feature Cards) 평균 |
| **T** | `AVERAGEIFS(PDP_Raw!$AT:$AT, ...)` | **AT (46열)** | 10. Tag \<Alt text\>_(Front Image) 평균 |
| **U** | `=XLOOKUP(C행, Summary by Country!$C:$C, Summary!$V:$V)` | — | 동일 시트 이전 기간 참조 |
| **W** | `=IF(ISNUMBER(U행), U행-V행, "-")` | — | GAP (U - V) |

- **조건**: `PDP_Raw!$B:$B = Summary by Country!$C행` (국가), `PDP_Raw!$F:$F = "Y"` (Monitoring = Y), `PDP_Raw!$E:$E = Summary by Country!$D행` (Division).
- **행 10**: K10~T10은 `=AVERAGE(K11:K60)` 등으로 **전체 국가 평균**만 계산.

---

## 3. PDP_Raw 시트 컬럼 (헤더 행=2 기준, 0-based 인덱스)

| 인덱스 | 엑셀 열 | 헤더명 |
|--------|--------|--------|
| 0 | A | Region |
| 1 | B | Country |
| 2 | C | Locale |
| 3 | D | Page Type |
| 4 | E | Division |
| 5 | F | Monitoring |
| 36 | AK | 1. UFN |
| 37 | AL | 2. Basic Assets |
| 38 | AM | 3. Spec Summary |
| 39 | AN | 4. FAQ |
| 40 | AO | 5. Tag \<Title\> |
| 41 | AP | 6. Tag \<Description\> |
| 42 | AQ | 7. Tag \<H1\> |
| 43 | AR | 8. Tag \<Canonical Link\> |
| 44 | AS | 9. Tag \<Alt text\>_(Feature Cards) |
| 45 | AT | 10. Tag \<Alt text\>_(Front Image) |

- B2C는 **Scoring Items**가 "Score (out of 10)" 이므로, 항목당 만점 10, 총 만점 **100**.

---

## 4. B2B vs B2C 차이 요약

| 항목 | B2B (Summary) | B2C (Summary by Country) |
|------|----------------|---------------------------|
| 소스 시트 | PLP_BUSINESS | PDP_Raw |
| 조건1 | Country (B) | Country (B) |
| 조건2 | Scoring Y/N (H) = "Y" | Monitoring (F) = "Y" |
| 조건3 | — | **Division (E)** = Summary의 Division (D) |
| 점수 컬럼 수 | 5개 (K~O) | **10개 (K~T)** |
| 점수 열 범위 | X~AB (24~28) | **AK~AT (37~46)** |
| 항목당 만점 | 20/20/15/15/15 (총 85) | **각 10 (총 100)** |

---

## 5. PDP_Raw만으로 만들 수 있는 Summary 컬럼

- **Region**, **Country**, **Division**: PDP_Raw에서 그대로 사용 (집계 키).
- **ufn_avg (K)** ~ **alt_front_avg (T)**: Country + Division + Monitoring='Y' 조건으로 **AK~AT 열 평균**.
- **total_score_pct**: (K+L+...+T) / 100 * 100 = 10개 평균의 평균 또는 합/100*100.

**U(이전 기간 참조)**, **W(GAP)** 는 동일 시트/이전 기간 데이터가 필요하므로 PDP_Raw 단일 소스로는 동일 복제 불가.

---

## 6. 엑셀 데이터 기반 SUMMARY 테이블 생성 (B2B와 동일 방식)

- **쿼리**: `summary_from_pdp_raw_b2c.sql` — PDP_Raw(엑셀 구조)를 소스로 Summary by Country와 동일한 집계.
- **실행**: `build_summary_b2c_from_excel.py` — B2C 엑셀 파일의 PDP_Raw 시트를 읽어 위 쿼리와 동일한 로직으로 집계 후 **SUMMARY 테이블**을 CSV로 저장 (`SUMMARY_B2C_*.csv`).
- **검증**: `run_summary_from_pdp_raw_b2c.py` — 엑셀 PDP_Raw 집계 결과와 Summary by Country 시트 값 비교.
