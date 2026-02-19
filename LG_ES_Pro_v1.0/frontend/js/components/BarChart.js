import { avg, groupBy } from '../utils/format.js';

export class BarChart {
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.chart = null;
  }

  render(data, config) {
    if (!this.canvas) return;
    this.destroy();

    if (!data || data.length === 0) {
      this.canvas.parentElement?.classList.add('is-empty');
      return;
    }

    this.canvas.parentElement?.classList.remove('is-empty');

    const grouped = groupBy(data, 'region');
    const regions = Object.keys(grouped);

    const datasets = config.scoreColumns.map((col, idx) => {
      const colorHue = Math.round((idx / config.scoreColumns.length) * 360);
      return {
        label: config.scoreLabels[idx],
        data: regions.map((region) => avg(grouped[region], col)),
        backgroundColor: `hsl(${colorHue} 70% 60% / 0.7)`,
        borderColor: `hsl(${colorHue} 70% 45%)`,
        borderWidth: 1,
      };
    });

    this.chart = new window.Chart(this.canvas, {
      type: 'bar',
      data: {
        labels: regions,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Score',
            },
            grid: {
              color: 'rgba(0,0,0,0.05)',
            },
          },
          x: {
            grid: {
              display: false,
            },
          },
        },
        plugins: {
          legend: {
            position: 'bottom',
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}`,
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
