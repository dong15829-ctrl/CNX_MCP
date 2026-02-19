import { avg, fmtInt, fmtPct } from '../utils/format.js';

export class ScoreCards {
  constructor(containerEl) {
    this.container = containerEl;
  }

  render(data, config) {
    if (!this.container) return;
    if (!data || data.length === 0) {
      this.container.innerHTML = '<div class="empty-state">No data found.</div>';
      return;
    }

    const overallAvg = avg(data, 'total_score_pct');
    const totalSkus = data.reduce((sum, row) => sum + (Number(row.sku_count) || 0), 0);

    const regions = [...new Set(data.map((row) => row.region))];
    const regionCards = regions.map((region) => {
      const regionRows = data.filter((row) => row.region === region);
      const regionAvg = avg(regionRows, 'total_score_pct');
      return {
        label: region,
        value: fmtPct(regionAvg, 1),
        className: regionAvg >= 90 ? 'good' : '',
        sub: `${regionRows.length} countries`,
      };
    });

    const cards = [
      {
        label: 'Overall Average',
        value: fmtPct(overallAvg, 1),
        className: 'primary',
        sub: 'Total score average',
      },
      {
        label: 'Total SKUs',
        value: fmtInt(totalSkus),
        className: 'info',
        sub: `Max ${config.totalMax} pts`,
      },
      ...regionCards,
    ];

    this.container.innerHTML = cards
      .map((card) => {
        return `
          <div class="score-card ${card.className}">
            <div class="score-label">${card.label}</div>
            <div class="score-value">${card.value}</div>
            <div class="score-sub">${card.sub || ''}</div>
          </div>
        `;
      })
      .join('');
  }
}
