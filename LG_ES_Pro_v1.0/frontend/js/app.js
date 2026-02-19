import { state } from './state.js';
import { router } from './router.js';
import { B2B_CONFIG, B2C_CONFIG } from './utils/constants.js';
import { MOCK_DATA, MOCK_MONTHS, MOCK_YEARS } from './data/mock.js';
import { ScoreCards } from './components/ScoreCards.js';
import { BarChart } from './components/BarChart.js';
import { TrendChart } from './components/TrendChart.js';
import { DataTable } from './components/DataTable.js';
import { MultiSelect } from './components/MultiSelect.js';
import { Toast } from './components/Toast.js';

const elements = {
  mainTabs: document.getElementById('main-tabs'),
  typeTabs: document.getElementById('type-tabs'),
  yearSelect: document.getElementById('year-select'),
  monthSelect: document.getElementById('month-select'),
  regionFilter: document.getElementById('region-filter'),
  countryFilter: document.getElementById('country-filter'),
  scoreFilter: document.getElementById('score-filter'),
  dashboardTitle: document.getElementById('dashboard-title'),
  summaryTitle: document.querySelector('#section-summary h2'),
  sections: {
    dashboard: document.getElementById('section-dashboard'),
    summary: document.getElementById('section-summary'),
    detail: document.getElementById('section-detail'),
    checklist: document.getElementById('section-checklist'),
  },
  downloadDropdown: document.getElementById('download-dropdown'),
  userDropdown: document.getElementById('user-dropdown'),
};

const scoreCards = new ScoreCards(document.getElementById('score-cards'));
const barChart = new BarChart(document.getElementById('bar-chart'));
const trendChart = new TrendChart(document.getElementById('trend-chart'));
const dataTable = new DataTable(document.getElementById('summary-table'));
const regionSelect = new MultiSelect(elements.regionFilter, { label: 'Region' });
const countrySelect = new MultiSelect(elements.countryFilter, { label: 'Country' });

function getConfig() {
  return state.get('type') === 'b2c' ? B2C_CONFIG : B2B_CONFIG;
}

function getRawData() {
  return MOCK_DATA[state.get('type')].summary;
}

function applyFilters(data) {
  const regions = state.get('selectedRegions');
  const countries = state.get('selectedCountries');

  return data.filter((row) => {
    const regionOk = regions.length === 0 || regions.includes(row.region);
    const countryOk = countries.length === 0 || countries.includes(row.country);
    return regionOk && countryOk;
  });
}

function updateData() {
  const filtered = applyFilters(getRawData());
  const trendData = MOCK_DATA[state.get('type')].trend;

  state.set({
    summaryData: filtered,
    trendData,
  });
}

function updateTitles() {
  const typeLabel = state.get('type') === 'b2c' ? 'B2C' : 'B2B';
  elements.dashboardTitle.textContent = `Average Total Score by Region (${typeLabel})`;
  elements.summaryTitle.textContent = `${typeLabel} Monitoring Report by Country`;
}

function updateSections() {
  const active = state.get('section');
  Object.entries(elements.sections).forEach(([key, section]) => {
    section.classList.toggle('active', key === active);
  });

  elements.mainTabs.querySelectorAll('.tab').forEach((tab) => {
    tab.classList.toggle('active', tab.dataset.section === active);
  });
}

function updateFilters() {
  const data = getRawData();
  const regions = [...new Set(data.map((row) => row.region))].sort();
  const countriesByRegion = data.reduce((acc, row) => {
    acc[row.region] = acc[row.region] || new Set();
    acc[row.region].add(row.country);
    return acc;
  }, {});

  regionSelect.setItems(regions, state.get('selectedRegions'));

  const selectedRegions = state.get('selectedRegions');
  let countries = [];
  if (selectedRegions.length) {
    selectedRegions.forEach((region) => {
      countries = countries.concat([...(countriesByRegion[region] || [])]);
    });
  } else {
    countries = Object.values(countriesByRegion).flatMap((set) => [...set]);
  }
  countries = [...new Set(countries)].sort();
  countrySelect.setItems(countries, state.get('selectedCountries'));
}

function initYearMonth() {
  elements.yearSelect.innerHTML = MOCK_YEARS.map((year) => `<option value="${year}">${year}</option>`).join('');
  const latestYear = Math.max(...MOCK_YEARS);
  const months = MOCK_MONTHS[latestYear] || [];
  const latestMonth = months.length ? Math.max(...months) : null;

  state.set({ year: latestYear, month: latestMonth });
  elements.yearSelect.value = String(latestYear);
  updateMonthOptions(latestYear, latestMonth);
}

