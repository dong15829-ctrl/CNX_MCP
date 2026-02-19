import pandas as pd
import re
import os

FILE_PATH = 'new_sku_nov_filled.xlsx'

def clean_value(val):
    if pd.isna(val): return val
    s = str(val)
    # Remove common markdown code block artifacts
    # e.g., "plaintext\nSamsung", "tsv\nSamsung"
    cleaned = re.sub(r'^(plaintext|tsv|csv|python)\s+', '', s, flags=re.IGNORECASE)
    return cleaned.strip()

def main():
    if not os.path.exists(FILE_PATH):
        print("File not found.")
        return
        
    print(f"Loading {FILE_PATH}...")
    # Load ALL sheets first to avoid truncation when opening Writer
    try:
        all_dfs = pd.read_excel(FILE_PATH, sheet_name=None)
    except Exception as e:
        print(f"Error loading excel: {e}")
        return
    
    cleaned_dfs = {}
    
    # Process in memory
    for sheet_name, df in all_dfs.items():
        print(f"Cleaning sheet: {sheet_name}")
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_value)
        cleaned_dfs[sheet_name] = df
            
    # Save all at once
    print("Saving cleaned file...")
    with pd.ExcelWriter(FILE_PATH, engine='openpyxl') as writer:
        for sheet_name, df in cleaned_dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print("Done. Cleaned file saved.")

if __name__ == "__main__":
    main()
