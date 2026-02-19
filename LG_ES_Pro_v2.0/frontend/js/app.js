(function(){
  window.API_BASE = window.location.origin;
})();
var API = window.API_BASE || '';
var currentUser = { username: '', role: 'user' };

var RETRY_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>';

function showSkeleton(containerId, type) {
  var el = document.getElementById(containerId);
  if (!el) return;
  var html = '';
  if (type === 'table') {
    html = '<div class="skeleton-card" id="' + containerId + '_skeleton">'
      + '<div class="skeleton-card-title skeleton-cell skeleton"></div>'
      + '<table class="skeleton-table"><thead><tr>';
    for (var i = 0; i < 6; i++) html += '<th class="skeleton"></th>';
    html += '</tr></thead><tbody>';
    for (var r = 0; r < 5; r++) {
      html += '<tr>';
      for (var c = 0; c < 6; c++) html += '<td><div class="skeleton-cell skeleton"></div></td>';
      html += '</tr>';
    }
    html += '</tbody></table></div>';
  } else if (type === 'dashboard') {
    html = '<div id="' + containerId + '_skeleton">'
      + '<div class="skeleton-score-grid">';
    for (var s = 0; s < 6; s++) html += '<div class="skeleton-score-item skeleton"></div>';
    html += '</div>'
      + '<div class="skeleton-card"><div class="skeleton-card-title skeleton-cell skeleton"></div><div class="skeleton-chart skeleton"></div></div>'
      + '<div class="skeleton-card"><div class="skeleton-card-title skeleton-cell skeleton"></div><div class="skeleton-chart skeleton"></div></div>'
      + '</div>';
  } else if (type === 'sheet') {
    html = '<div class="skeleton-card" id="' + containerId + '_skeleton">'
      + '<table class="skeleton-table"><thead><tr>';
    for (var i = 0; i < 8; i++) html += '<th class="skeleton"></th>';
    html += '</tr></thead><tbody>';
    for (var r = 0; r < 6; r++) {
      html += '<tr>';
      for (var c = 0; c < 8; c++) html += '<td><div class="skeleton-cell skeleton"></div></td>';
      html += '</tr>';
    }
    html += '</tbody></table></div>';
  } else {
    html = '<div id="' + containerId + '_skeleton" style="padding:1rem;">';
    for (var i = 0; i < 4; i++) {
      html += '<div class="skeleton-row">'
        + '<div class="skeleton-cell skeleton" style="width:' + (20 + Math.random() * 60) + '%;height:1rem;"></div>'
        + '</div>';
    }
    html += '</div>';
  }
  el.style.display = 'block';
  el.innerHTML = html;
}

function hideSkeleton(containerId) {
  var sk = document.getElementById(containerId + '_skeleton');
  if (sk) sk.remove();
}

function showErrorWithRetry(el, message, retryFn) {
  if (!el) return;
  el.className = 'error-with-retry';
  el.style.display = 'flex';
  el.innerHTML = '<span class="error-icon">&#9888;</span>'
    + '<span class="error-message">' + escapeHtml(message) + '</span>'
    + '<button type="button" class="btn-retry">' + RETRY_SVG + ' Retry</button>';
  var btn = el.querySelector('.btn-retry');
  if (btn && retryFn) btn.onclick = function(e) { e.preventDefault(); retryFn(); };
}

function activateWithTransition(el) {
  if (!el) return;
  el.style.display = 'block';
  el.offsetHeight;
  el.classList.add('active');
}

function deactivateWithTransition(el) {
  if (!el) return;
  el.classList.remove('active');
  setTimeout(function() { if (!el.classList.contains('active')) el.style.display = 'none'; }, 260);
}

function switchContentSection(activeEl, allEls) {
  (allEls || []).forEach(function(el) {
    if (!el || el === activeEl) return;
    if (el.classList.contains('active')) {
      el.classList.remove('active');
      el.style.display = 'none';
    }
  });
  if (activeEl) {
    activeEl.style.display = 'block';
    void activeEl.offsetHeight;
    activeEl.classList.add('active');
  }
}

function fetchWithAuth(url, opts) {
  opts = opts || {};
  opts.credentials = 'include';
  return fetch(url, opts).then(function(r) {
    if (r.status === 401) { window.location.href = '/login'; return Promise.reject(new Error('Unauthorized')); }
    return r;
  });
}
var chartScoreByRegion = null;
var chartScoreByCountry = null;
var selectedCountryRegion = 'ASIA';
var selectedCountryForChart = '';
var chartTotalVsJul = null;
var lastSummary = [];
var currentReportType = 'B2B';
var summaryTableSort = { colIndex: -1, dir: 1 };

function getReports() {
  return fetchWithAuth(API + '/api/reports').then(parseJsonOrThrow).then(function(l) { if (!Array.isArray(l)) throw new Error('Invalid'); return l; });
}
function getFilters(reportType, month, selectedRegions) {
  var q = new URLSearchParams();
  q.set('report_type', reportType);
  q.set('month', month);
  if (selectedRegions && selectedRegions.length) selectedRegions.forEach(function(r) { q.append('region', r); });
  return fetchWithAuth(API + '/api/filters?' + q).then(parseJsonOrThrow);
}
function buildSummaryParams(reportType, month, regions, countries) {
  var q = new URLSearchParams();
  q.set('report_type', reportType);
  q.set('month', month);
  if (regions && regions.length) regions.forEach(function(r) { q.append('region', r); });
  if (countries && countries.length) countries.forEach(function(c) { q.append('country', c); });
  return q.toString();
}
function parseJsonOrThrow(r) {
  return r.json().then(function(body) {
    if (!r.ok) {
      var msg = body.message || 'Request failed';
      if (body.detail !== undefined) {
        if (Array.isArray(body.detail)) msg = body.detail.map(function(d) { return d.msg || d.message || (typeof d === 'string' ? d : JSON.stringify(d)); }).join('; ');
        else if (typeof body.detail === 'string') msg = body.detail;
        else msg = String(body.detail);
      }
      throw new Error(msg);
    }
    return body;
  });
}
function getSummary(reportType, month, regions, countries) {
  return fetchWithAuth(API + '/api/summary?' + buildSummaryParams(reportType, month, regions, countries)).then(parseJsonOrThrow);
}
function getStats(reportType, month, regions, countries) {
  return fetchWithAuth(API + '/api/stats?' + buildSummaryParams(reportType, month, regions, countries)).then(parseJsonOrThrow);
}
function getChecklist(month) {
  var url = API + '/api/checklist' + (month ? '?month=' + encodeURIComponent(month) : '');
  return fetchWithAuth(url).then(function(r) { return r.json(); });
}
function getSheet(month, sheet) {
  var url = API + '/api/sheet?month=' + encodeURIComponent(month) + '&sheet=' + encodeURIComponent(sheet);
  return fetchWithAuth(url).then(function(r) { if (!r.ok) throw new Error('Failed to load sheet'); return r.json(); });
}

function getMonthParam() {
  var y = (document.getElementById('yearB2B') || {}).value;
  var m = (document.getElementById('monthB2B') || {}).value;
  if (!y || y === 'latest') return 'latest';
  if (!m) return y + '-01';
  return y + '-' + (String(m).length === 1 ? '0' + m : m);
}

function formatReportDateDisplay(monthStr) {
  var m = (monthStr || '').match(/^(\d{4})-M?(\d{1,2})$/i);
  if (!m) return '';
  var y = m[1], mo = m[2].length === 1 ? '0' + m[2] : m[2];
  var day = 13;
  var w = Math.ceil(day / 7) || 2;
  return y + '.' + mo + '.' + (day < 10 ? '0' + day : day) + '(W' + w + ')';
}

function updateSummaryDateFields(month) {
  var fmt = formatReportDateDisplay(month || getMonthParam());
  var d1 = document.getElementById('reportDate1');
  var lu = document.getElementById('lastUpdated');
  if (d1) d1.textContent = fmt || '—';
  var now = new Date();
  var luStr = now.getFullYear() + '.' + String(now.getMonth() + 1).padStart(2, '0') + '.' + String(now.getDate()).padStart(2, '0') + '(W' + Math.ceil(now.getDate() / 7) + ')';
  if (lu) lu.textContent = luStr;
  updateReportMonthDropdownActive();
}

/* Report Date 드롭다운 */
var _reportMonths = [];
function buildReportMonthDropdown(reports, reportType) {
  var dd = document.getElementById('reportMonthDropdown');
  if (!dd) return;
  var months = (reports || []).filter(function(r) { return (r.report_type || r.reportType) === reportType; }).map(function(r) { return r.month; });
  months = [...new Set(months)];
  months.sort(function(a, b) { if (a === 'latest') return -1; if (b === 'latest') return 1; return b.localeCompare(a); });
  _reportMonths = months;
  var current = getMonthParam();
  dd.innerHTML = months.map(function(m) {
    var label = m === 'latest' ? 'Latest' : m;
    var cls = 'rdm-item' + ((m === current || (current === 'latest' && m === 'latest')) ? ' active' : '');
    return '<button class="' + cls + '" data-month="' + m + '">' + label + '</button>';
  }).join('');
}
function updateReportMonthDropdownActive() {
  var dd = document.getElementById('reportMonthDropdown');
  if (!dd) return;
  var current = getMonthParam();
  dd.querySelectorAll('.rdm-item').forEach(function(btn) {
    btn.classList.toggle('active', btn.getAttribute('data-month') === current || (current === 'latest' && btn.getAttribute('data-month') === 'latest'));
  });
}
(function initReportDatePicker() {
  var chip = document.getElementById('reportDateField');
  if (!chip) return;
  var dd = document.getElementById('reportMonthDropdown');
  function positionDropdown() {
    if (!dd || !chip.classList.contains('open')) return;
    var rect = chip.getBoundingClientRect();
    dd.style.top = (rect.bottom + 6) + 'px';
    dd.style.left = Math.max(8, rect.right - 180) + 'px';
    dd.style.right = 'auto';
  }
  chip.addEventListener('click', function(e) {
    if (e.target.closest('.report-month-dropdown')) return;
    chip.classList.toggle('open');
    if (chip.classList.contains('open')) positionDropdown();
  });
  document.addEventListener('click', function(e) {
    if (!e.target.closest('#reportDateField')) chip.classList.remove('open');
  });
  if (dd) dd.addEventListener('click', function(e) {
    var btn = e.target.closest('.rdm-item');
    if (!btn) return;
    var month = btn.getAttribute('data-month');
    chip.classList.remove('open');
    applyReportMonth(month);
  });
})();
function applyReportMonth(month) {
  var yearSel = document.getElementById('yearB2B');
  var monthSel = document.getElementById('monthB2B');
  if (month === 'latest') {
    if (yearSel) yearSel.value = 'latest';
    if (monthSel) monthSel.value = '';
  } else {
    var parts = month.split('-');
    if (yearSel) { yearSel.value = parts[0]; if (yearSel.onchange) yearSel.onchange(); }
    if (monthSel) monthSel.value = parts[1] ? String(Number(parts[1])).padStart(2, '0') : '';
  }
  var m = getMonthParam();
  updateSummaryDateFields(m);
  getFilters(currentReportType, m, []).then(function(f) {
    fillRegionCountryPanels(f.regions || [], f.countries || [], false);
    loadDashboard(currentReportType, m, [], []);
  });
}

function getPreviousMonthLiteral(month) {
  if (!month || month === 'latest') return null;
  var match = String(month).match(/^(\d{4})-(\d{1,2})$/);
  if (!match) return null;
  var y = parseInt(match[1], 10);
  var m = parseInt(match[2], 10);
  if (m <= 1) return (y - 1) + '-12';
  return y + '-' + (m < 11 ? '0' : '') + (m - 1);
}

/** Return the immediately preceding month from report list. currentMonth = selected month or 'latest'. */
function getImmediatelyPreviousMonth(reports, reportType, currentMonth) {
  var all = (reports || []).filter(function(r) { return (r.report_type || r.reportType) === reportType; }).map(function(r) { return r.month; });
  var literal = all.filter(function(m) { return m && m !== 'latest'; });
  literal.sort(function(a, b) { return b.localeCompare(a); });
  if (literal.length < 2) return null;
  var current = (currentMonth === 'latest' || !currentMonth) ? literal[0] : currentMonth;
  var idx = literal.indexOf(current);
  if (idx < 0 || idx >= literal.length - 1) return null;
  return literal[idx + 1];
}

/** Resolved month for fetch. If 'latest', use first (newest) month in list. */
function resolveCurrentMonthForFetch(reports, reportType, selectedMonth) {
  var literal = (reports || []).filter(function(r) { return (r.report_type || r.reportType) === reportType; }).map(function(r) { return r.month; }).filter(function(m) { return m && m !== 'latest'; });
  literal.sort(function(a, b) { return b.localeCompare(a); });
  if (selectedMonth === 'latest' || !selectedMonth) return literal[0] || 'latest';
  return selectedMonth;
}

function rowKey(r, reportType) {
  var k = (r.region || '') + '|' + (r.country || '');
  if (reportType === 'B2C') k += '|' + (r.division || '');
  return k;
}

function assignRanksAndChange(currentRows, prevRows, reportType) {
  var score = function(r) {
    var v = r.total_score_pct != null ? r.total_score_pct : r.total_score;
    return v != null && v !== '' ? Number(v) : -Infinity;
  };
  currentRows.forEach(function(r) { r.rank = null; r.rankChange = null; });
  var sortedCurrent = currentRows.slice().sort(function(a, b) { return score(b) - score(a); });
  var rank = 1;
  for (var i = 0; i < sortedCurrent.length; i++) {
    if (i > 0 && score(sortedCurrent[i]) < score(sortedCurrent[i - 1])) rank = i + 1;
    sortedCurrent[i].rank = rank;
  }
  var prevRankMap = {};
  if (prevRows && prevRows.length) {
    var sortedPrev = prevRows.slice().sort(function(a, b) { return score(b) - score(a); });
    var pr = 1;
    for (var j = 0; j < sortedPrev.length; j++) {
      if (j > 0 && score(sortedPrev[j]) < score(sortedPrev[j - 1])) pr = j + 1;
      prevRankMap[rowKey(sortedPrev[j], reportType)] = pr;
    }
    currentRows.forEach(function(r) {
      if (r.rank != null) {
        var pk = prevRankMap[rowKey(r, reportType)];
        r.rankChange = pk != null ? r.rank - pk : null;
      }
    });
  }
}

function fillYearMonthSelect(reportType, reports) {
  var months = [...new Set((reports || []).filter(function(r) { return (r.report_type || r.reportType) === reportType; }).map(function(r) { return r.month; }))];
  months.sort(function(a, b) {
    if (a === 'latest') return -1;
    if (b === 'latest') return 1;
    return b.localeCompare(a);
  });
  var years = ['latest'];
  var monthMap = {};
  months.forEach(function(m) {
    if (m === 'latest') return;
    var match = String(m).match(/^(\d{4})-(\d{1,2})$/);
    if (match) {
      var yr = match[1], mo = match[2];
      if (years.indexOf(yr) === -1) years.push(yr);
      if (!monthMap[yr]) monthMap[yr] = [];
      if (monthMap[yr].indexOf(mo) === -1) monthMap[yr].push(mo);
    }
  });
  years.sort(function(a, b) { if (a === 'latest') return -1; if (b === 'latest') return 1; return Number(b) - Number(a); });
  var yearSel = document.getElementById('yearB2B');
  var monthSel = document.getElementById('monthB2B');
  if (yearSel) yearSel.innerHTML = years.map(function(y) { return '<option value="' + y + '">' + y + '</option>'; }).join('');
  function fillMonths() {
    var y = yearSel ? yearSel.value : 'latest';
    var list = (y && y !== 'latest' && monthMap[y]) ? monthMap[y].sort(function(a,b){ return Number(a) - Number(b); }) : ['01','02','03','04','05','06','07','08','09','10','11','12'];
    if (monthSel) {
      monthSel.innerHTML = '<option value="">All</option>' + list.map(function(m) { return '<option value="' + m + '">' + m + '</option>'; }).join('');
    }
  }
  fillMonths();
  if (yearSel) yearSel.onchange = fillMonths;
  if (typeof buildReportMonthDropdown === 'function') buildReportMonthDropdown(reports, reportType);
  return months[0] || 'latest';
}

