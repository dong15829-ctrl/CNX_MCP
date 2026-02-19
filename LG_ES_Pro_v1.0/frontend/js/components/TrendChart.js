import { REGION_COLORS } from '../utils/constants.js';

export class TrendChart {
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.chart = null;
  }

  render(trendData) {
    if (!this.canvas) return;
    this.destroy();

    if (!trendData || !trendData.labels?.length) {
      this.canvas.parentElement?.classList.add('is-empty');
      return;
    }

    this.canvas.parentElement?.classList.remove('is-empty');

    const datasets = trendData.series.map((series) => {
      const color = REGION_COLORS[series.region] || '#94a3b8';
      return {
        label: series.region,
        data: series.data,
        borderColor: color,
        backgroundColor: `${color}22`,
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 6,
      };
    });

    this.chart = new window.Chart(this.canvas, {
      type: 'line',
      data: {
        labels: trendData.labels,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 50,
            max: 100,
            ticks: {
              callback: (value) => `${value}%`,
            },
          },
        },
        plugins: {
          legend: {
            position: 'bottom',
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`,
            },
          },
        },
      },
    });
  }

  destroy() {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }
}
