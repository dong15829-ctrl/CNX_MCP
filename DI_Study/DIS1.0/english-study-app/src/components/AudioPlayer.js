export class AudioPlayer {
    constructor(container) {
        this.container = container;
        this.audio = new Audio();
        this.isPlaying = false;
        this.render();
    }

    render() {
        this.container.innerHTML = `
      <div class="glass-panel" style="padding: 20px; display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 20px;">
        <button class="btn-icon" id="play-btn" style="width: 64px; height: 64px; font-size: 1.5rem; background: var(--accent-color); color: #0f172a;">
          ▶
        </button>
        <div style="flex: 1; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
          <div id="progress-bar" style="width: 0%; height: 100%; background: var(--accent-color); transition: width 0.1s linear;"></div>
        </div>
      </div>
    `;

        this.playBtn = this.container.querySelector('#play-btn');
        this.progressBar = this.container.querySelector('#progress-bar');

        this.playBtn.addEventListener('click', () => {
            if (this.isPlaying) {
                this.stop();
            } else {
                this.audio.play();
            }
        });

        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            this.playBtn.innerHTML = '⏸';
        });

        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this.playBtn.innerHTML = '▶';
        });

        this.audio.addEventListener('ended', () => {
            this.isPlaying = false;
            this.playBtn.innerHTML = '▶';
            this.progressBar.style.width = '0%';
        });

        this.audio.addEventListener('timeupdate', () => {
            if (this.audio.duration) {
                const percent = (this.audio.currentTime / this.audio.duration) * 100;
                this.progressBar.style.width = `${percent}%`;
            }
        });
    }

    load(url) {
        this.audio.src = url;
        this.stop();
    }

    play() {
        this.audio.play();
    }

    stop() {
        this.audio.pause();
        this.audio.currentTime = 0;
    }
}