function getSelectedRegions() {
  var panel = document.getElementById('regionB2BPanel');
  if (!panel) return [];
  return Array.from(panel.querySelectorAll('input:checked')).map(function(el) { return el.value; });
}
function getSelectedCountries() {
  var panel = document.getElementById('countryB2BPanel');
  if (!panel) return [];
  return Array.from(panel.querySelectorAll('input:checked')).map(function(el) { return el.value; });
}

function updateMultiselectButtonLabels(regionList, countryList) {
  var selectedR = getSelectedRegions();
  var selectedC = getSelectedCountries();
  var rBtn = document.getElementById('regionB2BBtn');
  var cBtn = document.getElementById('countryB2BBtn');
  if (rBtn) {
    if (!selectedR.length || selectedR.length === (regionList || []).length) rBtn.textContent = 'All';
    else if (selectedR.length <= 3) rBtn.textContent = selectedR.join(', ');
    else rBtn.textContent = selectedR.length + '';
  }
  if (cBtn) {
    if (!selectedC.length || selectedC.length === (countryList || []).length) cBtn.textContent = 'All';
    else if (selectedC.length <= 5) cBtn.textContent = selectedC.join(', ');
    else cBtn.textContent = selectedC.length + '';
  }
}

function escapeHtml(s) {
  var d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

var SUMMARY_SHEET_CONFIG = [
  { sheet: 'PLP_BUSINESS', bodyId: 'sheetPlpBody', headId: 'sheetPlpHead', loadingId: 'sheetPlpLoading', errorId: 'sheetPlpError', wrapId: 'sheetPlpWrap' },
  { sheet: 'Product Category', bodyId: 'sheetProductCategoryBody', headId: 'sheetProductCategoryHead', loadingId: 'sheetProductCategoryLoading', errorId: 'sheetProductCategoryError', wrapId: 'sheetProductCategoryWrap' },
  { sheet: 'Blog', bodyId: 'sheetBlogBody', headId: 'sheetBlogHead', loadingId: 'sheetBlogLoading', errorId: 'sheetBlogError', wrapId: 'sheetBlogWrap' }
];

function renderSheetRow(arr, colCount, tag) {
  tag = tag || 'td';
  var cells = [];
  for (var i = 0; i < colCount; i++) {
    var v = i < arr.length ? arr[i] : null;
    var text = (v == null || v === '') ? '' : String(v);
    var titleAttr = (tag === 'th' && text) ? ' title="' + String(text).replace(/"/g, '&quot;') + '"' : '';
    cells.push('<' + tag + titleAttr + '>' + escapeHtml(text) + '</' + tag + '>');
  }
  return '<tr>' + cells.join('') + '</tr>';
}

function buildBlogSheetBody(rows, colCount) {
  if (!rows.length) return '';
  var mergeCol = 0, rowspanStart = [], rowspanLen = [];
  var urlCol = 2;
  for (var i = 0; i < rows.length; i++) {
    var arr = Array.isArray(rows[i]) ? rows[i] : [];
    var val = arr[mergeCol];
    var s = String(val != null ? val : '');
    if (i === 0 || s !== String((Array.isArray(rows[i - 1]) ? rows[i - 1] : [])[mergeCol] != null ? (Array.isArray(rows[i - 1]) ? rows[i - 1] : [])[mergeCol] : '')) {
      rowspanStart[i] = true;
      var count = 1;
      while (i + count < rows.length) {
        var nextArr = Array.isArray(rows[i + count]) ? rows[i + count] : [];
        if (String(nextArr[mergeCol] != null ? nextArr[mergeCol] : '') === s) count++;
        else break;
      }
      rowspanLen[i] = count;
    } else rowspanStart[i] = false;
  }
  var html = [];
  for (var r = 0; r < rows.length; r++) {
    var arr = Array.isArray(rows[r]) ? rows[r] : [];
    var cells = [];
    if (rowspanStart[r]) cells.push('<td rowspan="' + rowspanLen[r] + '">' + escapeHtml((arr[0] == null || arr[0] === '') ? '' : String(arr[0])) + '</td>');
    for (var c = 1; c < colCount; c++) {
      var v = c < arr.length ? arr[c] : null;
      var s = (v == null || v === '') ? '' : String(v);
      if (c === urlCol && /^https?:\/\//i.test(s.trim())) {
        var safeHref = s.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/&/g, '&amp;');
        cells.push('<td><a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(s) + '</a></td>');
      } else {
        cells.push('<td>' + escapeHtml(s) + '</td>');
      }
    }
    html.push('<tr>' + cells.join('') + '</tr>');
  }
  return html.join('');
}
function buildSheetBodyWithMerge(rows, colCount) {
  if (!rows.length) return '';
  var mergeCol = 0, rowspanStart = [], rowspanLen = [];
  for (var i = 0; i < rows.length; i++) {
    var arr = Array.isArray(rows[i]) ? rows[i] : [];
    var val = arr[mergeCol];
    var s = String(val != null ? val : '');
    if (i === 0 || s !== String((Array.isArray(rows[i - 1]) ? rows[i - 1] : [])[mergeCol] != null ? (Array.isArray(rows[i - 1]) ? rows[i - 1] : [])[mergeCol] : '')) {
      rowspanStart[i] = true;
      var count = 1;
      while (i + count < rows.length) {
        var nextArr = Array.isArray(rows[i + count]) ? rows[i + count] : [];
        if (String(nextArr[mergeCol] != null ? nextArr[mergeCol] : '') === s) count++;
        else break;
      }
      rowspanLen[i] = count;
    } else rowspanStart[i] = false;
  }
  var html = [];
  for (var r = 0; r < rows.length; r++) {
    var arr = Array.isArray(rows[r]) ? rows[r] : [];
    var cells = [];
    if (rowspanStart[r]) cells.push('<td rowspan="' + rowspanLen[r] + '">' + escapeHtml((arr[0] == null || arr[0] === '') ? '' : String(arr[0])) + '</td>');
    for (var c = 1; c < colCount; c++) {
      var v = c < arr.length ? arr[c] : null;
      cells.push('<td>' + escapeHtml((v == null || v === '') ? '' : String(v)) + '</td>');
    }
    html.push('<tr>' + cells.join('') + '</tr>');
  }
  return html.join('');
}

function isRowEmpty(arr) {
  if (!Array.isArray(arr) || !arr.length) return true;
  for (var i = 0; i < arr.length; i++) {
    if (arr[i] != null && String(arr[i]).trim() !== '') return false;
  }
  return true;
}

async function loadSheetSection(month, cfg) {
  var loading = document.getElementById(cfg.loadingId), errEl = document.getElementById(cfg.errorId), wrap = document.getElementById(cfg.wrapId), tbody = document.getElementById(cfg.bodyId), headRow = document.getElementById(cfg.headId);
  if (wrap) wrap.style.display = 'none';
  if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; errEl.className = 'error'; }
  showSkeleton(cfg.loadingId, 'sheet');
  try {
    var rows = await getSheet(month, cfg.sheet);
    hideSkeleton(cfg.loadingId);
    if (loading) loading.style.display = 'none';
    if (!Array.isArray(rows) || rows.length === 0) {
      if (errEl) {
        errEl.className = 'sheet-empty-state';
        errEl.style.display = 'block';
        errEl.textContent = 'No data for month (' + (month || '') + ') in [' + (cfg.sheet || '') + '].';
      }
      return;
    }
    var colCount = Math.max.apply(null, rows.map(function(r) { return Array.isArray(r) ? r.length : 0; })) || 1;
    var dataRows = rows;
    if (headRow && rows.length > 1) {
      var first = Array.isArray(rows[0]) ? rows[0] : [];
      if (cfg.sheet === 'Blog') {
        headRow.innerHTML = first.map(function(v, i) {
          var text = (v == null || v === '') ? '' : String(v);
          var cls = i < 3 ? 'th-dark' : 'th-blue';
          return '<th class="' + cls + '" title="' + escapeHtml(text) + '">' + escapeHtml(text) + '</th>';
        }).join('');
      } else {
        headRow.innerHTML = renderSheetRow(first, colCount, 'th');
      }
      dataRows = rows.slice(1);
    } else if (headRow) headRow.innerHTML = '';
    dataRows = dataRows.filter(function(row) { return !isRowEmpty(Array.isArray(row) ? row : []); });
    if (cfg.sheet === 'Blog') {
      window._blogSheetRows = dataRows;
      window._blogSheetColCount = colCount;
      var blogFilter = document.getElementById('blogCountryFilter');
      if (blogFilter) {
        var sel = blogFilter.value || '';
        blogFilter.innerHTML = '<option value="">All</option>';
        var seen = {};
        dataRows.forEach(function(r) { var arr = Array.isArray(r) ? r : []; var c = (arr[1] != null ? String(arr[1]) : '').trim(); if (c && !seen[c]) { seen[c] = true; var opt = document.createElement('option'); opt.value = c; opt.textContent = c; blogFilter.appendChild(opt); } });
        blogFilter.value = (sel && seen[sel]) ? sel : '';
      }
      var blogCountry = (blogFilter || {}).value || '';
      var filtered = blogCountry ? dataRows.filter(function(r) { var arr = Array.isArray(r) ? r : []; var c = (arr[1] != null ? String(arr[1]) : '').trim(); return c === blogCountry; }) : dataRows;
      tbody.innerHTML = buildBlogSheetBody(filtered, colCount);
    } else {
      tbody.innerHTML = buildSheetBodyWithMerge(dataRows, colCount);
    }
    if (wrap) wrap.style.display = 'block';
  } catch (e) {
    hideSkeleton(cfg.loadingId);
    if (loading) loading.style.display = 'none';
    if (errEl) {
      showErrorWithRetry(errEl, 'Load failed: ' + (e.message || String(e)), function() {
        loadSheetSection(month, cfg);
      });
    }
  }
}

function loadSummarySheets(month) {
  if (!month) return;
  SUMMARY_SHEET_CONFIG.forEach(function(cfg) { loadSheetSection(month, cfg); });
}

function fmtNum(v) { return (v != null && v !== '') ? Number(v).toFixed(2) : '—'; }
function rankFmt(v) { return (v != null && v !== '') ? Math.round(Number(v)) : '—'; }

// B2B Summary columns: REGION, COUNTRY, SKU, Rank, Rank change, Total Score %, 1.Title ~ 5.Alt
var SUMMARY_TABLE_COLS_B2B = [
  { key: 'region', label: 'REGION', num: false },
  { key: 'country', label: 'COUNTRY', num: false },
  { key: 'sku_count', label: 'SKU', num: true },
  { key: '_rank', label: 'Rank', num: true },
  { key: '_rank_change', label: '▲▼', num: true },
  { key: 'total_score_pct', label: 'Total\nScore', num: true, altKeys: ['total_score'] },
  { key: 'title_tag_score', label: '1. Title', num: true, altKeys: ['title_score'] },
  { key: 'description_tag_score', label: '2. Description', num: true, altKeys: ['description_score'] },
  { key: 'h1_tag_score', label: '3. H1', num: true, altKeys: ['h1_score'] },
  { key: 'canonical_link_score', label: '4. Canonical Link', num: true, altKeys: ['canonical_score'] },
  { key: 'feature_alt_score', label: '5. Alt text_ Feature Cards', num: true, altKeys: ['alt_feature_score', 'alt_text_score'] }
];
// B2C Summary: headers show 1~10, full text in title (tooltip)
var SUMMARY_TABLE_COLS_B2C = [
  { key: 'region', label: 'REGION', num: false },
  { key: 'country', label: 'COUNTRY', num: false },
  { key: 'sku_count', label: 'SKU', num: true },
  { key: '_rank', label: 'Rank', num: true },
  { key: '_rank_change', label: '▲▼', num: true },
  { key: 'total_score_pct', label: 'Total\nScore', num: true },
  { key: 'ufn_score', label: '1', num: true, fullLabel: '1. UFN' },
  { key: 'basic_assets_score', label: '2', num: true, fullLabel: '2. Basic Assets' },
  { key: 'spec_summary_score', label: '3', num: true, fullLabel: '3. Spec Summary' },
  { key: 'faq_score', label: '4', num: true, fullLabel: '4. FAQ' },
  { key: 'title_score', label: '5', num: true, fullLabel: '5. Tag <Title>' },
  { key: 'description_score', label: '6', num: true, fullLabel: '6. Tag <Description>' },
  { key: 'h1_score', label: '7', num: true, fullLabel: '7. Tag <H1>' },
  { key: 'canonical_score', label: '8', num: true, fullLabel: '8. Tag <Canonical Link>' },
  { key: 'alt_feature_score', label: '9', num: true, fullLabel: '9. Tag <Alt text> (Feature Cards)' },
  { key: 'alt_front_score', label: '10', num: true, fullLabel: '10. Tag <Alt text> (Front Image)' }
];

function setSummaryTableHeader(reportType) {
  var tr = document.getElementById('tableSummaryHeadRow');
  if (!tr) return;
  var cols = reportType === 'B2C' ? SUMMARY_TABLE_COLS_B2C : SUMMARY_TABLE_COLS_B2B;
  tr.innerHTML = cols.map(function(c, i) {
    var isDark = (c.key === 'region' || c.key === 'country');
    var cl = isDark ? 'th-dark' : 'th-blue';
    if (c.key === 'sku_count' || c.key === '_rank' || c.key === '_rank_change') cl += ' th-nowrap';
    if (c.key === 'total_score_pct') cl += ' th-two-line';
    var titleAttr = '';
    if (c.fullLabel) titleAttr = ' title="' + escapeHtml(c.fullLabel) + '"';
    else if (c.key === '_rank') titleAttr = ' title="Rank by Total Score %"';
    else if (c.key === '_rank_change') titleAttr = ' title="Rank change vs. previous period"';
    else if (c.key === 'total_score_pct') titleAttr = ' title="Total Score %"';
    else if (c.key && c.key.indexOf('_') !== 0) titleAttr = ' title="' + escapeHtml(c.key) + '"';
    return '<th class="' + cl + ' sortable" data-col-index="' + i + '"' + titleAttr + '>' + escapeHtml(c.label) + '<span class="sort-indicator" aria-hidden="true"></span></th>';
  }).join('');
  var table = tr.closest('table');
  var cg = table && (table.querySelector('#tableSummaryColgroup') || table.querySelector('colgroup'));
  if (cg) {
    var identityW = 10;
    var identityCount = 2;
    var skuW = 5.5;
    var rankW = 4.5;
    var rankChgW = 5;
    var reserved = identityCount * identityW + skuW + rankW + rankChgW;
    var equalCount = cols.length - identityCount - 3;
    var equalW = equalCount > 0 ? ((100 - reserved) / equalCount).toFixed(1) + '%' : '10%';
    cg.innerHTML = cols.map(function(c) {
      if (c.key === 'region' || c.key === 'country') return '<col class="col-identity" style="width:' + identityW + '%" />';
      if (c.key === 'sku_count') return '<col class="col-sku" style="width:' + skuW + '%" />';
      if (c.key === '_rank') return '<col class="col-rank" style="width:' + rankW + '%" />';
      if (c.key === '_rank_change') return '<col class="col-rank-chg" style="width:' + rankChgW + '%" />';
      return '<col class="col-score-equal" style="width:' + equalW + '" />';
    }).join('');
  }
  updateSummaryTableHeaderSortIcons();
}

function sortSummaryRows(rows, colIndex, dir, reportType) {
  if (!rows || !rows.length || colIndex < 0) return rows;
  var cols = reportType === 'B2C' ? SUMMARY_TABLE_COLS_B2C : SUMMARY_TABLE_COLS_B2B;
  var c = cols[colIndex];
  if (!c) return rows;
  var copy = rows.slice();
  copy.sort(function(a, b) {
    var va = getRowCellValue(a, c);
    var vb = getRowCellValue(b, c);
    var anum = c.num;
    var cmp = 0;
    if (anum) {
      var na = (va != null && va !== '') ? Number(va) : -Infinity;
      var nb = (vb != null && vb !== '') ? Number(vb) : -Infinity;
      cmp = na < nb ? -1 : na > nb ? 1 : 0;
    } else {
      var sa = (va != null && va !== '') ? String(va) : '';
      var sb = (vb != null && vb !== '') ? String(vb) : '';
      cmp = sa.localeCompare(sb, undefined, { numeric: true });
    }
    return dir > 0 ? cmp : -cmp;
  });
  return copy;
}

function updateSummaryTableHeaderSortIcons() {
  var tr = document.getElementById('tableSummaryHeadRow');
  if (!tr) return;
  var ths = tr.querySelectorAll('th.sortable');
  ths.forEach(function(th, i) {
    th.classList.remove('sort-asc', 'sort-desc');
    if (i === summaryTableSort.colIndex) {
      th.classList.add(summaryTableSort.dir > 0 ? 'sort-asc' : 'sort-desc');
    }
  });
}

function refreshSummaryTable() {
  var filterEl = document.getElementById('tableScoreFilterB2B');
  var filterType = filterEl ? filterEl.value || '' : '';
  var filtered = applyScoreFilter(lastSummary, filterType);
  var cols = currentReportType === 'B2C' ? SUMMARY_TABLE_COLS_B2C : SUMMARY_TABLE_COLS_B2B;
  var sorted = sortSummaryRows(filtered, summaryTableSort.colIndex, summaryTableSort.dir, currentReportType);
  renderTableB2B(sorted);
  updateSummaryTableHeaderSortIcons();
}

var SCORE_SUMMARY_KEYS_B2B = [
  { key: 'total_score_pct', label: 'Total Score %' },
  { key: 'title_tag_score', label: '1. Title' },
  { key: 'description_tag_score', label: '2. Description' },
  { key: 'h1_tag_score', label: '3. H1' },
  { key: 'canonical_link_score', label: '4. Canonical Link' },
  { key: 'feature_alt_score', label: '5. Alt text_ Feature Cards' }
];
var SCORE_SUMMARY_KEYS_B2C = [
  { key: 'total_score_pct', label: 'Total Score %' },
  { key: 'ufn_score', label: '1. UFN' },
  { key: 'basic_assets_score', label: '2. Basic Assets' },
  { key: 'spec_summary_score', label: '3. Spec Summary' },
  { key: 'faq_score', label: '4. FAQ' },
  { key: 'title_score', label: '5. Tag <Title>' },
  { key: 'description_score', label: '6. Tag <Description>' },
  { key: 'h1_score', label: '7. Tag <H1>' },
  { key: 'canonical_score', label: '8. Tag <Canonical Link>' },
  { key: 'alt_feature_score', label: '9. Tag <Alt text>_(Feature Cards)' },
  { key: 'alt_front_score', label: '10. Tag <Alt text>_(Front Image)' }
];
function renderScoreSummaryB2B(rows) {
  var el = document.getElementById('scoreSummaryB2B');
  if (!el) return;
  if (!rows || !rows.length) { el.innerHTML = ''; return; }
  var keys = currentReportType === 'B2C' ? SCORE_SUMMARY_KEYS_B2C : SCORE_SUMMARY_KEYS_B2B;
  var html = [];
  keys.forEach(function(item, idx) {
    var sum = 0, count = 0;
    rows.forEach(function(r) {
      var v = r[item.key];
      if (v != null && v !== '') { sum += Number(v); count++; }
    });
    var avg = count ? (sum / count).toFixed(2) : '—';
    var cardClass = 'score-summary-item' + (idx === 0 ? ' score-summary-item--primary' : '');
    html.push('<div class="' + cardClass + '"><span class="label">' + escapeHtml(item.label) + '</span><span class="value">' + escapeHtml(String(avg)) + '</span></div>');
  });
  el.innerHTML = html.join('');
}

function renderOperationalSummary(rows, reportType) {
  var topEl = document.getElementById('topPerformersList');
  var strengthsEl = document.getElementById('strengthsList');
  var weaknessesEl = document.getElementById('weaknessesList');
  var actionEl = document.getElementById('actionPlanList');
  if (!rows || !rows.length) {
    if (topEl) topEl.innerHTML = '';
    if (strengthsEl) strengthsEl.innerHTML = '<li>No data</li>';
    if (weaknessesEl) weaknessesEl.innerHTML = '';
    if (actionEl) actionEl.innerHTML = '';
    return;
  }
  var keyScore = reportType === 'B2C' ? 'total_score_pct' : 'total_score_pct';
  var keyCountry = reportType === 'B2C' ? 'division' : 'country';
  var keyRegion = reportType === 'B2C' ? 'region' : 'region';
  var sorted = rows.slice().sort(function(a, b) {
    var va = parseFloat(a[keyScore]) || 0;
    var vb = parseFloat(b[keyScore]) || 0;
    return vb - va;
  });
  var top4 = sorted.slice(0, 4);
  if (topEl) {
    topEl.innerHTML = top4.map(function(r, i) {
      var name = r[keyCountry] || r.country || r.division || '—';
      var score = (parseFloat(r[keyScore]) || 0).toFixed(1);
      return '<div class="score-summary-item"><span class="label">' + (i + 1) + 'st</span><span class="value">' + escapeHtml(name) + ' ' + score + '</span></div>';
    }).join('');
  }
  var avgScore = rows.reduce(function(s, r) { return s + (parseFloat(r[keyScore]) || 0); }, 0) / rows.length;
  var highCount = rows.filter(function(r) { return (parseFloat(r[keyScore]) || 0) >= 95; }).length;
  var lowRows = rows.filter(function(r) { return (parseFloat(r[keyScore]) || 0) < 70; });
  if (strengthsEl) {
    var strengths = [];
    if (avgScore >= 90) strengths.push('Strong regional average: ' + avgScore.toFixed(1) + '%');
    if (highCount > 0) strengths.push('Top performance: ' + highCount + ' countries scored 95+');
    strengthsEl.innerHTML = strengths.length ? strengths.map(function(s) { return '<li>' + escapeHtml(s) + '</li>'; }).join('') : '<li>—</li>';
  }
  if (weaknessesEl) {
    var weaknesses = lowRows.slice(0, 3).map(function(r) { return (r[keyCountry] || r.country || '—') + ': ' + (parseFloat(r[keyScore]) || 0).toFixed(1) + '%'; });
    weaknessesEl.innerHTML = weaknesses.length ? weaknesses.map(function(w) { return '<li>' + escapeHtml(w) + '</li>'; }).join('') : '<li>None significant</li>';
  }
  if (actionEl) {
    var actions = lowRows.length ? ['Mentoring: Share best practices from top performers to improve lower-scoring regions'] : [];
    actions.push('Review and iterate on low-scoring evaluation items');
    actionEl.innerHTML = actions.map(function(a) { return '<li>' + escapeHtml(a) + '</li>'; }).join('');
  }
}

function applyScoreFilter(rows, filterType) {
  if (!rows || !rows.length || !filterType) return rows;
  var n = rows.length;
  var take = Math.max(1, Math.ceil(n * 0.3));
  var score = function(r) { var v = r.total_score_pct != null ? r.total_score_pct : r.total_score; return v != null && v !== '' ? Number(v) : -Infinity; };
  if (filterType === 'top30') {
    return rows.slice().sort(function(a, b) { return score(b) - score(a); }).slice(0, take);
  }
  if (filterType === 'bottom30') {
    return rows.slice().sort(function(a, b) { return score(a) - score(b); }).slice(0, take);
  }
  return rows;
}

function getRowCellValue(r, c) {
  if (c.key === '_rank') return r.rank != null ? r.rank : null;
  if (c.key === '_rank_change') return r.rankChange != null ? r.rankChange : null;
  var v = r[c.key];
  if (v != null && v !== '') return v;
  if (c.altKeys) {
    for (var i = 0; i < c.altKeys.length; i++) {
      v = r[c.altKeys[i]];
      if (v != null && v !== '') return v;
    }
  }
  return null;
}

var CLICKABLE_KEYS_BLACKLIST = { region: 1, country: 1, division: 1, sku_count: 1, _rank: 1, _rank_change: 1 };
function renderTableB2B(rows) {
  var t = document.getElementById('tableBodyB2B');
  if (!t) return;
  var cols = currentReportType === 'B2C' ? SUMMARY_TABLE_COLS_B2C : SUMMARY_TABLE_COLS_B2B;
  t.innerHTML = (rows || []).map(function(r) {
    var region = (r.region != null && r.region !== '') ? String(r.region) : '';
    var country = (r.country != null && r.country !== '') ? String(r.country) : '';
    var division = (r.division != null && r.division !== '') ? String(r.division) : '';
    var trAttrs = ' data-region="' + escapeHtml(region) + '" data-country="' + escapeHtml(country) + '"';
    if (currentReportType === 'B2C') trAttrs += ' data-division="' + escapeHtml(division) + '"';
    return '<tr' + trAttrs + '>' + cols.map(function(c) {
      var v = getRowCellValue(r, c);
      var clickable = c.num && !CLICKABLE_KEYS_BLACKLIST[c.key];
      var tdClass = 'num';
      if (c.key === '_rank') {
        return '<td class="' + tdClass + '">' + (v != null && v !== '' ? Number(v) : '—') + '</td>';
      }
      if (c.key === '_rank_change') {
        if (v == null || v === '') return '<td class="num rank-cell" title="No previous period data">—</td>';
        var n = Number(v);
        var cl = n > 0 ? 'rank-down' : (n < 0 ? 'rank-up' : 'rank-same');
        var sym = n > 0 ? '▼' : (n < 0 ? '▲' : '—');
        var num = n !== 0 ? Math.abs(n) : 0;
        var title = n > 0 ? 'Rank down ' + num : (n < 0 ? 'Rank up ' + num : 'No change');
        var text = n === 0 ? '—' : (sym + ' ' + num);
        return '<td class="num rank-cell ' + cl + '" title="' + title + '">' + text + '</td>';
      }
      if (c.num) {
        if (c.key === 'sku_count') return '<td class="num">' + (v != null && v !== '' ? Math.round(Number(v)) : '—') + '</td>';
        if (clickable) tdClass += ' cell-clickable';
        return '<td class="' + tdClass + '">' + fmtNum(v) + '</td>';
      }
      return '<td>' + escapeHtml(v != null && v !== '' ? String(v) : '') + '</td>';
    }).join('') + '</tr>';
  }).join('');
}

var AGGREGATE_CHART_KEYS_B2B = [
  { dataKey: 'title_tag_score', avgKey: 'avg_title' }, { dataKey: 'description_tag_score', avgKey: 'avg_desc' },
  { dataKey: 'h1_tag_score', avgKey: 'avg_h1' }, { dataKey: 'canonical_link_score', avgKey: 'avg_canon' }, { dataKey: 'feature_alt_score', avgKey: 'avg_alt' }
];
var AGGREGATE_CHART_KEYS_B2C = [
  { dataKey: 'ufn_score', avgKey: 'avg_ufn' }, { dataKey: 'basic_assets_score', avgKey: 'avg_basic_assets' }, { dataKey: 'spec_summary_score', avgKey: 'avg_spec_summary' }, { dataKey: 'faq_score', avgKey: 'avg_faq' },
  { dataKey: 'title_score', avgKey: 'avg_title' }, { dataKey: 'description_score', avgKey: 'avg_desc' }, { dataKey: 'h1_score', avgKey: 'avg_h1' }, { dataKey: 'canonical_score', avgKey: 'avg_canon' }, { dataKey: 'alt_feature_score', avgKey: 'avg_alt_feature' }, { dataKey: 'alt_front_score', avgKey: 'avg_alt_front' }
];

function aggregateByRegion(rows, reportType) {
  if (!rows || !rows.length) return [];
  var rtype = reportType || currentReportType || 'B2B';
  var chartKeys = rtype === 'B2C' ? AGGREGATE_CHART_KEYS_B2C : AGGREGATE_CHART_KEYS_B2B;
  var byRegion = {};
  rows.forEach(function(r) {
    var region = r.region || '';
    if (!byRegion[region]) {
      var o = { region: region, sum_total: 0, count_total: 0 };
      chartKeys.forEach(function(k) { o['sum_' + k.avgKey] = 0; o['count_' + k.avgKey] = 0; });
      byRegion[region] = o;
    }
    var o = byRegion[region];
    var total = r.total_score_pct != null ? r.total_score_pct : r.total_score;
    if (total != null && total !== '') { o.sum_total += Number(total); o.count_total++; }
    chartKeys.forEach(function(k) {
      var v = r[k.dataKey];
      if (v != null && v !== '') { o['sum_' + k.avgKey] += Number(v); o['count_' + k.avgKey]++; }
    });
  });
  return Object.keys(byRegion).sort().map(function(k) {
    var o = byRegion[k];
    var out = { region: o.region, avg_total_score: o.count_total ? o.sum_total / o.count_total : null };
    chartKeys.forEach(function(c) { out[c.avgKey] = o['count_' + c.avgKey] ? o['sum_' + c.avgKey] / o['count_' + c.avgKey] : null; });
    return out;
  });
}

/* LG Normal grey: Red 50 #fa312e, Gray 600-800 */
var CHART_SCORE_KEYS_B2B = [
  { key: 'avg_title', label: '1. Title', color: 'rgba(250,49,46,0.85)' },
  { key: 'avg_desc', label: '2. Description', color: 'rgba(250,49,46,0.65)' },
  { key: 'avg_h1', label: '3. H1', color: 'rgba(117,117,117,0.85)' },
  { key: 'avg_canon', label: '4. Canonical', color: 'rgba(97,97,97,0.8)' },
  { key: 'avg_alt', label: '5. Alt text', color: 'rgba(250,49,46,0.5)' }
];
var CHART_SCORE_KEYS_B2C = [
  { key: 'avg_ufn', label: '1. UFN', color: 'rgba(250,49,46,0.85)' },
  { key: 'avg_basic_assets', label: '2. Basic Assets', color: 'rgba(250,49,46,0.75)' },
  { key: 'avg_spec_summary', label: '3. Spec Summary', color: 'rgba(117,117,117,0.85)' },
  { key: 'avg_faq', label: '4. FAQ', color: 'rgba(97,97,97,0.8)' },
  { key: 'avg_title', label: '5. Tag <Title>', color: 'rgba(250,49,46,0.65)' },
  { key: 'avg_desc', label: '6. Tag <Description>', color: 'rgba(250,49,46,0.55)' },
  { key: 'avg_h1', label: '7. Tag <H1>', color: 'rgba(117,117,117,0.75)' },
  { key: 'avg_canon', label: '8. Tag <Canonical>', color: 'rgba(97,97,97,0.75)' },
  { key: 'avg_alt_feature', label: '9. Alt Feature', color: 'rgba(250,49,46,0.5)' },
  { key: 'avg_alt_front', label: '10. Alt Front', color: 'rgba(250,49,46,0.45)' }
];

function renderChartScoreByRegion(rows) {
  var ctx = document.getElementById('chartScoreByRegion');
  if (!ctx) return null;
  if (chartScoreByRegion) chartScoreByRegion.destroy();
  var rtype = currentReportType || 'B2B';
  var agg = aggregateByRegion(rows || [], rtype);
  var chartKeys = rtype === 'B2C' ? CHART_SCORE_KEYS_B2C : CHART_SCORE_KEYS_B2B;
  var labels = agg.map(function(a) { return a.region; });
  var datasets = chartKeys.map(function(item) {
    return {
      label: item.label,
      data: agg.map(function(a) { var v = a[item.key]; return v != null ? Math.round(v * 100) / 100 : null; }),
      backgroundColor: item.color
    };
  });
  chartScoreByRegion = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } },
      plugins: {
        legend: { position: 'top' },
        datalabels: {
          anchor: 'end',
          align: 'start',
          offset: 2,
          clamp: true,
          color: '#fff',
          font: { size: 9, weight: 'bold' },
          formatter: function(value) { return value != null ? Number(value).toFixed(1) : ''; },
          display: function(context) { return context.raw != null && context.raw >= 2; }
        }
      }
    }
  });
  return chartScoreByRegion;
}

