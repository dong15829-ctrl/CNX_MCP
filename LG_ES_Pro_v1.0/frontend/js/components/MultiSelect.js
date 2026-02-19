export class MultiSelect {
  constructor(wrapEl, options = {}) {
    this.wrap = wrapEl;
    this.label = options.label || 'Select';
    this.items = options.items || [];
    this.selected = new Set(options.selected || []);
    this.changeCallback = null;
    this.handleOutside = this.handleOutside.bind(this);
    this.outsideBound = false;

    this.render(this.items, [...this.selected]);
  }

  onChange(callback) {
    this.changeCallback = callback;
  }

  getSelected() {
    return [...this.selected];
  }

  setItems(items, selectedItems = null) {
    this.items = items;
    const nextSelected = selectedItems ? new Set(selectedItems) : new Set(this.getSelected());
    this.selected = new Set([...nextSelected].filter((item) => items.includes(item)));
    this.render(this.items, [...this.selected]);
  }

  setSelected(selectedItems) {
    this.selected = new Set(selectedItems);
    this.render(this.items, [...this.selected]);
  }

  close() {
    this.wrap?.classList.remove('open');
  }

  open() {
    this.wrap?.classList.add('open');
  }

  toggle() {
    if (this.wrap?.classList.contains('open')) {
      this.close();
    } else {
      this.open();
    }
  }

  render(items, selectedItems = []) {
    if (!this.wrap) return;
    this.wrap.className = 'multiselect';
    this.items = items;
    this.selected = new Set(selectedItems);

    const labelText = this.getLabelText();

    this.wrap.innerHTML = `
      <button class="multiselect-button" type="button">
        <span>
          <strong>${this.label}</strong>
          <span>${labelText}</span>
        </span>
        <span>▾</span>
      </button>
      <div class="multiselect-panel">
        <div class="panel-actions">
          <button type="button" data-action="select-all">Select All</button>
          <button type="button" data-action="clear">Clear</button>
        </div>
        <div class="multiselect-list">
          ${items
            .map(
              (item) => `
                <label class="multiselect-item">
                  <input type="checkbox" value="${item}" ${this.selected.has(item) ? 'checked' : ''}>
                  <span>${item}</span>
                </label>
              `,
            )
            .join('')}
        </div>
      </div>
    `;

    const button = this.wrap.querySelector('.multiselect-button');
    const panel = this.wrap.querySelector('.multiselect-panel');

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      this.toggle();
    });

    panel.addEventListener('click', (event) => {
      event.stopPropagation();
      const target = event.target;
      if (target.matches('input[type="checkbox"]')) {
        const value = target.value;
        if (target.checked) {
          this.selected.add(value);
        } else {
          this.selected.delete(value);
        }
        this.notifyChange();
        this.updateButtonLabel();
      }

      if (target.matches('button[data-action="select-all"]')) {
        this.selected = new Set(this.items);
        this.render(this.items, [...this.selected]);
        this.notifyChange();
      }

      if (target.matches('button[data-action="clear"]')) {
        this.selected = new Set();
        this.render(this.items, []);
        this.notifyChange();
      }
    });

    if (!this.outsideBound) {
      document.addEventListener('click', this.handleOutside);
      this.outsideBound = true;
    }
  }

  handleOutside() {
    this.close();
  }

  updateButtonLabel() {
    const label = this.wrap.querySelector('.multiselect-button span span');
    if (label) label.textContent = this.getLabelText();
  }

  getLabelText() {
    if (this.selected.size === 0 || this.selected.size === this.items.length) {
      return 'All';
    }
    if (this.selected.size === 1) {
      return [...this.selected][0];
    }
    return `${this.selected.size} selected`;
  }

  notifyChange() {
    if (this.changeCallback) {
      this.changeCallback(this.getSelected());
    }
  }
}
