const initialState = {
  user: null,
  isAuthenticated: false,

  type: 'b2b',
  year: null,
  month: null,
  selectedRegions: [],
  selectedCountries: [],

  section: 'dashboard',

  summaryData: [],
  trendData: { labels: [], series: [] },

  sortCol: null,
  sortDir: 'asc',
  scoreFilter: '',

  loading: false,
  error: null,
};

class StateManager {
  constructor(initial) {
    this._state = { ...initial };
    this._listeners = new Map();
  }

  get(key) {
    return this._state[key];
  }

  getAll() {
    return { ...this._state };
  }

  set(updates) {
    const changed = [];
    Object.entries(updates).forEach(([key, value]) => {
      if (this._state[key] !== value) {
        this._state[key] = value;
        changed.push(key);
      }
    });

    changed.forEach((key) => {
      const listeners = this._listeners.get(key);
      if (!listeners) return;
      listeners.forEach((cb) => cb(this._state[key], this._state));
    });
  }

  subscribe(key, callback) {
    if (!this._listeners.has(key)) this._listeners.set(key, new Set());
    this._listeners.get(key).add(callback);
    return () => this._listeners.get(key)?.delete(callback);
  }
}

export const state = new StateManager(initialState);