var CHART_3MONTH_COLORS = ['rgba(250,49,46,0.85)', 'rgba(117,117,117,0.8)', 'rgba(97,97,97,0.75)'];

function renderChartTotalVsJul(monthsWithRows) {
  var ctx = document.getElementById('chartTotalVsJul');
  if (!ctx) return null;
  if (chartTotalVsJul) chartTotalVsJul.destroy();
  if (!monthsWithRows || !monthsWithRows.length) {
    chartTotalVsJul = new Chart(ctx.getContext('2d'), { type: 'bar', data: { labels: [], datasets: [] }, options: { responsive: true, maintainAspectRatio: false } });
    return chartTotalVsJul;
  }
  var aggPerMonth = monthsWithRows.map(function(m) { return aggregateByRegion(m.rows || [], currentReportType || 'B2B'); });
  var regionSet = {};
  aggPerMonth.forEach(function(agg) { agg.forEach(function(a) { if (a.region) regionSet[a.region] = true; }); });
  var labels = Object.keys(regionSet).sort();
  var datasets = monthsWithRows.map(function(m, i) {
    var agg = aggPerMonth[i] || [];
    var byRegion = {};
    agg.forEach(function(a) { byRegion[a.region] = a; });
    return {
      label: m.month || ('Month ' + (i + 1)),
      data: labels.map(function(reg) {
        var a = byRegion[reg];
        return (a && a.avg_total_score != null) ? Math.round(a.avg_total_score * 100) / 100 : null;
      }),
      backgroundColor: CHART_3MONTH_COLORS[i % CHART_3MONTH_COLORS.length]
    };
  });
  chartTotalVsJul = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } },
      plugins: {
        legend: { position: 'top' },
        datalabels: {
          anchor: 'end',
          align: 'start',
          offset: 2,
          clamp: true,
          color: '#212121',
          font: { size: 9, weight: 'bold' },
          formatter: function(value) { return value != null ? Number(value).toFixed(1) : ''; }
        }
      }
    }
  });
  return chartTotalVsJul;
}

