# B2B Summary: 원천 데이터 → 집계 → 테이블 표시

## 1. DB 원천 데이터

| 항목 | 값 |
|------|-----|
| **테이블** | `reportbusiness_es_old` (backend/db.py `TABLE_B2B`) |
| **DB** | `.env` 의 `MYSQL_DATABASE` (기본 `lg_ha`) |

**B2B Summary에서 쓰는 컬럼**

| 컬럼명 | 용도 | 비고 |
|--------|------|------|
| `region` | 집계 키 | 비어 있으면 제외 |
| `country` | 집계 키 | 비어 있으면 제외 |
| `scoring` | 필터 | `'Y'` (또는 `'YES'`, `'1'`) 인 행만 사용 |
| `h1_tag_pf` | 점수 | 숫자로 해석 → region·country 별 **평균** |
| `canonical_link_pf` | 점수 | 위와 동일 |
| `feature_cards` | 점수 | 위와 동일 |
| `title_tag_text` | 텍스트 | 점수 컬럼 아님 → Summary에서는 **0** |
| `description_tag_text` | 텍스트 | 점수 컬럼 아님 → Summary에서는 **0** |

**원천 조회 조건 (SQL)**

```sql
WHERE (scoring = 'Y' OR UPPER(TRIM(COALESCE(scoring,'')))= 'Y')
  AND TRIM(COALESCE(region,'')) != '' AND TRIM(COALESCE(country,'')) != ''
GROUP BY region, country
```

---

## 2. 집계 방식 (코드)

### 2-1. pandas 경로 (우선)

**파일**: `backend/data.py` → `get_summary_b2b_snapshot()`

1. **RAW 로드**  
   `get_b2b_raw_df()`  
   - `SELECT * FROM reportbusiness_es_old_v2_v2`  
   - `pipeline/preprocess.py` `preprocess_b2b()`: 컬럼 매핑(`h1_tag_pf`→`h1_tag_score` 등), `scoring_yn in ('Y','YES','1')` 필터, 점수 컬럼 `pd.to_numeric(..., errors='coerce')`

2. **집계**  
   `pipeline/aggregate.py` → `aggregate_b2b_snapshot(df)`:

```python
# pipeline/aggregate.py
B2B_SCORE_COLUMNS = [
    "title_tag_score", "description_tag_score", "h1_tag_score",
    "canonical_link_score", "feature_alt_score",
]
B2B_MAX = 85.0  # 만점 20+20+15+15+15

def _agg_b2b(df, group_cols):
    cols = [c for c in B2B_SCORE_COLUMNS if c in df.columns]
    if not cols:
        return pd.DataFrame()
    agg = df.groupby(group_cols, as_index=False).agg(
        sku_count=("country", "count"),
        **{c: (c, "mean") for c in cols}
    )
    agg[cols] = agg[cols].fillna(0.0)
    agg["total_score_pct"] = agg[cols].sum(axis=1) / B2B_MAX * 100.0
    return agg.round(6)
```

3. **행 변환**  
   `_df_to_rows(snap)`  
   - float 컬럼 NaN → 0, 소수 6자리  
   - `list[dict]` 반환

4. **스코어 null 보정**  
   `_b2b_fill_scores(rows)`  
   - `title_tag_score`, `description_tag_score`, `h1_tag_score`, `canonical_link_score`, `feature_alt_score`, `total_score_pct` 중 **없거나 None**이면 **0.0** 설정

### 2-2. SQL 경로 (pandas 빈 결과일 때)

**파일**: `backend/data.py` → `SQL_B2B_SNAPSHOT`, `get_summary_b2b_snapshot_sql()`

```python
# backend/data.py (요약)
SELECT
    region, country,
    COUNT(*) AS sku_count,
    0 AS title_tag_score,
    0 AS description_tag_score,
    ROUND(COALESCE(AVG(CAST(...h1_tag_pf... AS DECIMAL(10,2))), 0), 6) AS h1_tag_score,
    ROUND(COALESCE(AVG(CAST(...canonical_link_pf... AS DECIMAL(10,2))), 0), 6) AS canonical_link_score,
    ROUND(COALESCE(AVG(CAST(...feature_cards... AS DECIMAL(10,2))), 0), 6) AS feature_alt_score,
    ROUND((위 3개 합) / 85.0 * 100.0, 6) AS total_score_pct
FROM reportbusiness_es_old_v2
WHERE scoring = 'Y' AND region != '' AND country != ''
GROUP BY region, country
```

이후 동일하게 `_b2b_fill_scores(rows)` 적용.

---

## 3. 집계 테이블 저장/표시

### 3-1. API 응답 (저장 형태)

`GET /api/summary?report_type=B2B&month=latest` 가 반환하는 **한 행** 형태:

```json
{
  "region": "Asia",
  "country": "Australia",
  "sku_count": 175,
  "title_tag_score": 0.0,
  "description_tag_score": 0.0,
  "h1_tag_score": 0.0,
  "canonical_link_score": 0.0,
  "feature_alt_score": 0.0,
  "total_score_pct": 0.0
}
```

- **저장소**: DB에 별도 “집계 테이블”은 없음. 요청 시마다 위 집계( pandas 또는 SQL )를 실행해 **메모리에서 list[dict]** 로 만들고, `_b2b_fill_scores()` 로 스코어 키가 없거나 None이면 0.0을 채운 뒤 JSON으로 내려줌.

### 3-2. 프론트 테이블 매핑

**파일**: `frontend/index.html` → `renderTableB2B(rows)`

| 테이블 열 순서 | API 키 | 표시 |
|----------------|--------|------|
| 1 | `region` | 그대로 |
| 2 | `country` | 그대로 |
| 3 (td.num[0]) | `sku_count` | 숫자 또는 "—" |
| 4 (td.num[1]) | `title_tag_score` 또는 `title_score` | `fmtNum(...)` → "0.00" 또는 "—" |
| 5 | `description_tag_score` 또는 `description_score` | 위와 동일 |
| 6 | `h1_tag_score` 또는 `h1_score` | 위와 동일 |
| 7 | `canonical_link_score` 또는 `canonical_score` | 위와 동일 |
| 8 | `feature_alt_score` 또는 `alt_text_score` | 위와 동일 |
| 9 | `total_score_pct` 또는 `total_score` | 위와 동일 |

`fmtNum(v)`: `v != null && v !== ''` 이면 `Number(v).toFixed(2)`, 아니면 **"—"**.

**"—"가 나오는 경우**: 해당 키가 응답에 없거나 `null`/`undefined`일 때.  
→ 백엔드에서 `_b2b_fill_scores()` 가 **키가 없거나 None이면 0.0을 넣도록** 수정해 두었으므로, 재시작 후에는 "0.00"으로 나와야 함.

---

## 요약

1. **원천**: `reportbusiness_es_old_v2` 의 `region`, `country`, `scoring`, `h1_tag_pf`, `canonical_link_pf`, `feature_cards`.
2. **집계**: pandas(우선) 또는 SQL로 region·country 별 `sku_count`, 5개 스코어 평균, `total_score_pct` = (5개 합)/85×100.  
   이후 `_b2b_fill_scores()` 로 스코어 키가 없거나 None이면 0.0 보정.
3. **저장/표시**: 별도 DB 테이블 없이, API가 위 list[dict]를 JSON으로 내려주고, 프론트 `renderTableB2B` 가 위 키로 `#tableBodyB2B` 의 각 `td.num` 에 매핑해 표시.
