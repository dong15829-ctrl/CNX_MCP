import pandas as pd
import numpy as np
import os

MASTER_FILE = 'modelmaster_new_sku.xlsx'
TARGET_FILE = 'new_sku_nov_filled.xlsx'

def fast_normalize(val):
    """Normalize string values for comparison"""
    if pd.isna(val): return ""
    s = str(val).strip().lower()
    if s in ['-', 'nan', 'na', '']: return ""
    s = s.replace('\xa0', ' ').replace('\t', '')
    if 'plaintext' in s: s = s.replace('plaintext', '').strip()
    return s

def compare_dataframe(df_target, df_master, cols_to_compare):
    # Ensure SKU is string keys
    df_master['sku'] = df_master['sku'].astype(str).str.strip()
    df_target['sku'] = df_target['sku'].astype(str).str.strip()
    
    # Merge
    merged = pd.merge(df_target, df_master, on='sku', how='left', suffixes=('', '_master'))
    
    results = []
    details = []
    
    match_count = 0
    total_count = len(merged)

    for idx, row in merged.iterrows():
        mismatches = []
        
        # Check Others Logic first (category level)
        m_others = fast_normalize(row.get(f'others_yn_master', ''))
        t_others = fast_normalize(row.get('others_yn', ''))
        
        if m_others == 'others' and t_others == 'others':
            results.append('Correct (Others)')
            details.append('')
            match_count += 1
            continue
            
        # Compare columns
        for col in cols_to_compare:
            m_val = fast_normalize(row.get(f'{col}_master'))
            t_val = fast_normalize(row.get(col))
            
            # Numeric leniency
            if col in ['inch', 'refresh_rate']:
                try:
                    if m_val and t_val:
                        if float(m_val) == float(t_val): continue
                except:
                    pass
            
            if m_val != t_val:
                mismatches.append(f"{col}({t_val} vs {m_val})")
        
        if not mismatches:
            results.append('Correct')
            details.append('')
            match_count += 1
        else:
            results.append('Incorrect')
            details.append(', '.join(mismatches))

    # Add columns to merged df to keep alignment
    merged['validation_result'] = results
    merged['validation_details'] = details
    
    # We want to return the target dataframe structure + validation cols
    # The merge might have brought in _master columns, we should drop them or keep them?
    # User might want to see what the master had. Let's keep them but maybe clean up?
    # For simplicity, returning the merged DF including master cols is most informative for debugging.
    
    return merged, match_count, total_count

def main():
    if not os.path.exists(MASTER_FILE) or not os.path.exists(TARGET_FILE):
        print("Files not found.")
        return

    tv_cols = ['brand_1', 'resolution_1', 'inch', 'display_technology', 'others_yn']
    mo_cols = ['brand_1', 'resolution_1', 'refresh_rate', 'inch', 'segment', 'others_yn']
    
    # 1. READ EVERYTHING FIRST
    try:
        dict_master = pd.read_excel(MASTER_FILE, sheet_name=None, engine='openpyxl')
        dict_target = pd.read_excel(TARGET_FILE, sheet_name=None, engine='openpyxl')
    except Exception as e:
        print(f"Error reading input files: {e}")
        return

    final_sheets = {}
    
    # 2. PROCESS IN MEMORY
    # TV
    if 'TV' in dict_target and 'TV' in dict_master:
        print("\nComparing TV...")
        df_tv, m, t = compare_dataframe(dict_target['TV'], dict_master['TV'], tv_cols)
        final_sheets['TV'] = df_tv
        print(f"  Accuracy: {m}/{t} ({m/t*100:.1f}%)")
    elif 'TV' in dict_target:
        final_sheets['TV'] = dict_target['TV']
        
    # Monitor
    if 'Monitor' in dict_target and 'Monitor' in dict_master:
        print("\nComparing Monitor...")
        df_mo, m, t = compare_dataframe(dict_target['Monitor'], dict_master['Monitor'], mo_cols)
        final_sheets['Monitor'] = df_mo
        print(f"  Accuracy: {m}/{t} ({m/t*100:.1f}%)")
    elif 'Monitor' in dict_target:
        final_sheets['Monitor'] = dict_target['Monitor']

    # 3. WRITE ONCE
    print(f"\nSaving validated file to {TARGET_FILE}...")
    with pd.ExcelWriter(TARGET_FILE, engine='openpyxl') as writer:
        for name, df in final_sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            
    print("Done.")

if __name__ == "__main__":
    main()
