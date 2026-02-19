import json
import random
import re

def process_dictionary():
    try:
        # Load raw dictionary
        with open('dictionary_raw.json', 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        print(f"Loaded {len(raw_data)} words from raw dictionary.")
        
        processed_words = []
        id_counter = 1000  # Start IDs from 1000
        
        # Filter and process words
        # raw_data format: "WORD": "DEFINITION"
        
        keys = list(raw_data.keys())
        random.shuffle(keys) # Shuffle to get random selection
        
        for word in keys:
            definition = raw_data[word]
            
            # Skipping extremely short or long words, or words with obscure chars
            if len(word) < 3 or len(word) > 15 or not word.isalpha():
                continue
                
            # Clean definition
            # Sometimes definition is "See X" or very short. Filter those.
            if len(definition) < 10 or "See" in definition[:5]:
                continue
            
            # Basic Leveling Heuristic based on length and commonality characters
            level = 'intermediate'
            if len(word) <= 5:
                level = 'beginner'
            elif len(word) >= 9:
                level = 'advanced'
            
            # Pronunciation placeholder (Hard to generate without API, use simple placeholder)
            # Or use empty string, UI handles it gracefully?
            # Let's try to simulate IPA for fun? No, better leave it generic or empty.
            pronunciation = f"/{word.lower()}/" 
            
            processed_words.append({
                "id": id_counter,
                "word": word,
                "meaning": definition[:100] + ("..." if len(definition) > 100 else ""), # Truncate long defs
                "example": f"The word '{word}' is often used in this context.", # Placeholder example
                "pronunciation": pronunciation,
                "level": level
            })
            
            id_counter += 1
            
            if len(processed_words) >= 3500:
                break
        
        # Sort by ID
        processed_words.sort(key=lambda x: x['id'])
        
        # Save to src/data/words.json
        with open('src/data/words.json', 'w', encoding='utf-8') as f:
            json.dump(processed_words, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully generated {len(processed_words)} words into src/data/words.json")
        
    except Exception as e:
        print(f"Error processing dictionary: {e}")

if __name__ == "__main__":
    process_dictionary()
