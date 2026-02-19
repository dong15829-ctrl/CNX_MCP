export function fmtScore(value, decimals = 1) {
  if (value == null || value === '') return '—';
  return Number(value).toFixed(decimals);
}

export function fmtPct(value, decimals = 1) {
  if (value == null || value === '') return '—';
  return Number(value).toFixed(decimals) + '%';
}

export function fmtInt(value) {
  if (value == null || value === '') return '—';
  return Number(value).toLocaleString();
}

export function scoreColor(pct) {
  if (pct >= 90) return 'var(--green)';
  if (pct >= 70) return 'var(--orange)';
  return 'var(--red-danger)';
}

export function avg(arr, key) {
  if (!arr.length) return 0;
  return arr.reduce((sum, row) => sum + (Number(row[key]) || 0), 0) / arr.length;
}

export function groupBy(arr, key) {
  const map = {};
  arr.forEach((row) => {
    const k = row[key] ?? 'Unknown';
    if (!map[k]) map[k] = [];
    map[k].push(row);
  });
  return map;
}
