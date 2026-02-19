
import os
import re
import json
from collections import Counter

# Paths
CORPUS_EN = 'korean-parallel-corpora/korean-english-news-v1/korean-english-park.train.en'
KENGDIC_PATH = 'temp_kengdic/kengdic.tsv'
OUTPUT_PATH = 'src/data/words.json'

def get_frequency_list(limit=5000):
    print("Counting word frequencies from corpus...")
    word_counts = Counter()
    try:
        with open(CORPUS_EN, 'r', encoding='utf-8') as f:
            for line in f:
                # Tokenize simple: lowercase, keep only alphabets
                words = re.findall(r'\b[a-z]{3,}\b', line.lower()) 
                word_counts.update(words)
    except FileNotFoundError:
        print("Corpus file not found.")
        return []
    
    # Filter out very rare words
    common_words = [w for w, c in word_counts.most_common(limit)]
    print(f"Top 10 words: {common_words[:10]}")
    return common_words

def load_kengdic_meanings():
    print("Loading Kengdic meanings...")
    # Kengdic format: id | surface(Korean) | hanja | gloss(English) | ...
    # Wait, previous view said: id | surface | hanja | gloss | ...
    # But gloss is the *English definition* of the *Korean word*? 
    # Or is it Korean definition of English word?
    # Actually Kengdic is usually Korean-English dictionary. 
    # But we want English -> Korean.
    # Let's check the file content again or assume we can reverse it.
    # The 'gloss' usually contains the English translation.
    # So we map English Gloss Word -> Korean Surface.
    
    eng_to_kor = {}
    
    with open(KENGDIC_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            
            kor_word = parts[1]
            eng_gloss = parts[3]
            
            # Gloss often has multiple words "apple, apology"
            # We need to split them to reverse map properly?
            # Or is it a full definition?
            # Let's look at the gloss more carefully in a separate step if needed.
            # For now, simplistic reverse mapping:
            
            # Clean gloss
            glosses = [g.strip().lower() for g in eng_gloss.split(',')]
            for g in glosses:
                if g not in eng_to_kor:
                    eng_to_kor[g] = []
                # Add Korean word if not duplicate
                if kor_word not in eng_to_kor[g]:
                    eng_to_kor[g].append(kor_word)
                    
    print(f"Loaded {len(eng_to_kor)} English terms mapped to Korean.")
    return eng_to_kor

def main():
    # 1. Get useful words (Frequency based)
    vocab_list = get_frequency_list(4000)
    
    # 2. Get meanings
    descriptions = load_kengdic_meanings()
    
    final_words = []
    id_counter = 1000
    
    print("Merging data...")
    for word in vocab_list:
        if word in descriptions:
            meanings = descriptions[word]
            # Filter meanings?
            # e.g., remove Hanja contained ones if any? Kengdic surface is usually Hangul.
            
            # Select primary meaning (shortest is often best? or first?)
            # Sort by length to find the most "concise" meaning for quiz
            meanings.sort(key=len)
            primary = meanings[0]
            
            # Combine all for detailed view (~3 max)
            full_meanings = meanings[:5]
            
            # Difficulty level
            level = 'beginner'
            if len(word) > 5: level = 'intermediate'
            if len(word) > 8: level = 'advanced'
            
            final_words.append({
                "id": id_counter,
                "word": word.capitalize(),
                "meaning": primary, # Quiz extraction
                "meanings": full_meanings, # Card detailed view
                "pronunciation": f"/{word}/",
                "example": "", # Placeholder, will be filled by match_examples.py later
                "example_meaning": "",
                "level": level
            })
            id_counter += 1
            
    print(f"Generated {len(final_words)} refined words.")
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_words, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
