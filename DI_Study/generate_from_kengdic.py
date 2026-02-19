import json
import re
import random

def generate_from_kengdic():
    kengdic_file = 'temp_kengdic/kengdic.tsv'
    output_file = 'src/data/words.json'
    
    entries = []
    
    # Kengdic format: ID(maybe) \t Korean \t English
    # Need to verify column index from view_file result.
    # Usually: id \t korean \t english ...
    
    try:
        with open(kengdic_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('id'): continue
                
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue
                
                # Based on Kengdic TSV header: id, surface, hanja, gloss, ...
                # [1] surface (Korean)
                # [3] gloss (English)
                
                # Faster parsing
                korean = parts[1].strip()
                english_field = parts[3].lower() # Lowercase for check
                
                # Check if English field is simple enough
                # If it contains comma, split
                if ',' in english_field or ';' in english_field:
                    # Clean split
                    tokens = english_field.replace(';', ',').split(',')
                else:
                    tokens = [english_field]
                
                for token in tokens:
                    token = token.strip()
                    # Check length and alpha (ASCII only)
                    if 3 <= len(token) <= 15 and re.match(r'^[a-zA-Z]+$', token):
                        # Capitalize first letter
                        w = token.capitalize()
                        entries.append({'word': w, 'meaning': korean})
                        
    except Exception as e:
        print(f"Error reading dictionary: {e}")
        return

    print(f"Extracted {len(entries)} raw entries.")
    
    unique_words = {}
    for entry in entries:
        w = entry['word']
        m = entry['meaning']
        if w not in unique_words:
            unique_words[w] = m
        else:
            # Overwrite if current meaning is shorter (likely more basic)
            if len(m) < len(unique_words[w]):
                unique_words[w] = m
                
    print(f"Unique words: {len(unique_words)}")
    
    sorted_unique = sorted(unique_words.keys(), key=len)
    
    final_list = []
    id_counter = 1000
    
    # Take up to 4000
    for w in sorted_unique[:4000]:
        level = 'intermediate'
        if len(w) <= 5: level = 'beginner'
        elif len(w) >= 9: level = 'advanced'
        
        final_list.append({
            "id": id_counter,
            "word": w,
            "meaning": unique_words[w],
            "pronunciation": f"/{w.lower()}/",
            "example": f"Example sentence for {w}",
            "level": level
        })
        id_counter += 1
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)
        
    print(f"Done. {len(final_list)} words written.")

if __name__ == "__main__":
    generate_from_kengdic()
