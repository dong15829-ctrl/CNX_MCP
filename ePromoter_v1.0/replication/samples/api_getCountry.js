/**
 * getCountry API 호출 샘플. Region 목록 조회.
 */
var BASE = '';

function getCountry(title) {
  var body = {
    rhqArray: ['AFRICA', 'Americas', 'APAC', 'EHQ', 'G.CN', 'KOREA', 'MENA', 'SWA'],
    title: title || 'Executive Summary'
  };
  return fetch(BASE + '/ajax/getCountry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body)
  })
  .then(function(res) { return res.json(); });
}

// 사용 예: getCountry('Executive Summary').then(function(data) { ... });
