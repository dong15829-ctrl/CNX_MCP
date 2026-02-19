const STORAGE_KEY_PROGRESS = 'english_app_progress';
const STORAGE_KEY_CUSTOM_WORDS = 'english_app_custom_words';

export const Storage = {
    saveProgress(currentIndex) {
        localStorage.setItem(STORAGE_KEY_PROGRESS, JSON.stringify({ currentIndex }));
    },

    loadProgress() {
        const data = localStorage.getItem(STORAGE_KEY_PROGRESS);
        return data ? JSON.parse(data) : { currentIndex: 0 };
    },

    saveCustomWords(words) {
        localStorage.setItem(STORAGE_KEY_CUSTOM_WORDS, JSON.stringify(words));
    },

    loadCustomWords() {
        const data = localStorage.getItem(STORAGE_KEY_CUSTOM_WORDS);
        return data ? JSON.parse(data) : [];
    }
};