var COUNTRY_REGION_LIST = ['ASIA', 'CIS', 'EU', 'INDIA', 'LATAM', 'MEA', 'NA'];

function renderCountryRegionSelector() {
  var el = document.getElementById('countryRegionSelector');
  if (!el) return;
  var regions = COUNTRY_REGION_LIST.slice();
  if (lastSummary && lastSummary.length) {
    var fromData = {};
    lastSummary.forEach(function(r) { var k = (r.region || '').trim(); if (k) fromData[k] = true; });
    Object.keys(fromData).forEach(function(k) { if (regions.indexOf(k) < 0) regions.push(k); });
  }
  regions.sort();
  if (regions.length && regions.indexOf(selectedCountryRegion) < 0) selectedCountryRegion = regions[0];
  el.innerHTML = regions.map(function(r) {
    var active = (r === selectedCountryRegion) ? ' active' : '';
    return '<button type="button" class="country-region-btn' + active + '" data-region="' + escapeHtml(r) + '">' + escapeHtml(r) + '</button>';
  }).join('');
  el.querySelectorAll('.country-region-btn').forEach(function(btn) {
    btn.onclick = function() {
      selectedCountryRegion = btn.getAttribute('data-region') || '';
      el.querySelectorAll('.country-region-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      renderCountryFilterSelect();
      renderChartScoreByCountry();
    };
  });
}

function renderCountryFilterSelect() {
  var sel = document.getElementById('countryFilterSelect');
  if (!sel) return;
  var rows = (lastSummary || []).filter(function(r) { return (r.region || '').trim() === selectedCountryRegion; });
  var keyCountry = (currentReportType || 'B2B') === 'B2C' ? 'division' : 'country';
  var countries = [];
  var seen = {};
  rows.forEach(function(r) {
    var c = (r[keyCountry] || r.country || r.division || '').trim();
    if (c && !seen[c]) { seen[c] = true; countries.push(c); }
  });
  countries.sort();
  var curVal = sel.value;
  sel.innerHTML = '<option value="">All</option>' + countries.map(function(c) {
    return '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</option>';
  }).join('');
  sel.value = curVal && countries.indexOf(curVal) >= 0 ? curVal : '';
  selectedCountryForChart = sel.value || '';
}

function renderChartScoreByCountry() {
  var ctx = document.getElementById('chartScoreByCountry');
  if (!ctx) return null;
  if (chartScoreByCountry) chartScoreByCountry.destroy();
  chartScoreByCountry = null;
  var rows = (lastSummary || []).filter(function(r) {
    if ((r.region || '').trim() !== selectedCountryRegion) return false;
    if (selectedCountryForChart) {
      var keyCountry = (currentReportType || 'B2B') === 'B2C' ? 'division' : 'country';
      var c = (r[keyCountry] || r.country || r.division || '').trim();
      return c === selectedCountryForChart;
    }
    return true;
  });
  var agg = aggregateByRegion(rows, currentReportType || 'B2B');
  var rtype = currentReportType || 'B2B';
  var chartKeys = rtype === 'B2C' ? CHART_SCORE_KEYS_B2C : CHART_SCORE_KEYS_B2B;
  var labels = chartKeys.map(function(k) { return k.label; });
  var first = agg.length ? agg[0] : null;
  var data = chartKeys.map(function(k) {
    var v = first ? first[k.key] : null;
    return v != null ? Math.round(v * 100) / 100 : null;
  });
  var barColor = 'rgba(250,49,46,0.85)';
  chartScoreByCountry = new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{ label: selectedCountryForChart || selectedCountryRegion || 'Region', data: data, backgroundColor: barColor }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, max: 10 } },
      plugins: {
        legend: { display: false },
        datalabels: {
          anchor: 'end',
          align: 'start',
          offset: 2,
          clamp: true,
          color: '#212121',
          font: { size: 9, weight: 'bold' },
          formatter: function(value) { return value != null ? Number(value).toFixed(1) : ''; }
        }
      }
    }
  });
  return chartScoreByCountry;
}

async function loadDashboard(reportType, month, regions, countries) {
  setSummaryTableHeader(reportType);
  var titleEl = document.getElementById('dashboardScoreTitle');
  var reportTitleEl = document.getElementById('dashboardReportTitle');
  if (titleEl) titleEl.textContent = 'Average Total Score by Region (' + reportType + ')';
  if (reportTitleEl) reportTitleEl.textContent = reportType + ' Monitoring Report by Country';
  var tableBody = document.getElementById('tableBodyB2B');
  var tableLoading = document.getElementById('tableLoadingB2B');
  var tableError = document.getElementById('tableErrorB2B');
  if (tableBody) tableBody.innerHTML = '';
  if (tableError) { tableError.style.display = 'none'; tableError.className = 'error'; tableError.innerHTML = ''; }
  showSkeleton('tableLoadingB2B', 'dashboard');
  if (tableLoading) tableLoading.style.display = 'block';
  try {
    var reports = await getReports();
    var currentMonthForFetch = resolveCurrentMonthForFetch(reports, reportType, month);
    var prevMonth = getImmediatelyPreviousMonth(reports, reportType, month);
    var summary = await getSummary(reportType, currentMonthForFetch, regions || [], countries || []);
    var summaryArr = Array.isArray(summary) ? summary : [];
    var prevArr = [];
    if (prevMonth) {
      try {
        var prevRes = await getSummary(reportType, prevMonth, regions || [], countries || []);
        prevArr = Array.isArray(prevRes) ? prevRes : [];
      } catch (e) { prevArr = []; }
    }
    assignRanksAndChange(summaryArr, prevArr, reportType);
    lastSummary = summaryArr;
    summaryTableSort = { colIndex: 3, dir: 1 };
    var filterType = (document.getElementById('tableScoreFilterB2B') || {}).value || '';
    var filtered = applyScoreFilter(summaryArr, filterType);
    var sorted = sortSummaryRows(filtered, summaryTableSort.colIndex, summaryTableSort.dir, reportType);
    renderScoreSummaryB2B(summaryArr);
    renderTableB2B(sorted);
    updateSummaryTableHeaderSortIcons();
    renderOperationalSummary(summaryArr, reportType);
    renderChartScoreByRegion(summaryArr);
    renderCountryRegionSelector();
    renderCountryFilterSelect();
    renderChartScoreByCountry();
    hideSkeleton('tableLoadingB2B');
    var tableLoading = document.getElementById('tableLoadingB2B');
    if (tableLoading) tableLoading.style.display = 'none';
    updateSummaryDateFields(currentMonthForFetch || month);
    renderChartTotalVsJul([]);
    (function loadTrendChart() {
      getReports().then(function(reports) {
        var allMonths = [...new Set((reports || []).filter(function(r) { return (r.report_type || r.reportType) === reportType; }).map(function(r) { return r.month; }))];
        function monthKey(m) {
          var match = (m || '').match(/^(\d{4})-M?(\d{1,2})$/i);
          return match ? parseInt(match[1], 10) * 12 + parseInt(match[2], 10) : 0;
        }
        allMonths.sort(function(a, b) { return monthKey(a) - monthKey(b); });
        var monthsForChart = allMonths.slice(-3);
        return Promise.all(monthsForChart.map(function(m) { return getSummary(reportType, m, regions || [], countries || []); })).then(function(rowsPerMonth) {
          var monthsWithRows = monthsForChart.map(function(m, i) { return { month: m, rows: Array.isArray(rowsPerMonth[i]) ? rowsPerMonth[i] : [] }; });
          if (currentReportType === reportType) renderChartTotalVsJul(monthsWithRows);
        });
      }).catch(function() {});
    })();
  } catch (e) {
    hideSkeleton('tableLoadingB2B');
    var tableErr = document.getElementById('tableErrorB2B');
    var tableLoad = document.getElementById('tableLoadingB2B');
    if (tableLoad) tableLoad.style.display = 'none';
    if (tableErr) {
      showErrorWithRetry(tableErr, 'Connection failed: ' + (e.message || String(e)), function() {
        loadDashboard(reportType, month, regions, countries);
      });
    }
  }
}

function downloadAsPdf() {
  var el = document.getElementById('dashboardB2B');
  if (!el || typeof html2canvas === 'undefined' || typeof jspdf === 'undefined') return;
  html2canvas(el, { scale: 2, useCORS: true, logging: false }).then(function(canvas) {
    var imgData = canvas.toDataURL('image/png');
    var pdf = new jspdf.jsPDF('p', 'mm', 'a4');
    var pdfW = pdf.internal.pageSize.getWidth();
    var pdfH = pdf.internal.pageSize.getHeight();
    var margin = 10;
    var maxW = pdfW - margin * 2;
    var maxH = pdfH - margin * 2;
    var imgW = maxW;
    var imgH = (canvas.height * imgW) / canvas.width;
    if (imgH > maxH) { imgH = maxH; imgW = (canvas.width * imgH) / canvas.height; }
    pdf.addImage(imgData, 'PNG', margin, margin, imgW, imgH);
    var month = getMonthParam() || '';
    pdf.save('LG_ES_Monitoring_' + currentReportType + '_' + (month || 'report') + '.pdf');
  }).catch(function(err) { console.error(err); alert('An error occurred while generating PDF.'); });
}

function buildRawDownloadParams() {
  var q = new URLSearchParams();
  q.set('report_type', currentReportType);
  getSelectedRegions().forEach(function(r) { q.append('region', r); });
  getSelectedCountries().forEach(function(c) { q.append('country', c); });
  return q.toString();
}

function parseCSVToRows(csvText) {
  var rows = [];
  var lines = csvText.split(/\r?\n/);
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    var fields = [];
    var idx = 0;
    while (idx < line.length) {
      if (line[idx] === '"') {
        var end = idx + 1;
        var s = '';
        while (end < line.length) {
          if (line[end] === '"') {
            if (line[end + 1] === '"') { s += '"'; end += 2; continue; }
            break;
          }
            s += line[end]; end++;
        }
        fields.push(s);
        idx = end + 1;
        if (idx < line.length && line[idx] === ',') idx++;
        continue;
      }
      var comma = line.indexOf(',', idx);
      if (comma === -1) { fields.push(line.slice(idx)); break; }
      fields.push(line.slice(idx, comma));
      idx = comma + 1;
    }
    rows.push(fields);
  }
  return rows;
}

var EXCEL_HEADER_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFEFE6E6' } };
var EXCEL_BORDER_THIN = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };

function applySheetStyle(worksheet, headerRowIndex) {
  worksheet.eachRow(function(row, rowNumber) {
    row.eachCell(function(cell) {
      cell.border = EXCEL_BORDER_THIN;
      if (rowNumber === headerRowIndex) {
        cell.fill = EXCEL_HEADER_FILL;
        cell.font = { bold: true };
      }
    });
  });
}

function downloadAsExcel() {
  if (!lastSummary.length) {
    alert('No table data to download.');
    return;
  }
  var month = getMonthParam() || '';
  var periodLabel = month ? 'Period: ' + month : 'Period: latest';
  var cols = currentReportType === 'B2C' ? SUMMARY_TABLE_COLS_B2C : SUMMARY_TABLE_COLS_B2B;
  var headers = cols.map(function(c) { return c.label; });
  var summaryDataRows = lastSummary.map(function(r) {
    return cols.map(function(c) {
      if (c.key === '_rank') return r.rank != null ? r.rank : '';
      if (c.key === '_rank_change') {
        if (r.rankChange == null || r.rankChange === '') return '—';
        var n = Number(r.rankChange);
        return n > 0 ? '▼ ' + n : (n < 0 ? '▲ ' + Math.abs(n) : '—');
      }
      return getRowCellValue(r, c);
    });
  });

  function buildWithExcelJS(rawRows) {
    if (typeof ExcelJS === 'undefined') return buildWithXLSX(rawRows);
    var wb = new ExcelJS.Workbook();
    wb.creator = 'LG ES Monitoring';
    var wsSummary = wb.addWorksheet('Summary', { views: [{ showGridLines: true }] });
    wsSummary.getCell(1, 1).value = periodLabel;
    wsSummary.getCell(1, 1).font = { bold: true };
    wsSummary.addRow(headers);
    summaryDataRows.forEach(function(row) { wsSummary.addRow(row); });
    var summaryHeaderRowIndex = 2;
    applySheetStyle(wsSummary, summaryHeaderRowIndex);

    if (rawRows && rawRows.length) {
      var wsRaw = wb.addWorksheet('Raw', { views: [{ showGridLines: true }] });
      wsRaw.getCell(1, 1).value = periodLabel;
      wsRaw.getCell(1, 1).font = { bold: true };
      rawRows.forEach(function(row, i) { wsRaw.addRow(row); });
      applySheetStyle(wsRaw, 2);
    }

    return wb.xlsx.writeBuffer().then(function(buffer) {
      var blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'LG_ES_Monitoring_' + currentReportType + '_' + (month || 'report') + '.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  function buildWithXLSX(rawRows) {
    var summaryRows = lastSummary.map(function(r) {
      var row = {};
      cols.forEach(function(c) {
        var label = c.label;
        if (c.key === '_rank') row[label] = r.rank != null ? r.rank : '';
        else if (c.key === '_rank_change') {
          if (r.rankChange == null || r.rankChange === '') row[label] = '—';
          else { var n = Number(r.rankChange); row[label] = n > 0 ? '▼ ' + n : (n < 0 ? '▲ ' + Math.abs(n) : '—'); }
        } else row[label] = getRowCellValue(r, c);
      });
      return row;
    });
    var wsSummary = XLSX.utils.json_to_sheet(summaryRows);
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, wsSummary, 'Summary');
    if (rawRows && rawRows.length && typeof XLSX !== 'undefined') {
      var wsRaw = XLSX.utils.aoa_to_sheet(rawRows);
      XLSX.utils.book_append_sheet(wb, wsRaw, 'Raw');
    }
    XLSX.writeFile(wb, 'LG_ES_Monitoring_' + currentReportType + '_' + (month || 'report') + '.xlsx');
    return Promise.resolve();
  }

  var rawUrl = API + '/api/raw/download?' + buildRawDownloadParams();
  fetchWithAuth(rawUrl).then(function(res) {
    if (!res.ok) return Promise.reject(new Error('Could not load Raw data.'));
    return res.text();
  }).then(function(csvText) {
    var rawRows = (csvText && csvText.trim()) ? parseCSVToRows(csvText.trim()) : null;
    return buildWithExcelJS(rawRows);
  }).catch(function(err) {
    console.error(err);
    return buildWithExcelJS(null).then(function() {
      alert('Saved Summary sheet only. Could not load Raw data.');
    });
  }).then(function() {
    fetchWithAuth(API + '/api/admin/log-download', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ download_type: 'Excel (Summary + Raw)', period_or_detail: periodLabel }) }).catch(function() {});
  });
}

