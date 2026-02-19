export class Toast {
  static show(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || Toast.ensureContainer();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div>${message}</div>
      <button type="button">✕</button>
    `;

    const close = () => toast.remove();
    toast.querySelector('button').addEventListener('click', close);
    container.appendChild(toast);

    if (duration > 0) {
      setTimeout(close, duration);
    }
  }

  static ensureContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
  }
}
