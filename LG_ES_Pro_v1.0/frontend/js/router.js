import { state } from './state.js';

const ROUTES = {
  '#dashboard': 'dashboard',
  '#summary': 'summary',
  '#detail': 'detail',
  '#checklist': 'checklist',
};

class Router {
  constructor() {
    window.addEventListener('hashchange', () => this.route());
  }

  route() {
    const hash = window.location.hash || '#dashboard';
    const section = ROUTES[hash] || 'dashboard';
    state.set({ section });
  }

  navigate(section) {
    window.location.hash = `#${section}`;
  }

  init() {
    this.route();
  }
}

export const router = new Router();