var MULTISELECT_ACTIONS_HTML = '<div class="multiselect-panel-actions"><button type="button" class="multiselect-select-all" title="Select all" aria-label="Select all"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg></button><button type="button" class="multiselect-deselect-all" title="Deselect all" aria-label="Deselect all"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/></svg></button></div>';

function fillRegionCountryPanels(regions, countries, autoSelectAllCountries) {
  var rPanel = document.getElementById('regionB2BPanel');
  var cPanel = document.getElementById('countryB2BPanel');
  var selectedR = getSelectedRegions();
  var selectedC = getSelectedCountries();
  if (rPanel) rPanel.innerHTML = MULTISELECT_ACTIONS_HTML + (regions || []).map(function(r) { var checked = selectedR.indexOf(r) !== -1 ? ' checked' : ''; return '<label><input type="checkbox" value="' + escapeHtml(r) + '"' + checked + '> ' + escapeHtml(r) + '</label>'; }).join('');
  if (cPanel) {
    var countryList = countries || [];
    if (autoSelectAllCountries && countryList.length) selectedC = countryList;
    cPanel.innerHTML = MULTISELECT_ACTIONS_HTML + countryList.map(function(c) { var checked = selectedC.indexOf(c) !== -1 ? ' checked' : ''; return '<label><input type="checkbox" value="' + escapeHtml(c) + '"' + checked + '> ' + escapeHtml(c) + '</label>'; }).join('');
  }
  updateMultiselectButtonLabels(regions, countries);
}

async function loadChecklist(month) {
  var wrap = document.getElementById('checklistTableWrap'), loading = document.getElementById('checklistLoading'), err = document.getElementById('checklistError'), tbody = document.getElementById('checklistTableBody');
  if (wrap) wrap.style.display = 'none';
  if (err) { err.style.display = 'none'; err.textContent = ''; err.className = 'error'; }
  showSkeleton('checklistLoading', 'table');
  try {
    var rows = await getChecklist(month);
    hideSkeleton('checklistLoading');
    if (loading) loading.style.display = 'none';
    if (!Array.isArray(rows) || rows.length === 0) {
      if (err) { err.style.display = 'block'; err.textContent = 'No data.'; }
      return;
    }
    var colCount = Math.max.apply(null, rows.map(function(r) { return Array.isArray(r) ? r.length : 0; })) || 1;
    tbody.innerHTML = rows.map(function(row) {
      var arr = Array.isArray(row) ? row : [];
      return '<tr>' + Array.from({ length: colCount }, function(_, i) { return '<td>' + escapeHtml(i < arr.length && arr[i] != null ? String(arr[i]) : '') + '</td>'; }).join('') + '</tr>';
    }).join('');
    if (wrap) wrap.style.display = 'block';
  } catch (e) {
    hideSkeleton('checklistLoading');
    if (loading) loading.style.display = 'none';
    if (err) {
      showErrorWithRetry(err, 'Load failed: ' + (e.message || String(e)), function() { loadChecklist(month); });
    }
  }
}