function updateMonthOptions(year, selected) {
  const months = MOCK_MONTHS[year] || [];
  elements.monthSelect.innerHTML = months
    .map((month) => `<option value="${month}">${String(month).padStart(2, '0')}</option>`)
    .join('');
  if (selected) {
    elements.monthSelect.value = String(selected);
  }
}

function bindTabs() {
  elements.mainTabs.querySelectorAll('.tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      router.navigate(tab.dataset.section);
    });
  });

  elements.typeTabs.querySelectorAll('.subtab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const type = tab.dataset.type;
      state.set({
        type,
        selectedRegions: [],
        selectedCountries: [],
        scoreFilter: '',
        sortCol: null,
        sortDir: 'asc',
      });

      elements.typeTabs.querySelectorAll('.subtab').forEach((item) => {
        item.classList.toggle('active', item.dataset.type === type);
      });

      elements.scoreFilter.value = '';
      updateTitles();
      updateFilters();
      updateData();
    });
  });
}

function bindFilters() {
  regionSelect.onChange((selected) => {
    state.set({ selectedRegions: selected, selectedCountries: [] });
    updateFilters();
    updateData();
  });

  countrySelect.onChange((selected) => {
    state.set({ selectedCountries: selected });
    updateData();
  });

  elements.scoreFilter.addEventListener('change', () => {
    state.set({ scoreFilter: elements.scoreFilter.value });
    updateData();
  });

  elements.yearSelect.addEventListener('change', () => {
    const year = Number(elements.yearSelect.value);
    const months = MOCK_MONTHS[year] || [];
    const latestMonth = months.length ? Math.max(...months) : null;
    state.set({ year, month: latestMonth });
    updateMonthOptions(year, latestMonth);
    updateData();
    Toast.show(`Year set to ${year}`, 'info', 1500);
  });

  elements.monthSelect.addEventListener('change', () => {
    const month = Number(elements.monthSelect.value);
    state.set({ month });
    updateData();
    Toast.show(`Month set to ${String(month).padStart(2, '0')}`, 'info', 1500);
  });
}

function bindDropdowns() {
  const dropdowns = [elements.downloadDropdown, elements.userDropdown];

  dropdowns.forEach((dropdown) => {
    const button = dropdown.querySelector('button');
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      dropdowns.forEach((other) => {
        if (other !== dropdown) other.classList.remove('open');
      });
      dropdown.classList.toggle('open');
    });
  });

  document.addEventListener('click', () => {
    dropdowns.forEach((dropdown) => dropdown.classList.remove('open'));
  });

  elements.downloadDropdown.querySelectorAll('[data-download]').forEach((item) => {
    item.addEventListener('click', () => {
      const type = item.dataset.download;
      Toast.show(`${type.toUpperCase()} download 준비 중입니다.`, 'info');
    });
  });

  elements.userDropdown.querySelectorAll('[data-action]').forEach((item) => {
    item.addEventListener('click', () => {
      const action = item.dataset.action;
      if (action === 'logout') {
        Toast.show('로그아웃 완료', 'success');
      } else {
        Toast.show('관리자 메뉴는 준비 중입니다.', 'info');
      }
    });
  });
}

function bindTableSort() {
  dataTable.onSort((col) => {
    const current = state.get('sortCol');
    const nextDir = current === col && state.get('sortDir') === 'asc' ? 'desc' : 'asc';
    state.set({ sortCol: col, sortDir: nextDir });
    updateData();
  });
}

function subscribeState() {
  state.subscribe('summaryData', (data) => {
    const config = getConfig();
    scoreCards.render(data, config);
    barChart.render(data, config);
    dataTable.render(data, {
      columns: config.columns,
      labels: config.labels,
      scoreColumns: config.scoreColumns,
      sortCol: state.get('sortCol'),
      sortDir: state.get('sortDir'),
      scoreFilter: state.get('scoreFilter'),
    });
  });

  state.subscribe('trendData', (data) => {
    trendChart.render(data);
  });

  state.subscribe('section', updateSections);
}

function init() {
  if (!window.Chart) {
    Toast.show('Chart.js failed to load.', 'error');
  }

  initYearMonth();
  updateTitles();
  updateFilters();
  bindTabs();
  bindFilters();
  bindDropdowns();
  bindTableSort();
  subscribeState();

  updateData();
  router.init();
}

document.addEventListener('DOMContentLoaded', init);
