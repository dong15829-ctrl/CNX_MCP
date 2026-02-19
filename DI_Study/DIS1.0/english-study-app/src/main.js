import { Header } from './components/Header.js';
import { Flashcard } from './components/Flashcard.js';
import { AudioPlayer } from './components/AudioPlayer.js';
import { Storage } from './storage.js';
import wordsData from './data/words.json' with { type: "json" }; // Import JSON module (supported in modern browsers/Vite, but pure JS might need fetch)

// Note: "import ... with { type: 'json' }" is a stage 3 proposal. 
// In pure browser environment without bundler, fetching JSON is safer.
// I will use fetch to be safe.

const app = document.getElementById('app');

// Layout
app.innerHTML = `
  <div id="header-container"></div>
  <div id="flashcard-container" class="fade-in"></div>
  <div id="audio-container" class="fade-in"></div>
  
  <div style="display: flex; justify-content: space-between; margin-top: 40px;">
    <button id="prev-btn" class="btn">← Prev</button>
    <button id="next-btn" class="btn">Next →</button>
  </div>
`;

const header = new Header(document.getElementById('header-container'));
const audioPlayer = new AudioPlayer(document.getElementById('audio-container'));
const flashcard = new Flashcard(document.getElementById('flashcard-container'), () => {
    // Auto play audio on flip?
    // audioPlayer.play(); 
});

let words = [];
let currentIndex = 0;

async function init() {
    // Load words
    try {
        const response = await fetch('./src/data/words.json');
        words = await response.json();

        // Load progress
        const progress = Storage.loadProgress();
        currentIndex = progress.currentIndex < words.length ? progress.currentIndex : 0;

        updateUI();
    } catch (e) {
        console.error("Failed to load data", e);
        app.innerHTML += `<p style="color: red; text-align: center;">Failed to load data. Please check console.</p>`;
    }
}

function updateUI() {
    const word = words[currentIndex];
    flashcard.setData(word);
    audioPlayer.load(word.audioUrl);

    // Update buttons
    document.getElementById('prev-btn').disabled = currentIndex === 0;
    document.getElementById('prev-btn').style.opacity = currentIndex === 0 ? 0.5 : 1;

    document.getElementById('next-btn').disabled = currentIndex === words.length - 1;
    document.getElementById('next-btn').style.opacity = currentIndex === words.length - 1 ? 0.5 : 1;

    // Save progress
    Storage.saveProgress(currentIndex);
}

document.getElementById('prev-btn').addEventListener('click', () => {
    if (currentIndex > 0) {
        currentIndex--;
        updateUI();
    }
});

document.getElementById('next-btn').addEventListener('click', () => {
    if (currentIndex < words.length - 1) {
        currentIndex++;
        updateUI();
    }
});

init();
