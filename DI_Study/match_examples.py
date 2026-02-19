
import json
import re
import os
from collections import defaultdict

WORDS_PATH = 'src/data/words.json'
CORPUS_DIR = 'korean-parallel-corpora/korean-english-news-v1'
EN_CORPUS = os.path.join(CORPUS_DIR, 'korean-english-park.train.en')
KO_CORPUS = os.path.join(CORPUS_DIR, 'korean-english-park.train.ko')

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def build_index(en_lines):
    index = defaultdict(list)
    print("Building index...")
    for i, line in enumerate(en_lines):
        # Normalize and tokenize
        # Find all words, convert to lower case
        words = set(re.findall(r'\b[a-zA-Z]+\b', line.lower()))
        for w in words:
            index[w].append(i)
    print(f"Index built with {len(index)} unique words.")
    return index

def main():
    print("Loading words...")
    words_data = load_json(WORDS_PATH)
    
    print("Loading corpus...")
    with open(EN_CORPUS, 'r', encoding='utf-8') as f:
        en_lines = [line.strip() for line in f]
    with open(KO_CORPUS, 'r', encoding='utf-8') as f:
        ko_lines = [line.strip() for line in f]
        
    if len(en_lines) != len(ko_lines):
        print(f"Warning: Corpus length mismatch! EN: {len(en_lines)}, KO: {len(ko_lines)}")
        # Truncate to shorter length to be safe
        min_len = min(len(en_lines), len(ko_lines))
        en_lines = en_lines[:min_len]
        ko_lines = ko_lines[:min_len]

    index = build_index(en_lines)
    
    matched_count = 0
    
    print("Matching examples...")
    for entry in words_data:
        target_word = entry['word'].lower()
        
        # Look up directly
        candidate_indices = index.get(target_word)
        
        if candidate_indices:
            # Simple heuristic: valid lines, not too long, not too short
            # Prefer length between 20 and 100 characters for readability
            best_idx = -1
            best_score = float('inf')
            
            for idx in candidate_indices:
                line = en_lines[idx]
                if len(line) < 15 or len(line) > 150:
                    continue
                
                # Score: prefer shorter within range, but maybe not too short
                # For now, just take the first one that fits length criteria
                best_idx = idx
                break
            
            # If no "good" length found, fallback to first one if any exist
            if best_idx == -1 and candidate_indices:
                best_idx = candidate_indices[0]
                
            if best_idx != -1:
                entry['example'] = en_lines[best_idx]
                entry['example_meaning'] = ko_lines[best_idx]
                matched_count += 1
        else:
            # Clear the placeholder if no match found
            entry['example'] = ""
            entry['example_meaning'] = ""

    print(f"Matched examples for {matched_count} / {len(words_data)} words.")
    
    save_json(WORDS_PATH, words_data)
    print("Done.")

if __name__ == "__main__":
    main()
