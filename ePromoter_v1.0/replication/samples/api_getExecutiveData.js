/**
 * Executive Summary 데이터/차트 API 호출 샘플.
 * getParam()은 화면에서 선택한 from, to, site_code, switch_table 등을 반환하는 함수로 가정.
 */
var BASE = '';

function getParam() {
  // 실제 구현: daterange, region/country/site 체크박스, data_type(day/week/month/quarter) 등 수집
  return {
    title: 'Executive Summary',
    from: '2026-02-06',
    to: '2026-02-06',
    period: 'custom',
    site_code: 'AE,AU,BR,DE,FR,UK',
    period_date: '',
    switch_table: { chat: 1, sales14: 2, sales: 1 }
  };
}

function getExecutiveData() {
  var param = getParam();
  return fetch(BASE + '/executiveSummary/ajax/getExecutiveData', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(param)
  }).then(function(res) { return res.json(); });
}

function getExecutiveGraphData() {
  var param = getParam();
  return fetch(BASE + '/executiveSummary/ajax/getExecutiveGraphData', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(param)
  }).then(function(res) { return res.json(); });
}

// 사용 예:
// getExecutiveData().then(function(data) { /* 테이블 렌더 */ });
// getExecutiveGraphData().then(function(data) { /* Google Charts 렌더 */ });