(async function init() {
  // Lv1/Lv2 tabs and filter row are always bound regardless of API result
  var contentMonitoringItem = document.getElementById('contentMonitoringItem');
  var contentSummary = document.getElementById('contentSummary');
  var contentNotice = document.getElementById('contentNotice');
  var contentQna = document.getElementById('contentQna');
  var contentMonitoringDetail = document.getElementById('contentMonitoringDetail');
  var contentChecklist = document.getElementById('contentChecklist');
  var subNavMonitoringItem = document.getElementById('subNavMonitoringItem');
  var subNavSummary = document.getElementById('subNavSummary');
  var subNavB2C = document.getElementById('subNavB2C');
  var subNavB2B = document.getElementById('subNavB2B');
  var subNavInfo = document.getElementById('subNavInfo');
  var filtersRowEl = document.getElementById('headerFiltersRow');
  var summarySubRow = document.getElementById('summarySubRow');

  var _allContentPanels = [contentMonitoringItem, contentSummary, contentNotice, contentQna, contentMonitoringDetail, contentChecklist];
  function switchContentPanel(activeEl) {
    _allContentPanels.forEach(function(el) {
      if (!el) return;
      if (el === activeEl) {
        el.style.display = 'block';
        el.offsetHeight;
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });
  }

  function saveViewState(gnbId, subTabId) {
    try { sessionStorage.setItem('lg_es_pro_view', JSON.stringify({ gnb: gnbId || 'gnbSummary', subTab: subTabId || 'tabScoreByRegion' })); } catch (e) {}
  }
  function restoreViewState() {
    try {
      var raw = sessionStorage.getItem('lg_es_pro_view');
      var gnb = 'gnbMonitoringItem';
      if (raw) {
        try {
          var state = JSON.parse(raw);
          gnb = (state && state.gnb) || 'gnbMonitoringItem';
        } catch (e) {}
      }
      if (gnb === 'gnbMonitoringItem') {
        showLv1MonitoringItem();
        updateGnbActive('gnbMonitoringItem');
        updatePageTitle('ES Content Monitoring DashBoard');
        var t = document.getElementById('tabMonitoringB2C');
        if (t) t.click();
      } else if (gnb === 'gnbB2C') {
        showLv1B2C();
        updateGnbActive('gnbB2C');
        updatePageTitle('ES Content Monitoring DashBoard');
        var t = document.getElementById('tabB2CAll');
        if (t) t.click();
      } else if (gnb === 'gnbB2B') {
        showLv1B2B();
        updateGnbActive('gnbB2B');
        updatePageTitle('ES Content Monitoring DashBoard');
        var t = document.getElementById('tabB2BAll');
        if (t) t.click();
      } else if (gnb === 'gnbFaq') {
        showLv1Info('notice');
        updateGnbActive('gnbFaq');
        updatePageTitle('ES Content Monitoring DashBoard');
      } else {
        showLv1Summary();
        updateGnbActive('gnbSummary');
        updatePageTitle('ES Content Monitoring DashBoard');
        var t = document.getElementById('tabScoreByRegion');
        if (t) t.click();
      }
    } catch (e) {}
  }

  var meRes = await fetchWithAuth(API + '/auth/me').then(function(r) { return r.json(); }).catch(function() { return {}; });
  currentUser.username = meRes.username || '';
  currentUser.role = meRes.role || 'user';
  (function renderGnbUserProfile() {
    var u = (currentUser.username || '').trim();
    var displayName = u ? (u.split(/[\s._-]/).map(function(s) { return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase(); }).join(' ')) : '-';
    var parts = u.split(/[\s._-]+/).filter(Boolean);
    var initials = u ? (parts.length >= 2 ? parts.slice(0, 2).map(function(s) { return (s.charAt(0) || '').toUpperCase(); }).join('') : u.slice(0, 2).toUpperCase()) : '--';
    var accountLabel = currentUser.role === 'admin' ? 'Admin' : 'User';
    var avatarEl = document.getElementById('gnbUserAvatar');
    var nameEl = document.getElementById('gnbUserName');
    var accountEl = document.getElementById('gnbUserAccount');
    if (avatarEl) avatarEl.textContent = initials;
    if (nameEl) nameEl.textContent = displayName;
    if (accountEl) accountEl.textContent = accountLabel;
  })();
  var linkLogin = document.getElementById('linkLogin');
  var btnLogoutSidebar = document.getElementById('btnLogoutSidebar');
  if (linkLogin) linkLogin.style.display = currentUser.username ? 'none' : '';
  if (btnLogoutSidebar) btnLogoutSidebar.style.display = currentUser.username ? '' : 'none';
  var tabPageAdminUsers = document.getElementById('tabPageAdminUsers');
  var contentAdminUsers = document.getElementById('contentAdminUsers');
  var dashboardSubNav = null;
  if (currentUser.role === 'admin' && tabPageAdminUsers) tabPageAdminUsers.style.display = '';
  var noticeWriteBtn = document.getElementById('noticeWriteBtn');
  if (noticeWriteBtn) noticeWriteBtn.style.display = currentUser.role === 'admin' ? '' : 'none';
  window._noticeList = window._noticeList || [];

  function showDashboardPage() {
    if (tabPageAdminUsers) tabPageAdminUsers.classList.remove('active');
    if (summarySubRow) summarySubRow.style.display = '';
    switchContentSection(contentSummary, allContentSections());
    var panel = document.getElementById('summaryPanelDashboard');
    if (panel) { document.querySelectorAll('.summary-sub-panel').forEach(function(p) { p.classList.remove('active'); }); panel.style.display = 'block'; void panel.offsetHeight; panel.classList.add('active'); }
    document.getElementById('tabSummary').classList.add('active');
    document.getElementById('tabInfo').classList.remove('active');
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = 'none';
    if (subNavSummary) subNavSummary.style.display = '';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (subNavInfo) subNavInfo.style.display = 'none';
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = '';
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = 'none';
  }
  function showAdminPage(showUsageLogs) {
    if (tabPageAdminUsers) tabPageAdminUsers.classList.add('active');
    if (summarySubRow) summarySubRow.style.display = '';
    switchContentSection(contentAdminUsers, allContentSections());
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = 'none';
    var tabUsers = document.getElementById('tabAdminUsers');
    var tabUsageLogs = document.getElementById('tabAdminUsageLogs');
    var panelUsers = document.getElementById('adminPanelUsers');
    var panelUsageLogs = document.getElementById('adminPanelUsageLogs');
    if (showUsageLogs && panelUsageLogs && tabUsageLogs) {
      if (panelUsers) panelUsers.classList.remove('active');
      panelUsageLogs.classList.add('active');
      if (tabUsers) tabUsers.classList.remove('active');
      tabUsageLogs.classList.add('active');
      loadAdminUsageLogs();
    } else {
      if (panelUsageLogs) panelUsageLogs.classList.remove('active');
      if (panelUsers) panelUsers.classList.add('active');
      if (tabUsageLogs) tabUsageLogs.classList.remove('active');
      if (tabUsers) tabUsers.classList.add('active');
      loadAdminUsers();
    }
  }
  function showAdminSubTab(which) {
    var panelUsers = document.getElementById('adminPanelUsers');
    var panelUsageLogs = document.getElementById('adminPanelUsageLogs');
    var tabUsers = document.getElementById('tabAdminUsers');
    var tabUsageLogs = document.getElementById('tabAdminUsageLogs');
    if (which === 'usage') {
      if (panelUsers) panelUsers.classList.remove('active');
      if (panelUsageLogs) panelUsageLogs.classList.add('active');
      if (tabUsers) tabUsers.classList.remove('active');
      if (tabUsageLogs) tabUsageLogs.classList.add('active');
      loadAdminUsageLogs();
    } else {
      if (panelUsageLogs) panelUsageLogs.classList.remove('active');
      if (panelUsers) panelUsers.classList.add('active');
      if (tabUsageLogs) tabUsageLogs.classList.remove('active');
      if (tabUsers) tabUsers.classList.add('active');
      loadAdminUsers();
    }
  }
  if (tabPageAdminUsers) tabPageAdminUsers.addEventListener('click', function(e) { e.preventDefault(); if (currentUser.role !== 'admin') return; showAdminPage(false); });
  var tabAdminUsageLogs = document.getElementById('tabAdminUsageLogs');
  var tabAdminUsers = document.getElementById('tabAdminUsers');
  if (tabAdminUsageLogs) tabAdminUsageLogs.addEventListener('click', function(e) { e.preventDefault(); showAdminSubTab('usage'); });
  if (tabAdminUsers) tabAdminUsers.addEventListener('click', function(e) { e.preventDefault(); showAdminSubTab('users'); });
  var linkToHome = document.getElementById('linkToHome');
  if (linkToHome) linkToHome.addEventListener('click', function(e) { e.preventDefault(); showLv1Summary(); var t = document.getElementById('tabScoreByRegion'); if (t) t.click(); updateGnbActive('gnbSummary'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbSummary', 'tabScoreByRegion'); });

  var allContentSections = function() { return [contentMonitoringItem, contentSummary, contentNotice, contentQna, contentMonitoringDetail, contentChecklist, contentAdminUsers]; };

  function showLv1Summary() {
    if (contentAdminUsers && contentAdminUsers.classList.contains('active')) {
      showDashboardPage();
      return;
    }
    var tabSummary = document.getElementById('tabSummary');
    var tabInfo = document.getElementById('tabInfo');
    if (tabSummary) tabSummary.classList.add('active');
    if (tabInfo) tabInfo.classList.remove('active');
    switchContentSection(contentSummary, allContentSections());
    if (summarySubRow) summarySubRow.style.display = '';
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = 'none';
    if (subNavSummary) subNavSummary.style.display = '';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (subNavInfo) subNavInfo.style.display = 'none';
    if (filtersRowEl) filtersRowEl.style.display = '';
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = '';
    document.querySelectorAll('.summary-sub-panel').forEach(function(p) { p.classList.remove('active'); });
    var panel = document.getElementById('summaryPanelDashboard');
    if (panel) { panel.style.display = 'block'; void panel.offsetHeight; panel.classList.add('active'); }
  }
  function showLv1MonitoringItem() {
    if (contentAdminUsers && contentAdminUsers.classList.contains('active')) { return; }
    switchContentSection(contentMonitoringItem, allContentSections());
    if (summarySubRow) summarySubRow.style.display = '';
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = '';
    if (subNavSummary) subNavSummary.style.display = 'none';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (subNavInfo) subNavInfo.style.display = 'none';
    if (filtersRowEl) filtersRowEl.style.display = 'none';
    var tabB2C = document.getElementById('tabMonitoringB2C');
    var tabB2B = document.getElementById('tabMonitoringB2B');
    var pmB2C = document.getElementById('panelMonitoringB2C');
    var pmB2B = document.getElementById('panelMonitoringB2B');
    if (tabB2C) tabB2C.classList.add('active');
    if (tabB2B) tabB2B.classList.remove('active');
    if (pmB2C) pmB2C.classList.add('active');
    if (pmB2B) pmB2B.classList.remove('active');
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = 'none';
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = 'none';
  }
  function showLv1B2C() {
    if (contentAdminUsers && contentAdminUsers.classList.contains('active')) { return; }
    switchContentSection(contentSummary, allContentSections());
    if (summarySubRow) summarySubRow.style.display = '';
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = 'none';
    if (subNavSummary) subNavSummary.style.display = 'none';
    if (subNavB2C) subNavB2C.style.display = '';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (subNavInfo) subNavInfo.style.display = 'none';
    if (filtersRowEl) filtersRowEl.style.display = '';
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = '';
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = '';
    var panel = document.getElementById('summaryPanelDashboard');
    if (panel) { document.querySelectorAll('.summary-sub-panel').forEach(function(p) { p.classList.remove('active'); }); panel.classList.add('active'); }
    if (typeof currentReportType !== 'undefined') currentReportType = 'B2C';
    getReports().then(function(reports) {
      var firstMonth = fillYearMonthSelect('B2C', reports);
      var month = getMonthParam() || firstMonth || 'latest';
      return getFilters('B2C', month, []).then(function(f) {
        fillRegionCountryPanels(f.regions || [], f.countries || [], false);
        if (month) return loadDashboard('B2C', getMonthParam() || month, [], []);
      });
    });
  }
  function showLv1B2B() {
    if (contentAdminUsers && contentAdminUsers.classList.contains('active')) { return; }
    switchContentSection(contentSummary, allContentSections());
    if (summarySubRow) summarySubRow.style.display = '';
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = 'none';
    if (subNavSummary) subNavSummary.style.display = 'none';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = '';
    if (subNavInfo) subNavInfo.style.display = 'none';
    if (filtersRowEl) filtersRowEl.style.display = '';
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = '';
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = '';
    var panel = document.getElementById('summaryPanelDashboard');
    if (panel) { document.querySelectorAll('.summary-sub-panel').forEach(function(p) { p.classList.remove('active'); }); panel.classList.add('active'); }
    if (typeof currentReportType !== 'undefined') currentReportType = 'B2B';
    getReports().then(function(reports) {
      var firstMonth = fillYearMonthSelect('B2B', reports);
      var month = getMonthParam() || firstMonth || 'latest';
      return getFilters('B2B', month, []).then(function(f) {
        fillRegionCountryPanels(f.regions || [], f.countries || [], false);
        if (month) return loadDashboard('B2B', getMonthParam() || month, [], []);
      });
    });
  }
  function showLv1Info(activeInfoSub) {
    if (contentAdminUsers && contentAdminUsers.classList.contains('active')) {
      if (tabPageAdminUsers) tabPageAdminUsers.classList.remove('active');
      contentAdminUsers.classList.remove('active');
      contentAdminUsers.style.display = 'none';
      if (summarySubRow) summarySubRow.style.display = '';
    }
    document.getElementById('tabSummary').classList.remove('active');
    document.getElementById('tabInfo').classList.add('active');
    if (subNavMonitoringItem) subNavMonitoringItem.style.display = 'none';
    if (subNavSummary) subNavSummary.style.display = 'none';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (subNavInfo) subNavInfo.style.display = '';
    if (filtersRowEl) filtersRowEl.style.display = 'none';
    var reportDateFieldEl = document.getElementById('reportDateField');
    if (reportDateFieldEl) reportDateFieldEl.style.display = 'none';
    var summaryTableSection = document.getElementById('summaryTableSection');
    if (summaryTableSection) summaryTableSection.style.display = 'none';
    var tabs = ['tabNotice', 'tabQna'];
    tabs.forEach(function(id) { var el = document.getElementById(id); if (el) el.classList.remove('active'); });
    var activeContent = activeInfoSub === 'notice' ? contentNotice : contentQna;
    switchContentSection(activeContent, allContentSections());
    if (activeInfoSub === 'notice') {
      document.getElementById('tabNotice').classList.add('active');
      loadNoticeList();
    } else {
      document.getElementById('tabQna').classList.add('active');
      loadQnaList();
    }
  }

  function loadNoticeList() {
    var table = document.getElementById('noticeTable');
    var tbody = document.getElementById('noticeTableBody');
    var listWrap = document.getElementById('noticeListWrap');
    var detailWrap = document.getElementById('noticeDetailWrap');
    var emptyEl = document.getElementById('noticeEmpty');
    if (detailWrap) detailWrap.style.display = 'none';
    if (listWrap) listWrap.style.display = '';
    if (!tbody) return;
    tbody.innerHTML = '';
    var list = (window._noticeList || []).slice().sort(function(a, b) { return (b.id || 0) - (a.id || 0); });
    if (list.length === 0) {
      if (table) table.style.display = 'none';
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }
    if (table) table.style.display = 'table';
    if (emptyEl) emptyEl.style.display = 'none';
    list.forEach(function(item, idx) {
      var tr = document.createElement('tr');
      tr.setAttribute('data-notice-id', String(item.id));
      tr.style.cursor = 'pointer';
      tr.innerHTML = '<td class="th-num">' + (idx + 1) + '</td><td class="th-title">' + escapeHtml(item.title || '') + '</td><td class="th-date">' + (item.date || '') + '</td>';
      tr.addEventListener('click', function() { showNoticeDetail(item.id); });
      tbody.appendChild(tr);
    });
  }
  function escapeHtml(s) {
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
  function showNoticeDetail(id) {
    var list = window._noticeList || [];
    var item = list.find(function(n) { return n.id === id; });
    if (!item) return;
    document.getElementById('noticeListWrap').style.display = 'none';
    document.getElementById('noticeDetailWrap').style.display = 'block';
    document.getElementById('noticeDetailTitle').textContent = item.title || '';
    document.getElementById('noticeDetailDate').textContent = item.date || '';
    document.getElementById('noticeDetailBody').textContent = item.body || '';
    var delBtn = document.getElementById('noticeDetailDelete');
    if (delBtn) {
      delBtn.style.display = currentUser.role === 'admin' ? '' : 'none';
      delBtn.dataset.noticeId = String(id);
    }
  }
  function loadQnaList() {
    var table = document.getElementById('qnaTable');
    var tbody = document.getElementById('qnaTableBody');
    var emptyEl = document.getElementById('qnaEmpty');
    if (tbody) tbody.innerHTML = '';
    if (table) table.style.display = 'none';
    if (emptyEl) emptyEl.style.display = 'block';
  }

  function updateGnbActive(gnbId) {
    var links = document.querySelectorAll('.gnb-nav a');
    links.forEach(function(a) { a.classList.remove('active'); });
    var el = document.getElementById(gnbId);
    if (el) el.classList.add('active');
  }
  function updatePageTitle(title) {
    var el = document.getElementById('pageTitle');
    if (el) el.textContent = 'ES Content Monitoring DashBoard';
  }
  document.getElementById('tabSummary').onclick = function(e) { e.preventDefault(); showLv1Summary(); };
  document.getElementById('tabInfo').onclick = function(e) { e.preventDefault(); showLv1Info('notice'); };
  document.getElementById('tabNotice').onclick = function(e) { e.preventDefault(); showLv1Info('notice'); };
  document.getElementById('tabQna').onclick = function(e) { e.preventDefault(); showLv1Info('qna'); };
  var gnbMonitoringItem = document.getElementById('gnbMonitoringItem');
  if (gnbMonitoringItem) gnbMonitoringItem.onclick = function(e) { e.preventDefault(); showLv1MonitoringItem(); updateGnbActive('gnbMonitoringItem'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbMonitoringItem', 'tabMonitoringB2C'); };
  var tabMonitoringB2C = document.getElementById('tabMonitoringB2C');
  var tabMonitoringB2B = document.getElementById('tabMonitoringB2B');
  var panelMonitoringB2C = document.getElementById('panelMonitoringB2C');
  var panelMonitoringB2B = document.getElementById('panelMonitoringB2B');
  if (tabMonitoringB2C) tabMonitoringB2C.onclick = function(e) {
    e.preventDefault();
    if (tabMonitoringB2C) tabMonitoringB2C.classList.add('active');
    if (tabMonitoringB2B) tabMonitoringB2B.classList.remove('active');
    if (panelMonitoringB2C) panelMonitoringB2C.classList.add('active');
    if (panelMonitoringB2B) panelMonitoringB2B.classList.remove('active');
  };
  if (tabMonitoringB2B) tabMonitoringB2B.onclick = function(e) {
    e.preventDefault();
    if (tabMonitoringB2C) tabMonitoringB2C.classList.remove('active');
    if (tabMonitoringB2B) tabMonitoringB2B.classList.add('active');
    if (panelMonitoringB2C) panelMonitoringB2C.classList.remove('active');
    if (panelMonitoringB2B) panelMonitoringB2B.classList.add('active');
  };
  var gnbSummary = document.getElementById('gnbSummary');
  if (gnbSummary) gnbSummary.onclick = function(e) { e.preventDefault(); showLv1Summary(); var tab = document.getElementById('tabScoreByRegion'); if (tab) tab.click(); updateGnbActive('gnbSummary'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbSummary', 'tabScoreByRegion'); };
  var gnbB2B = document.getElementById('gnbB2B');
  if (gnbB2B) gnbB2B.onclick = function(e) { e.preventDefault(); showLv1B2B(); var t = document.getElementById('tabB2BAll'); if (t) t.click(); updateGnbActive('gnbB2B'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbB2B', 'tabB2BAll'); };
  var gnbB2C = document.getElementById('gnbB2C');
  if (gnbB2C) gnbB2C.onclick = function(e) { e.preventDefault(); showLv1B2C(); var t = document.getElementById('tabB2CAll'); if (t) t.click(); updateGnbActive('gnbB2C'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbB2C', 'tabB2CAll'); };
  var gnbMonitoringDetail = document.getElementById('gnbMonitoringDetail');
  if (gnbMonitoringDetail) gnbMonitoringDetail.onclick = function(e) { e.preventDefault(); showLv1Info('monitoring'); updateGnbActive('gnbMonitoringDetail'); updatePageTitle('Monitoring Detail'); };
  var gnbFaq = document.getElementById('gnbFaq');
  if (gnbFaq) gnbFaq.onclick = function(e) { e.preventDefault(); showLv1Info('notice'); updateGnbActive('gnbFaq'); updatePageTitle('ES Content Monitoring DashBoard'); saveViewState('gnbFaq', 'tabNotice'); };
  var gnbChecklist = document.getElementById('gnbChecklist');
  if (gnbChecklist) gnbChecklist.onclick = function(e) { e.preventDefault(); showLv1Info('checklist'); updateGnbActive('gnbChecklist'); updatePageTitle('Checklist & Criteria'); };

  var noticeDetailBack = document.getElementById('noticeDetailBack');
  if (noticeDetailBack) noticeDetailBack.onclick = function() {
    document.getElementById('noticeDetailWrap').style.display = 'none';
    document.getElementById('noticeListWrap').style.display = '';
  };
  var noticeDetailDelete = document.getElementById('noticeDetailDelete');
  if (noticeDetailDelete) noticeDetailDelete.onclick = function() {
    var id = parseInt(noticeDetailDelete.dataset.noticeId, 10);
    if (!id) return;
    if (!confirm('Delete this notice?')) return;
    window._noticeList = (window._noticeList || []).filter(function(n) { return n.id !== id; });
    document.getElementById('noticeDetailWrap').style.display = 'none';
    document.getElementById('noticeListWrap').style.display = '';
    loadNoticeList();
  };
  var noticeWriteModalOverlay = document.getElementById('noticeWriteModalOverlay');
  if (noticeWriteBtn) noticeWriteBtn.onclick = function() {
    document.getElementById('noticeWriteTitle').value = '';
    document.getElementById('noticeWriteBody').value = '';
    var errEl = document.getElementById('noticeWriteError');
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    if (noticeWriteModalOverlay) noticeWriteModalOverlay.classList.add('show');
  };
  var noticeWriteCancel = document.getElementById('noticeWriteCancel');
  if (noticeWriteCancel) noticeWriteCancel.onclick = function() {
    if (noticeWriteModalOverlay) noticeWriteModalOverlay.classList.remove('show');
  };
  var noticeWriteSubmit = document.getElementById('noticeWriteSubmit');
  if (noticeWriteSubmit) noticeWriteSubmit.onclick = function() {
    var title = (document.getElementById('noticeWriteTitle') || {}).value || '';
    var body = (document.getElementById('noticeWriteBody') || {}).value || '';
    var errEl = document.getElementById('noticeWriteError');
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    if (!title.trim()) { if (errEl) { errEl.textContent = 'Please enter a title.'; errEl.style.display = 'block'; } return; }
    var id = Date.now();
    var date = new Date().toISOString().slice(0, 10);
    window._noticeList = window._noticeList || [];
    window._noticeList.push({ id: id, title: title.trim(), body: body.trim(), date: date });
    if (noticeWriteModalOverlay) noticeWriteModalOverlay.classList.remove('show');
    loadNoticeList();
  };
  if (noticeWriteModalOverlay) noticeWriteModalOverlay.onclick = function(e) {
    if (e.target === noticeWriteModalOverlay) noticeWriteModalOverlay.classList.remove('show');
  };
  var qnaSubmitBtn = document.getElementById('qnaSubmitBtn');
  if (qnaSubmitBtn) qnaSubmitBtn.onclick = function() {
    var subject = (document.getElementById('qnaSubject') || {}).value || '';
    var content = (document.getElementById('qnaContent') || {}).value || '';
    var errEl = document.getElementById('qnaSubmitError');
    var okEl = document.getElementById('qnaSubmitSuccess');
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    if (okEl) okEl.style.display = 'none';
    if (!subject.trim()) { if (errEl) { errEl.textContent = 'Please enter a subject.'; errEl.style.display = 'block'; } return; }
    if (!content.trim()) { if (errEl) { errEl.textContent = 'Please enter content.'; errEl.style.display = 'block'; } return; }
    if (okEl) okEl.style.display = 'block';
    document.getElementById('qnaAuthor').value = '';
    document.getElementById('qnaEmail').value = '';
    document.getElementById('qnaSubject').value = '';
    document.getElementById('qnaContent').value = '';
  };

  function loadAdminUsers() {
    var wrap = document.getElementById('adminUsersTableWrap');
    var loading = document.getElementById('adminUsersLoading');
    var errEl = document.getElementById('adminUsersError');
    var tbody = document.getElementById('adminUsersTableBody');
    var roleFilter = (document.getElementById('adminUsersRoleFilter') || {}).value || '';
    var statusFilter = (document.getElementById('adminUsersStatusFilter') || {}).value || '';
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; errEl.className = 'error'; }
    if (wrap) wrap.style.display = 'none';
    showSkeleton('adminUsersLoading', 'table');
    var q = '?limit=300&offset=0';
    if (roleFilter) q += '&role=' + encodeURIComponent(roleFilter);
    if (statusFilter === 'pending') q += '&pending_only=true';
    else if (statusFilter === 'active') q += '&active_only=true';
    fetchWithAuth(API + '/api/admin/users' + q)
      .then(function(r) {
        if (r.status === 403) { throw new Error('Permission denied.'); }
        if (!r.ok) return r.text().then(function(t) { try { var b = JSON.parse(t); throw new Error(b.detail || t); } catch (e) { if (e instanceof Error && e.message && e.message !== t) throw e; throw new Error(t || 'Request failed (status ' + r.status + ')'); } });
        return r.json();
      })
      .then(function(data) {
        hideSkeleton('adminUsersLoading');
        if (loading) loading.style.display = 'none';
        var items = data.items || [];
        var total = data.total != null ? data.total : items.length;
        tbody.innerHTML = items.map(function(u) {
          var roleBadge = u.role === 'admin' ? '<span class="badge badge-admin">Admin</span>' : '<span class="badge badge-user">User</span>';
          var statusBadge = u.is_active ? '<span class="badge badge-active">Active</span>' : '<span class="badge badge-inactive">Inactive</span>';
          var created = (u.created_at || '').slice(0, 10);
          var roleBtn = u.role === 'admin'
            ? '<button type="button" class="btn-role" data-id="' + u.id + '" data-role="user">Set User</button>'
            : '<button type="button" class="btn-role" data-id="' + u.id + '" data-role="admin">Set Admin</button>';
          var activeBtn = u.is_active
            ? '<button type="button" class="btn-active" data-id="' + u.id + '" data-active="false">Deactivate</button>'
            : '<button type="button" class="btn-active" data-id="' + u.id + '" data-active="true">Activate</button>';
          var pwBtn = '<button type="button" class="btn-pw" data-id="' + u.id + '">Change password</button>';
          var deleteBtn = '<button type="button" class="btn-delete" data-id="' + u.id + '" onclick="window.doAdminDeleteUser(this); return false;">Delete</button>';
          return '<tr><td>' + escapeHtml(u.email) + '</td><td>' + roleBadge + '</td><td>' + statusBadge + '</td><td>' + escapeHtml(created) + '</td><td>' + roleBtn + ' ' + activeBtn + ' ' + pwBtn + ' ' + deleteBtn + '</td></tr>';
        }).join('');
        if (wrap) wrap.style.display = 'block';
        document.getElementById('adminUsersPagination').style.display = 'block';
        document.getElementById('adminUsersPagination').textContent = 'Total ' + total;
      })
      .catch(function(e) {
        hideSkeleton('adminUsersLoading');
        if (loading) loading.style.display = 'none';
        if (errEl) {
          showErrorWithRetry(errEl, e.message || 'Load failed', function() { loadAdminUsers(); });
        }
      });
  }

  function loadAdminUsageLogs() {
    var usageLoading = document.getElementById('usageSummaryLoading');
    var usageWrap = document.getElementById('usageSummaryWrap');
    var usageBody = document.getElementById('usageSummaryBody');
    var usageEmpty = document.getElementById('usageSummaryEmpty');
    var usageError = document.getElementById('usageSummaryError');
    var pipelineLoading = document.getElementById('pipelineStatusLoading');
    var pipelineWrap = document.getElementById('pipelineStatusWrap');
    var pipelineBody = document.getElementById('pipelineStatusBody');
    var pipelineEmpty = document.getElementById('pipelineStatusEmpty');
    var pipelineError = document.getElementById('pipelineStatusError');
    var downloadLoading = document.getElementById('downloadLogLoading');
    var downloadWrap = document.getElementById('downloadLogWrap');
    var downloadBody = document.getElementById('downloadLogBody');
    var downloadEmpty = document.getElementById('downloadLogEmpty');
    var downloadError = document.getElementById('downloadLogError');
    var activityLoading = document.getElementById('activityLogLoading');
    var activityWrap = document.getElementById('activityLogWrap');
    var activityBody = document.getElementById('activityLogBody');
    var activityEmpty = document.getElementById('activityLogEmpty');
    var activityError = document.getElementById('activityLogError');
    function show(el, visible) { if (el) el.style.display = visible ? '' : 'none'; }
    [usageError, pipelineError, downloadError, activityError].forEach(function(el) { if (el) { el.style.display = 'none'; el.textContent = ''; el.className = 'error'; } });
    showSkeleton('usageSummaryLoading', 'table');
    showSkeleton('pipelineStatusLoading', 'table');
    showSkeleton('downloadLogLoading', 'table');
    showSkeleton('activityLogLoading', 'table');
    [usageWrap, pipelineWrap, downloadWrap, activityWrap].forEach(function(el) { show(el, false); });
    [usageEmpty, pipelineEmpty, downloadEmpty, activityEmpty].forEach(function(el) { show(el, false); });

    Promise.all([
      fetchWithAuth(API + '/api/admin/usage').then(function(r) { if (!r.ok) throw new Error('Usage'); return r.json(); }),
      fetchWithAuth(API + '/api/admin/pipeline-status').then(function(r) { if (!r.ok) throw new Error('Pipeline'); return r.json(); }),
      fetchWithAuth(API + '/api/admin/download-log?limit=100').then(function(r) { if (!r.ok) throw new Error('Download log'); return r.json(); }),
      fetchWithAuth(API + '/api/admin/activity-log?limit=100').then(function(r) { if (!r.ok) throw new Error('Activity log'); return r.json(); })
    ]).then(function(results) {
      var usage = results[0];
      var pipeline = results[1];
      var download = results[2];
      var activity = results[3];
      ['usageSummaryLoading','pipelineStatusLoading','downloadLogLoading','activityLogLoading'].forEach(function(id) { hideSkeleton(id); var el = document.getElementById(id); if (el) el.style.display = 'none'; });
      var items = usage.items || [];
      if (items.length && usageBody) {
        usageBody.innerHTML = items.map(function(u) {
          return '<tr><td>' + escapeHtml(u.email || '') + '</td><td>' + escapeHtml(u.role || '') + '</td><td>' + (u.last_login || '—') + '</td><td>' + (u.sessions_7d != null ? u.sessions_7d : '—') + '</td><td>' + (u.downloads_7d != null ? u.downloads_7d : '—') + '</td></tr>';
        }).join('');
        show(usageWrap, true);
      } else if (usageEmpty) { show(usageEmpty, true); }
      items = pipeline.items || [];
      if (items.length && pipelineBody) {
        pipelineBody.innerHTML = items.map(function(p) {
          return '<tr><td>' + escapeHtml(p.name || '') + '</td><td>' + escapeHtml(p.type || '') + '</td><td>' + (p.last_run || '—') + '</td><td>' + escapeHtml(p.status || '—') + '</td><td>' + escapeHtml(p.note || '') + '</td></tr>';
        }).join('');
        show(pipelineWrap, true);
      } else if (pipelineEmpty) { show(pipelineEmpty, true); }
      items = download.items || [];
      if (items.length && downloadBody) {
        downloadBody.innerHTML = items.map(function(d) {
          return '<tr><td>' + escapeHtml(d.ts || '') + '</td><td>' + escapeHtml(d.email || '') + '</td><td>' + escapeHtml(d.download_type || '') + '</td><td>' + escapeHtml(d.period_or_detail || '') + '</td></tr>';
        }).join('');
        show(downloadWrap, true);
      } else if (downloadEmpty) { show(downloadEmpty, true); }
      items = activity.items || [];
      if (items.length && activityBody) {
        activityBody.innerHTML = items.map(function(a) {
          return '<tr><td>' + escapeHtml(a.ts || '') + '</td><td>' + escapeHtml(a.email || '') + '</td><td>' + escapeHtml(a.action || '') + '</td><td>' + escapeHtml(a.detail || '') + '</td></tr>';
        }).join('');
        show(activityWrap, true);
      } else if (activityEmpty) { show(activityEmpty, true); }
    }).catch(function(e) {
      ['usageSummaryLoading','pipelineStatusLoading','downloadLogLoading','activityLogLoading'].forEach(function(id) { hideSkeleton(id); var el = document.getElementById(id); if (el) el.style.display = 'none'; });
      var msg = e.message || 'Load failed';
      [usageError, pipelineError, downloadError, activityError].forEach(function(el) {
        if (el) showErrorWithRetry(el, msg, function() { loadAdminUsageLogs(); });
      });
    });
  }

  var pwChangeUserId = null;
  function openPwChangeModal(userId) {
    pwChangeUserId = userId;
    var modal = document.getElementById('pwChangeModal');
    var input = document.getElementById('pwModalInput');
    var errEl = document.getElementById('pwModalError');
    if (modal) modal.classList.add('show');
    if (input) { input.value = ''; input.focus(); }
    if (errEl) { errEl.textContent = ''; errEl.classList.remove('show'); }
  }
  function closePwChangeModal() {
    var modal = document.getElementById('pwChangeModal');
    if (modal) modal.classList.remove('show');
    pwChangeUserId = null;
  }
  document.getElementById('pwModalCancel').onclick = closePwChangeModal;
  document.getElementById('pwModalConfirm').onclick = function() {
    var input = document.getElementById('pwModalInput');
    var errEl = document.getElementById('pwModalError');
    var newPw = (input && input.value) ? input.value : '';
    if (newPw.length < 6) {
      if (errEl) { errEl.textContent = 'Password must be at least 6 characters.'; errEl.classList.add('show'); }
      return;
    }
    if (!pwChangeUserId) return;
    if (errEl) { errEl.classList.remove('show'); errEl.textContent = ''; }
    fetchWithAuth(API + '/api/admin/users/' + pwChangeUserId, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: newPw }) })
      .then(function(r) {
        return r.text().then(function(t) {
          var b;
          try { b = t ? JSON.parse(t) : {}; } catch (_) { throw new Error(t || 'Update failed'); }
          if (!r.ok) throw new Error(b.detail || t || 'Update failed');
          return b;
        });
      })
      .then(function() {
        closePwChangeModal();
        alert('Password has been updated.');
        loadAdminUsers();
      })
      .catch(function(e) {
        if (errEl) { errEl.textContent = e.message || 'Update failed'; errEl.classList.add('show'); }
      });
  };
  document.getElementById('pwChangeModal').onclick = function(e) {
    if (e.target.id === 'pwChangeModal') closePwChangeModal();
  };
  document.getElementById('pwModalInput').onkeydown = function(e) {
    if (e.key === 'Enter') document.getElementById('pwModalConfirm').click();
  };

  var adminRoleFilter = document.getElementById('adminUsersRoleFilter');
  var adminStatusFilter = document.getElementById('adminUsersStatusFilter');
  var adminRefresh = document.getElementById('adminUsersRefresh');
  if (adminRoleFilter) adminRoleFilter.onchange = loadAdminUsers;
  if (adminStatusFilter) adminStatusFilter.onchange = loadAdminUsers;
  if (adminRefresh) adminRefresh.onclick = loadAdminUsers;

  window.doAdminDeleteUser = function(btn) {
    if (!btn || !btn.getAttribute) return;
    var id = parseInt(btn.getAttribute('data-id'), 10);
    var row = btn.closest('tr');
    var email = row && row.querySelector('td') ? (row.querySelector('td').textContent || '').trim() : '';
    if (!id) return;
    if (!confirm('Really delete account "' + (email || 'this account') + '"?\nDeleted accounts cannot be recovered.')) return;
    var baseUrl = window.API_BASE || window.location.origin || '';
    fetch(baseUrl + '/api/admin/users/' + id, { method: 'DELETE', credentials: 'include' })
      .then(function(r) {
        if (r.status === 401) { window.location.href = '/login'; return Promise.reject(new Error('Unauthorized')); }
        if (!r.ok) return r.text().then(function(t) { try { var b = JSON.parse(t); throw new Error(b.detail || t); } catch (err) { throw err instanceof Error ? err : new Error(t || 'Delete failed'); } });
        return r.status === 204 ? {} : r.json();
      })
      .then(function() { loadAdminUsers(); })
      .catch(function(e) { alert(e.message || 'Delete failed'); });
  };

  var adminTable = document.getElementById('adminUsersTable');
  if (adminTable) {
    adminTable.addEventListener('click', function(e) {
      var btn = e.target.closest('button[data-id]');
      if (!btn || !btn.classList.contains('btn-role') && !btn.classList.contains('btn-active') && !btn.classList.contains('btn-pw')) return;
      if (btn.classList.contains('btn-delete')) return;
      e.preventDefault();
      e.stopPropagation();
      var id = parseInt(btn.getAttribute('data-id'), 10);
      if (!id) return;
      if (btn.classList.contains('btn-pw')) {
        openPwChangeModal(id);
        return;
      }
      if (btn.classList.contains('btn-role')) {
        var role = btn.getAttribute('data-role');
        if (!role) return;
        fetchWithAuth(API + '/api/admin/users/' + id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role: role }), credentials: 'include' })
          .then(function(r) { return r.json(); })
          .then(function() { loadAdminUsers(); })
          .catch(function(e) { alert(e.message || 'Update failed'); });
        return;
      }
      if (btn.classList.contains('btn-active')) {
        var active = btn.getAttribute('data-active') === 'true';
        fetchWithAuth(API + '/api/admin/users/' + id, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: active }), credentials: 'include' })
          .then(function(r) { return r.json(); })
          .then(function() { loadAdminUsers(); })
          .catch(function(e) { alert(e.message || 'Update failed'); });
      }
    });
  }

  document.getElementById('adminUsersAddBtn').onclick = function() {
    var emailEl = document.getElementById('adminAddEmail');
    var pwEl = document.getElementById('adminAddPassword');
    var roleEl = document.getElementById('adminAddRole');
    var errEl = document.getElementById('adminUsersAddError');
    var email = (emailEl && emailEl.value || '').trim();
    var password = pwEl && pwEl.value || '';
    var role = roleEl && roleEl.value || 'user';
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    if (!email) { if (errEl) { errEl.style.display = 'block'; errEl.textContent = 'Please enter email.'; } return; }
    if (password.length < 6) { if (errEl) { errEl.style.display = 'block'; errEl.textContent = 'Password must be at least 6 characters.'; } return; }
    fetchWithAuth(API + '/api/admin/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email, password: password, role: role }) })
      .then(function(r) {
        return r.text().then(function(t) {
          var b;
          try { b = t ? JSON.parse(t) : {}; } catch (_) { throw new Error(r.status === 405 ? 'Please restart the server and try again. (Method Not Allowed)' : (t || 'Add failed (status ' + r.status + ')')); }
          if (!r.ok) throw new Error(b.detail || t || 'Add failed');
          return b;
        });
      })
      .then(function() {
        if (emailEl) emailEl.value = '';
        if (pwEl) pwEl.value = '';
        if (errEl) errEl.style.display = 'none';
        loadAdminUsers();
      })
      .catch(function(e) { if (errEl) { errEl.style.display = 'block'; errEl.textContent = e.message || 'Add failed'; } });
  };

  setSummaryTableHeader(currentReportType || 'B2B');

  try {
    var reports = await getReports();
    if (!reports.length) {
      var te = document.getElementById('tableErrorB2B');
      if (te) { te.style.display = 'block'; te.textContent = 'No data. Check .env DB connection (MYSQL_*) and refresh the dashboard.'; }
      return;
    }
    var firstMonth = fillYearMonthSelect('B2B', reports);
    var month = getMonthParam() || firstMonth || 'latest';
    var filters = await getFilters('B2B', month, []);
    var regions = filters.regions || [];
    var countries = filters.countries || [];
    fillRegionCountryPanels(regions, countries, false);
    if (subNavSummary) subNavSummary.style.display = '';
    if (subNavB2C) subNavB2C.style.display = 'none';
    if (subNavB2B) subNavB2B.style.display = 'none';
    if (firstMonth) {
      var match = String(firstMonth).match(/^(\d{4})-(\d{1,2})$/);
      if (match) {
        var yEl = document.getElementById('yearB2B'), mEl = document.getElementById('monthB2B');
        if (yEl) yEl.value = match[1];
        if (mEl) mEl.value = (match[2].length === 1 ? '0' + match[2] : match[2]);
      }
      await loadDashboard('B2B', getMonthParam() || firstMonth, [], []);
    }
    var monthsB2B = [...new Set(reports.filter(function(r) { return (r.report_type || r.reportType) === 'B2B'; }).map(function(r) { return r.month; }))].sort();
    document.getElementById('monthChecklist').innerHTML = '<option value="">B2B Latest</option>' + monthsB2B.map(function(m) { return '<option value="' + m + '">' + m + '</option>'; }).join('');

    var filterEl = document.getElementById('tableScoreFilterB2B');
    if (filterEl) filterEl.onchange = function() { refreshSummaryTable(); };

    var tabScoreByRegion = document.getElementById('tabScoreByRegion');
    var tabScoreByCountry = document.getElementById('tabScoreByCountry');
    var panelScoreByRegion = document.getElementById('panelScoreByRegion');
    var panelScoreByCountry = document.getElementById('panelScoreByCountry');
    if (tabScoreByRegion) tabScoreByRegion.onclick = function(e) {
      e.preventDefault();
      tabScoreByRegion.classList.add('active');
      if (tabScoreByCountry) tabScoreByCountry.classList.remove('active');
      if (panelScoreByRegion) panelScoreByRegion.classList.add('active');
      if (panelScoreByCountry) panelScoreByCountry.classList.remove('active');
      var opWrap = document.getElementById('operationalSummaryWrap');
      if (opWrap) opWrap.style.display = '';
    };
    if (tabScoreByCountry) tabScoreByCountry.onclick = function(e) {
      e.preventDefault();
      tabScoreByCountry.classList.add('active');
      if (tabScoreByRegion) tabScoreByRegion.classList.remove('active');
      if (panelScoreByCountry) panelScoreByCountry.classList.add('active');
      if (panelScoreByRegion) panelScoreByRegion.classList.remove('active');
      var opWrap = document.getElementById('operationalSummaryWrap');
      if (opWrap) opWrap.style.display = 'none';
      renderCountryRegionSelector();
      renderCountryFilterSelect();
      renderChartScoreByCountry();
    };
    var countryFilterSelectEl = document.getElementById('countryFilterSelect');
    if (countryFilterSelectEl) countryFilterSelectEl.onchange = function() {
      selectedCountryForChart = this.value || '';
      renderChartScoreByCountry();
    };

    function setActiveInNav(navId, activeId) {
      var nav = document.getElementById(navId);
      if (!nav) return;
      nav.querySelectorAll('a').forEach(function(a) { a.classList.remove('active'); });
      var el = document.getElementById(activeId);
      if (el) el.classList.add('active');
    }
    ['tabB2CAll','tabB2CFeatureCard','tabB2C360','tabB2CGnbStructure'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.onclick = function(e) { e.preventDefault(); setActiveInNav('subNavB2C', id); };
    });
    function switchB2BSubTab(tabId) {
      setActiveInNav('subNavB2B', tabId);
      var layout = document.querySelector('.summary-dashboard-layout');
      var tableSection = document.getElementById('summaryTableSection');
      var dashboardPanel = document.getElementById('summaryPanelDashboard');
      var blogPanel = document.getElementById('summaryPanelBlog');
      var ncPanel = document.getElementById('summaryPanelNewContents');
      document.querySelectorAll('.summary-sub-panel').forEach(function(p) { p.classList.remove('active'); });
      if (tabId === 'tabB2BBlog') {
        if (layout) layout.style.display = 'none';
        if (tableSection) tableSection.style.display = 'none';
        if (blogPanel) blogPanel.classList.add('active');
        var month = getMonthParam() || 'latest';
        var blogCfg = SUMMARY_SHEET_CONFIG.find(function(c) { return c.sheet === 'Blog'; });
        if (blogCfg) loadSheetSection(month, blogCfg);
      } else if (tabId === 'tabB2BNewContents') {
        if (layout) layout.style.display = 'none';
        if (tableSection) tableSection.style.display = 'none';
        if (ncPanel) ncPanel.classList.add('active');
        loadNewContentsData();
      } else if (tabId === 'tabB2BContentsError') {
        if (layout) layout.style.display = 'none';
        if (tableSection) tableSection.style.display = 'none';
        var cePanel = document.getElementById('summaryPanelContentsError');
        if (cePanel) cePanel.classList.add('active');
        loadContentsErrorData();
      } else {
        if (layout) layout.style.display = '';
        if (tableSection) tableSection.style.display = '';
        if (dashboardPanel) dashboardPanel.classList.add('active');
      }
    }
    ['tabB2BAll','tabB2BBlog','tabB2BNewContents','tabB2BContentsError'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.onclick = function(e) { e.preventDefault(); switchB2BSubTab(id); };
    });
    var blogCountryFilterEl = document.getElementById('blogCountryFilter');
    if (blogCountryFilterEl) blogCountryFilterEl.onchange = function() {
      var rows = window._blogSheetRows || [];
      var colCount = window._blogSheetColCount || 0;
      var blogCfg = SUMMARY_SHEET_CONFIG.find(function(c) { return c.sheet === 'Blog'; });
      if (!blogCfg) return;
      var tbody = document.getElementById(blogCfg.bodyId);
      var country = this.value || '';
      var filtered = country ? rows.filter(function(r) { var arr = Array.isArray(r) ? r : []; var c = (arr[1] != null ? String(arr[1]) : '').trim(); return c === country; }) : rows;
      if (tbody) tbody.innerHTML = buildBlogSheetBody(filtered, colCount);
    };
    var btnBlogDownload = document.getElementById('btnBlogDownload');
    if (btnBlogDownload) btnBlogDownload.onclick = function() {
      var rows = window._blogSheetRows || [];
      if (!rows.length) return;
      var country = (document.getElementById('blogCountryFilter') || {}).value || '';
      if (country) rows = rows.filter(function(r) { var arr = Array.isArray(r) ? r : []; var c = (arr[1] != null ? String(arr[1]) : '').trim(); return c === country; });
      var headRow = document.getElementById('sheetBlogHead');
      var headers = headRow ? Array.from(headRow.querySelectorAll('th')).map(function(th) { return th.textContent || ''; }) : [];
      var lines = [headers.join('\t')];
      rows.forEach(function(r) { var arr = Array.isArray(r) ? r : []; lines.push(arr.map(function(c) { var s = (c != null && c !== '') ? String(c).replace(/\t/g, ' ').replace(/\n/g, ' ') : ''; return s; }).join('\t')); });
      var blob = new Blob([lines.join('\n')], { type: 'text/tab-separated-values' });
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'blog_' + (getMonthParam() || 'latest') + '.tsv'; a.click(); URL.revokeObjectURL(a.href);
    };

    // ===== New Contents 탭 =====
    var NC_BLOG_SAMPLE = [
      { title: "Enhancing Commercial Comfort and Efficiency with LG's Energy Recovery Ventilators", mandatory: "Global", ref: "https://www.lg.com/business/hvac-blog/energy-recovery-ventilators/" },
      { title: "Beyond Efficiency: LG Charts the Next Decade of HVAC Tech at AHR 2025", mandatory: "Global", ref: "https://www.lg.com/business/hvac-blog/ahr-2025/" },
      { title: "Beat the Cold: Why LG Cold Climate Heat Pumps are Trending", mandatory: "US", ref: "" },
      { title: "Slim is in: LG's New Single Duct System Transforms HVAC Installation", mandatory: "Global", ref: "" },
    ];
    var NC_LGCOM_SAMPLE = [
      { page: "AWHP R32 Monobloc S II", mandatory: "EU", ref: "", damLink: "", ca: "O" },
      { page: "R290 Heat Pump Water Heater", mandatory: "EU", ref: "", damLink: "", ca: "X" },
      { page: "Chiller Main", mandatory: "Global", ref: "", damLink: "", ca: "-" },
      { page: "Centrifugal Chiller", mandatory: "Global", ref: "", damLink: "", ca: "" },
      { page: "Oil-free Centrifugal Chiller", mandatory: "Global", ref: "", damLink: "", ca: "" },
    ];
    function loadNewContentsData() {
      var blogBody = document.getElementById('ncBlogBody');
      var blogWrap = document.getElementById('ncBlogWrap');
      if (blogBody) {
        blogBody.innerHTML = NC_BLOG_SAMPLE.map(function(r) {
          var refCell = r.ref ? '<a href="' + escapeHtml(r.ref) + '" target="_blank" rel="noopener noreferrer">Reference 링크</a>' : '';
          return '<tr><td><input type="checkbox" /></td><td>' + escapeHtml(r.title) + '</td><td>' + escapeHtml(r.mandatory) + '</td><td>' + refCell + '</td></tr>';
        }).join('');
      }
      if (blogWrap) blogWrap.style.display = 'block';
      var lgBody = document.getElementById('ncLgcomBody');
      var lgWrap = document.getElementById('ncLgcomWrap');
      if (lgBody) {
        lgBody.innerHTML = NC_LGCOM_SAMPLE.map(function(r) {
          return '<tr><td>' + escapeHtml(r.page) + '</td><td>' + escapeHtml(r.mandatory) + '</td><td>' + escapeHtml(r.ref) + '</td><td>' + escapeHtml(r.damLink) + '</td><td>' + escapeHtml(r.ca) + '</td></tr>';
        }).join('');
      }
      if (lgWrap) lgWrap.style.display = 'block';
    }

    // ===== Contents Error 탭 =====
    var CE_VIDEO_SAMPLE = [
      { country: "UAE", locale: "AE : AE (en)", catplp: "PLP", gnb: "Absorption Chiller Direct Fired Type", gnbEng: "Absorption Chiller Direct Fired Type", url: "https://www.lg.com/ae/business/hvac/commercial-solutions/chiller/absorption-chiller-direct-fired-type", src: "" },
    ];
    var CE_404_SAMPLE = [];
    function loadContentsErrorData() {
      var videoBody = document.getElementById('ceVideoBody');
      if (videoBody) {
        videoBody.innerHTML = CE_VIDEO_SAMPLE.map(function(r) {
          var urlCell = r.url ? '<a href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(r.url) + '</a>' : '';
          return '<tr><td>' + escapeHtml(r.country) + '</td><td>' + escapeHtml(r.locale) + '</td><td>' + escapeHtml(r.catplp) + '</td><td>' + escapeHtml(r.gnb) + '</td><td>' + escapeHtml(r.gnbEng) + '</td><td>' + urlCell + '</td><td>' + escapeHtml(r.src) + '</td></tr>';
        }).join('');
        if (!CE_VIDEO_SAMPLE.length) {
          videoBody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-secondary);padding:1rem;">No video errors</td></tr>';
        }
      }
      var body404 = document.getElementById('ce404Body');
      if (body404) {
        if (!CE_404_SAMPLE.length) {
          body404.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-secondary);padding:1rem;">No 404 errors</td></tr>';
        } else {
          body404.innerHTML = CE_404_SAMPLE.map(function(r) {
            var urlCell = r.url ? '<a href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(r.url) + '</a>' : '';
            return '<tr><td>' + escapeHtml(r.country) + '</td><td>' + escapeHtml(r.locale) + '</td><td>' + escapeHtml(r.catplp) + '</td><td>' + escapeHtml(r.gnb) + '</td><td>' + escapeHtml(r.gnbEng) + '</td><td>' + urlCell + '</td><td>' + escapeHtml(r.src) + '</td></tr>';
          }).join('');
        }
      }
    }

    var tableSummary = document.getElementById('tableSummaryB2B');
    if (tableSummary) tableSummary.addEventListener('click', function(e) {
      var th = e.target && e.target.closest && e.target.closest('th.sortable');
      if (!th) return;
      var colIndex = parseInt(th.getAttribute('data-col-index'), 10);
      if (isNaN(colIndex)) return;
      if (summaryTableSort.colIndex === colIndex) {
        summaryTableSort.dir = -summaryTableSort.dir;
      } else {
        summaryTableSort.colIndex = colIndex;
        summaryTableSort.dir = 1;
      }
      refreshSummaryTable();
    });

    function openRawDataModal(region, country) {
      var overlay = document.getElementById('rawDataModalOverlay');
      var titleEl = document.getElementById('rawDataModalTitle');
      var loadingEl = document.getElementById('rawDataModalLoading');
      var tableWrap = document.getElementById('rawDataModalTableWrap');
      var theadEl = document.getElementById('rawDataModalThead');
      var tbodyEl = document.getElementById('rawDataModalTbody');
      var emptyEl = document.getElementById('rawDataModalEmpty');
      if (titleEl) titleEl.textContent = 'Raw data: ' + (region || '—') + ' / ' + (country || '—');
      if (loadingEl) loadingEl.style.display = 'block';
      if (tableWrap) tableWrap.style.display = 'none';
      if (emptyEl) emptyEl.style.display = 'none';
      if (overlay) overlay.classList.add('show');
      var q = '?report_type=' + encodeURIComponent(currentReportType || 'B2B') + '&limit=500';
      if (region) q += '&region=' + encodeURIComponent(region);
      if (country) q += '&country=' + encodeURIComponent(country);
      fetchWithAuth(API + '/api/raw' + q).then(function(r) {
        if (!r.ok) throw new Error('Load failed');
        return r.json();
      }).then(function(data) {
        if (loadingEl) loadingEl.style.display = 'none';
        var items = data.items || [];
        if (items.length === 0) {
          if (emptyEl) emptyEl.style.display = 'block';
          return;
        }
        var keys = Object.keys(items[0]);
        if (theadEl) {
          theadEl.innerHTML = '<tr>' + keys.map(function(k) { return '<th>' + escapeHtml(k) + '</th>'; }).join('') + '</tr>';
        }
        if (tbodyEl) {
          tbodyEl.innerHTML = items.map(function(row) {
            return '<tr>' + keys.map(function(k) {
              var v = row[k];
              var s = (v != null && v !== '') ? String(v) : '';
              var url = s.trim();
              var isUrl = /^https?:\/\//i.test(url);
              if (isUrl) {
                var safeHref = url.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/&/g, '&amp;');
                return '<td><a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(s) + '</a></td>';
              }
              return '<td>' + escapeHtml(s) + '</td>';
            }).join('') + '</tr>';
          }).join('');
        }
        if (tableWrap) tableWrap.style.display = 'block';
      }).catch(function(err) {
        if (loadingEl) loadingEl.style.display = 'none';
        if (emptyEl) { emptyEl.textContent = err.message || 'Load failed.'; emptyEl.style.display = 'block'; }
      });
    }
    function closeRawDataModal() {
      var overlay = document.getElementById('rawDataModalOverlay');
      if (overlay) overlay.classList.remove('show');
    }
    document.getElementById('rawDataModalClose').onclick = closeRawDataModal;
    document.getElementById('rawDataModalOverlay').onclick = function(e) {
      if (e.target.id === 'rawDataModalOverlay') closeRawDataModal();
    };

    var tableSummary2 = document.getElementById('tableSummaryB2B');
    if (tableSummary2) tableSummary2.addEventListener('click', function(e) {
      var td = e.target && e.target.closest && e.target.closest('td.cell-clickable');
      if (!td) return;
      var tr = td.closest('tr');
      if (!tr) return;
      var region = (tr.getAttribute('data-region') || '').trim();
      var country = (tr.getAttribute('data-country') || '').trim();
      openRawDataModal(region, country);
    });

    function onYearMonthChange() {
      var m = getMonthParam();
      getFilters(currentReportType, m, []).then(function(f) {
        fillRegionCountryPanels(f.regions || [], f.countries || [], false);
        loadDashboard(currentReportType, m, getSelectedRegions(), getSelectedCountries());
      });
    }
    var yearEl = document.getElementById('yearB2B'), monthEl = document.getElementById('monthB2B');
    if (yearEl) yearEl.onchange = onYearMonthChange;
    if (monthEl) monthEl.onchange = onYearMonthChange;
    document.getElementById('regionB2BPanel').addEventListener('change', function() {
      var month = getMonthParam();
      var selectedR = getSelectedRegions();
      getFilters(currentReportType, month, selectedR).then(function(f) {
        var countriesInRegion = f.countries || [];
        fillRegionCountryPanels(f.regions || [], countriesInRegion, true);
        loadDashboard(currentReportType, month, selectedR, getSelectedCountries());
      });
    });
    document.getElementById('countryB2BPanel').addEventListener('change', function() {
      updateMultiselectButtonLabels(
        Array.from(document.getElementById('regionB2BPanel').querySelectorAll('input')).map(function(i) { return i.value; }),
        Array.from(document.getElementById('countryB2BPanel').querySelectorAll('input')).map(function(i) { return i.value; })
      );
      loadDashboard(currentReportType, getMonthParam(), getSelectedRegions(), getSelectedCountries());
    });

    function applyMultiselectAll(panelId, selectAll) {
      var panel = document.getElementById(panelId);
      if (!panel) return;
      panel.querySelectorAll('input[type="checkbox"]').forEach(function(cb) { cb.checked = selectAll; });
      if (panelId === 'regionB2BPanel') {
        var month = getMonthParam();
        var selectedR = getSelectedRegions();
        getFilters(currentReportType, month, selectedR).then(function(f) {
          fillRegionCountryPanels(f.regions || [], f.countries || [], true);
          loadDashboard(currentReportType, month, selectedR, getSelectedCountries());
        });
      } else {
        updateMultiselectButtonLabels(
          Array.from(document.getElementById('regionB2BPanel').querySelectorAll('input')).map(function(i) { return i.value; }),
          Array.from(document.getElementById('countryB2BPanel').querySelectorAll('input')).map(function(i) { return i.value; })
        );
        loadDashboard(currentReportType, getMonthParam(), getSelectedRegions(), getSelectedCountries());
      }
    }
    document.getElementById('regionB2BPanel').addEventListener('click', function(e) {
      var sel = e.target.closest && e.target.closest('.multiselect-select-all');
      var des = e.target.closest && e.target.closest('.multiselect-deselect-all');
      if (sel) { e.preventDefault(); applyMultiselectAll('regionB2BPanel', true); }
      else if (des) { e.preventDefault(); applyMultiselectAll('regionB2BPanel', false); }
    });
    document.getElementById('countryB2BPanel').addEventListener('click', function(e) {
      var sel = e.target.closest && e.target.closest('.multiselect-select-all');
      var des = e.target.closest && e.target.closest('.multiselect-deselect-all');
      if (sel) { e.preventDefault(); applyMultiselectAll('countryB2BPanel', true); }
      else if (des) { e.preventDefault(); applyMultiselectAll('countryB2BPanel', false); }
    });

    document.querySelectorAll('.multiselect-wrap').forEach(function(wrap) {
      var btn = wrap.querySelector('.multiselect-btn');
      if (btn) btn.onclick = function(e) { e.stopPropagation(); wrap.classList.toggle('open'); };
      var panel = wrap.querySelector('.multiselect-panel');
      if (panel) panel.onclick = function(e) { e.stopPropagation(); }
    });
    document.addEventListener('click', function() { document.querySelectorAll('.multiselect-wrap.open').forEach(function(w) { w.classList.remove('open'); }); });

    document.getElementById('monthChecklist').onchange = function() { loadChecklist(this.value); };

    var downloadWrap = document.getElementById('downloadWrapB2B');
    var btnDownload = document.getElementById('btnDownload');
    var downloadDropdown = document.getElementById('downloadDropdown');
    if (btnDownload && downloadDropdown && downloadWrap) {
      btnDownload.onclick = function(e) { e.stopPropagation(); downloadWrap.classList.toggle('open'); };
      document.getElementById('btnDownloadExcel').onclick = function(e) { e.stopPropagation(); downloadWrap.classList.remove('open'); downloadAsExcel(); };
    }
    var btnLogoutSidebar = document.getElementById('btnLogoutSidebar');
    if (btnLogoutSidebar) {
      btnLogoutSidebar.onclick = function(e) {
        e.preventDefault();
        fetchWithAuth(API + '/auth/logout', { method: 'POST' }).then(function() { window.location.href = '/login'; }).catch(function() { window.location.href = '/login'; });
      };
    }
    document.addEventListener('click', function() { if (downloadWrap) downloadWrap.classList.remove('open'); });

    restoreViewState();
  } catch (e) {
    var te = document.getElementById('tableErrorB2B');
    if (te) { te.style.display = 'block'; te.textContent = 'Connection failed: ' + (e.message || String(e)) + '. Open via ' + API + '.'; }
  }
})();
