import json
import re
import random

def refine_vocabulary():
    print("1. Loading English Dictionary (Source of Truth)...")
    valid_eng_words = set()
    try:
        with open('dictionary_raw.json', 'r', encoding='utf-8') as f:
            eng_dict = json.load(f)
        
        for w in eng_dict.keys():
            w_clean = w.strip()
            # Filter: Alpha only, length 3~15, no spaces (single word)
            # This ensures we only get REAL English words, not phrases or weird chars.
            if w_clean.isalpha() and 3 <= len(w_clean) <= 15:
                valid_eng_words.add(w_clean.lower())
    except Exception as e:
        print(f"Error loading dictionary_raw.json: {e}")
        return

    print(f"Valid English Headwords: {len(valid_eng_words)}")

    print("2. Mapping Meanings from Kengdic...")
    eng_to_kor = {}
    
    try:
        with open('temp_kengdic/kengdic.tsv', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('id'): continue
                
                parts = line.strip().split('\t')
                # Kengdic structure: [1] Korean, [3] English Gloss
                if len(parts) < 4: continue
                
                kor_def = parts[1].strip()
                eng_defs = parts[3].lower() # Lowercase for matching
                
                # Skip if Korean part looks like English or empty
                if not kor_def or re.match(r'^[a-zA-Z]+$', kor_def):
                    continue

                # Clean Korean definition (remove hanja in brackets if any details, but Kengdic is usually clean)
                
                # Split English definitions by comma, semicolon
                # Example: "apple, fruit" -> map "apple"->kor, "fruit"->kor
                tokens = re.split(r'[,;]', eng_defs)
                
                for token in tokens:
                    token = token.strip()
                    if not token: continue
                    
                    # Intersect: Only accept if it's in our Valid English Words list
                    if token in valid_eng_words:
                        # Add to map
                        # If duplicate, prefer shorter meaning (likely more representative)
                        # or one that is purely Hangul
                        if token not in eng_to_kor:
                            eng_to_kor[token] = kor_def
                        else:
                            current_mean = eng_to_kor[token]
                            # Heuristic: shorter length often means 'main definition' in dictionary exports
                            if len(kor_def) < len(current_mean) and len(kor_def) >= 1:
                                eng_to_kor[token] = kor_def
                                
    except Exception as e:
        print(f"Error reading Kengdic: {e}")
        return

    print(f"Mapped Words (Eng->Kor): {len(eng_to_kor)}")
    
    print("3. Selecting and Formatting Words...")
    final_list = []
    id_counter = 1000
    
    # Sort for deterministic processing (before shuffle)
    all_mapped_words = sorted(list(eng_to_kor.keys()))
    
    # Categorize by length for creating balanced levels
    beginner = [w for w in all_mapped_words if len(w) <= 5]
    intermediate = [w for w in all_mapped_words if 6 <= len(w) <= 8]
    advanced = [w for w in all_mapped_words if len(w) >= 9]
    
    print(f"Beginner Candidates: {len(beginner)}")
    print(f"Intermediate Candidates: {len(intermediate)}")
    print(f"Advanced Candidates: {len(advanced)}")
    
    # Sample balanced dataset (Target: ~4000 total)
    random.seed(42)
    random.shuffle(beginner)
    random.shuffle(intermediate)
    random.shuffle(advanced)
    
    # Take top N from each
    selection = beginner[:1300] + intermediate[:1700] + advanced[:1000]
    
    # Create JSON objects
    for w in selection:
        w_cap = w.capitalize()
        meaning = eng_to_kor[w]
        
        level = 'advanced'
        if len(w) <= 5: level = 'beginner'
        elif len(w) <= 8: level = 'intermediate'
        
        # Use adambom dict for example if available? Too complex to join back now.
        # Use placeholder example.
        
        final_list.append({
            "id": id_counter,
            "word": w_cap,
            "meaning": meaning,
            "pronunciation": f"/{w}/", 
            "example": f"{w_cap} is a word appearing in the dictionary.",
            "level": level
        })
        id_counter += 1
        
    # Write to file
    output_file = 'src/data/words.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {len(final_list)} refined words in {output_file}")

if __name__ == "__main__":
    refine_vocabulary()
