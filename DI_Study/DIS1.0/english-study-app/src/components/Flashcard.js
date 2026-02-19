export class Flashcard {
    constructor(container, onFlip) {
        this.container = container;
        this.onFlip = onFlip;
        this.isFlipped = false;
        this.data = null;
        this.render();
    }

    render() {
        // CSS for 3D flip is needed here or in style.css. I'll add inline styles for structure and rely on style.css for classes.
        // But specific flip styles are better in CSS. I will add them to style.css later or inject them here.
        // Let's inject a style tag for specific component styles to keep it self-contained or assume style.css has it.
        // I'll add the specific flip styles to style.css in a moment using replace_file_content, or just inline them.
        // Inline is messy for keyframes/transforms. I'll update style.css after this.

        this.container.innerHTML = `
      <div class="scene" style="perspective: 1000px; width: 100%; height: 400px; cursor: pointer;">
        <div class="card" style="width: 100%; height: 100%; position: relative; transition: transform 0.6s; transform-style: preserve-3d;">
          
          <!-- Front -->
          <div class="card-face card-front glass-panel" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px;">
            <h2 id="word-text" style="font-size: 3rem; font-weight: 700; text-align: center; margin-bottom: 10px;"></h2>
            <p style="color: var(--text-secondary); font-size: 1rem;">Tap to flip</p>
          </div>

          <!-- Back -->
          <div class="card-face card-back glass-panel" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; transform: rotateY(180deg); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px; text-align: center;">
            <h3 id="word-def" style="font-size: 1.2rem; margin-bottom: 20px; line-height: 1.6;"></h3>
            <div style="width: 40px; height: 2px; background: var(--accent-color); margin-bottom: 20px;"></div>
            <p id="word-ex" style="color: var(--text-secondary); font-style: italic;"></p>
          </div>

        </div>
      </div>
    `;

        this.cardElement = this.container.querySelector('.card');
        this.container.querySelector('.scene').addEventListener('click', () => this.flip());
    }

    setData(data) {
        this.data = data;
        this.container.querySelector('#word-text').textContent = data.word;
        this.container.querySelector('#word-def').textContent = data.definition;
        this.container.querySelector('#word-ex').textContent = `"${data.example}"`;

        // Reset flip state when data changes
        if (this.isFlipped) {
            this.flip(false); // Flip back instantly or smoothly? 
            // For now, just remove the class without animation if we want instant reset, 
            // but better to flip back first.
            this.isFlipped = false;
            this.cardElement.style.transform = 'rotateY(0deg)';
        }
    }

    flip(forceState) {
        if (typeof forceState === 'boolean') {
            this.isFlipped = forceState;
        } else {
            this.isFlipped = !this.isFlipped;
        }

        this.cardElement.style.transform = this.isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)';

        if (this.isFlipped && this.onFlip) {
            this.onFlip();
        }
    }
}
