import json
import csv
import re

def translate_to_korean():
    words_file = 'src/data/words.json'
    kengdic_file = 'temp_kengdic/kengdic.tsv'
    
    # Load existing words
    with open(words_file, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    
    print(f"Loaded {len(words_data)} English words to translate.")
    
    # Load Kengdic
    # Format: id (0) | surface (1) | gloss (2) ... ? No, standard kengdic is often:
    # hanja | korean | english definition ...
    # Let's inspect the TSV structure first via heuristic or just read lines.
    # Usually: KOREAN \t ENGLISH_DEF
    
    # We will build a dictionary: English Word -> Korean Definition
    eng_to_kor = {}
    
    try:
        with open(kengdic_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    continue
                
                # Kengdic structure might vary. Often:
                # index 1 is Korean word
                # index varies for English meanings.
                # Let's assume the file content based on common Kengdic structure:
                # [0] ID? [1] Korean [2] English ...
                
                # To be safe, we will search for the english word in the line.
                # But that's slow.
                # Let's assume parts have English meanings in them.
                # We need to map ENGLISH WORD -> KOREAN WORD (meaning).
                
                # Example Kengdic line:
                # 1024	사과	apple; apology
                
                korean_word = parts[1].strip()
                english_part = parts[2].lower() if len(parts) > 2 else ""
                
                # Split english part by synonyms
                synonyms = [w.strip() for w in re.split(r'[,;]', english_part)]
                
                for syn in synonyms:
                    if syn and syn not in eng_to_kor:
                        eng_to_kor[syn] = korean_word
                    # If multiple Korean words exist for one English word, maybe keep first or append?
                    # Let's keep the first one found for simplicity, or overwrite?
                    # "apple" -> "사과" is good.
    except Exception as e:
        print(f"Error reading dictionary: {e}")
        return

    print(f"Built dictionary map with {len(eng_to_kor)} English keys.")
    
    translated_count = 0
    
    for entry in words_data:
        word_lower = entry['word'].lower()
        
        if word_lower in eng_to_kor:
            # Found a match!
            entry['meaning'] = eng_to_kor[word_lower]
            translated_count += 1
        elif word_lower.endswith('s') and word_lower[:-1] in eng_to_kor:
            # Simple plural check
            entry['meaning'] = eng_to_kor[word_lower[:-1]]
            translated_count += 1
    
    print(f"Translated {translated_count} out of {len(words_data)} words.")
    
    # Save back
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(words_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    translate_to_korean()
