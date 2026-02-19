import { fmtInt, fmtScore } from '../utils/format.js';

export class DataTable {
  constructor(containerEl) {
    this.container = containerEl;
    this.sortCallback = null;
  }

  onSort(callback) {
    this.sortCallback = callback;
  }

  render(data, config) {
    if (!this.container) return;

    if (!data || data.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No data found.</div>';
      return;
    }

    const { columns, labels, scoreColumns, sortCol, sortDir, scoreFilter } = config;

    let working = [...data];

    if (scoreFilter) {
      const sortedByScore = [...working].sort((a, b) => (b.total_score_pct || 0) - (a.total_score_pct || 0));
      const cut = Math.max(1, Math.ceil(sortedByScore.length * 0.3));
      if (scoreFilter === 'top30') {
        working = sortedByScore.slice(0, cut);
      } else if (scoreFilter === 'bottom30') {
        working = sortedByScore.slice(-cut);
      }
    }

    if (sortCol) {
      working.sort((a, b) => {
        const aVal = a[sortCol];
        const bVal = b[sortCol];
        const aNum = Number(aVal);
        const bNum = Number(bVal);

        let cmp = 0;
        if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
          cmp = aNum - bNum;
        } else {
          cmp = String(aVal ?? '').localeCompare(String(bVal ?? ''));
        }
        return sortDir === 'asc' ? cmp : -cmp;
      });
    }

    if (working.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No data found.</div>';
      return;
    }
    const headerCells = columns
      .map((col, idx) => {
        const isActive = sortCol === col;
        const arrow = isActive ? (sortDir === 'asc' ? ' ▲' : ' ▼') : '';
        const label = (labels[idx] || '').replace(/\n/g, '<br>');
        return `<th data-col="${col}">${label}${arrow}</th>`;
      })
      .join('');

    const bodyRows = working
      .map((row) => {
        const cells = columns
          .map((col) => {
            const value = row[col];
            if (col === 'sku_count') return `<td>${fmtInt(value)}</td>`;
            if (col === 'total_score_pct') {
              const scoreClass = value >= 90 ? 'score-good' : value >= 70 ? 'score-warn' : 'score-bad';
              return `<td class="${scoreClass}">${fmtScore(value, 1)}%</td>`;
            }
            if (scoreColumns.includes(col)) return `<td>${fmtScore(value, 1)}</td>`;
            return `<td>${value ?? '—'}</td>`;
          })
          .join('');
        return `<tr>${cells}</tr>`;
      })
      .join('');

    this.container.innerHTML = `
      <table class="data-table">
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    `;

    const headers = this.container.querySelectorAll('th[data-col]');
    headers.forEach((th) => {
      th.addEventListener('click', () => {
        const col = th.dataset.col;
        if (this.sortCallback) this.sortCallback(col);
      });
    });
  }
}
