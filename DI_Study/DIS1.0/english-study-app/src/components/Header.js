export class Header {
    constructor(container) {
        this.container = container;
        this.render();
    }

    render() {
        this.container.innerHTML = `
      <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
        <h1 style="font-size: 1.5rem; font-weight: 700; background: linear-gradient(to right, #2dd4bf, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          English Flow
        </h1>
        <button class="btn-icon" id="theme-toggle" aria-label="Toggle Theme">
          🌙
        </button>
      </header>
    `;

        // Simple theme toggle logic (placeholder for now as we are dark-first)
        this.container.querySelector('#theme-toggle').addEventListener('click', () => {
            // Future: Implement light mode
            alert('Light mode coming soon!');
        });
    }
}
