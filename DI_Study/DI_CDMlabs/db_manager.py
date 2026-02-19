import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

DB_FILE = 'enrichment_archive.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

import sqlite3
import pandas as pd
import json
from datetime import datetime
import os
import time

DB_FILE = 'enrichment_archive.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Check if legacy table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    legacy_exists = c.fetchone()
    
    # New History Table
    # id: Auto-increment primary key
    # batch_id: Identifier for the run (e.g., 'v1_2023...', 'prompt_test_A')
    # sku: Not unique globally, but unique per batch ideally.
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS enrichment_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT,
        sku TEXT,
        category TEXT,
        country TEXT,
        title TEXT,
        brand_1 TEXT,
        brand_2 TEXT,
        resolution_1 TEXT,
        resolution_2 TEXT,
        inch TEXT,
        display_technology TEXT,
        led_type TEXT,
        refresh_rate TEXT,
        response_time TEXT,
        segment TEXT,
        others_yn TEXT,
        update_time TEXT,
        raw_gpt_response TEXT,
        execution_time REAL
    )
    ''')
    conn.commit()
    conn.close()

def migrate_legacy_data(target_batch_id):
    """Moves data from old 'products' table to 'enrichment_history'."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    if not c.fetchone():
        conn.close()
        return # No legacy data
        
    print(f"Migrating legacy 'products' table to 'enrichment_history' (Batch: {target_batch_id})...")
    
    # Get columns from legacy
    c.execute("PRAGMA table_info(products)")
    cols = [r[1] for r in c.fetchall()]
    col_str = ",".join(cols)
    
    # Copy data
    try:
        c.execute(f'''
        INSERT INTO enrichment_history (batch_id, {col_str})
        SELECT ?, {col_str} FROM products
        ''', (target_batch_id,))
        
        # Drop legacy
        c.execute("DROP TABLE products")
        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")
        
    conn.close()

def insert_result(data, batch_id):
    """
    Append a new record to history.
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Inject batch_id
    data['batch_id'] = batch_id
    
    keys = list(data.keys())
    placeholders = ',' .join(['?'] * len(keys))
    cols_str = ','.join(keys)
    values = tuple(data.values())
    
    query = f'''
    INSERT INTO enrichment_history ({cols_str})
    VALUES ({placeholders})
    '''
    
    try:
        c.execute(query, values)
        conn.commit()
    except Exception as e:
        print(f"[DB Error] {e}")
    finally:
        conn.close()

def get_processed_skus(batch_id):
    """Returns a set of SKUs that have been processed IN THIS BATCH."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT sku FROM enrichment_history WHERE batch_id = ?", (batch_id,))
        rows = c.fetchall()
        return {r[0] for r in rows}
    except:
        return set()
    finally:
        conn.close()

def export_to_excel(output_file='new_sku_nov_filled.xlsx', batch_id=None):
    """
    Exports content to Excel. 
    If batch_id provided, exports only that batch. 
    If None, exports the LATEST version of each SKU (deduplicated by update_time).
    """
    conn = get_connection()
    
    query = "SELECT * FROM enrichment_history"
    params = ()
    
    if batch_id:
        query += " WHERE batch_id = ?"
        params = (batch_id,)
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"Export error: {e}")
        conn.close()
        return

    conn.close()
    
    if df.empty:
        print("Database is empty. Nothing to export.")
        return

    # ALWAYS De-duplicate to ensure clean output (even within a single batch)
    # Sort by update_time desc and keep first
    df = df.sort_values('update_time', ascending=False).drop_duplicates('sku', keep='first')

    print(f"Exporting {len(df)} rows to {output_file}...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # TV Sheet
        tv_df = df[df['category'] == 'TV'].copy()
        if not tv_df.empty:
            tv_cols = ['brand_1', 'brand_2', 'resolution_1', 'resolution_2', 'inch', 'display_technology', 'led_type', 'others_yn', 'update_time', 'batch_id', 'execution_time']
            # Re-order
            desired_cols = ['sku', 'country', 'title'] + [c for c in tv_cols if c in tv_df.columns]
            tv_df[desired_cols].to_excel(writer, sheet_name='TV', index=False)
            
        # Monitor Sheet
        mo_df = df[df['category'] == 'Monitor'].copy()
        if not mo_df.empty:
            mo_cols = ['brand_1', 'brand_2', 'resolution_1', 'resolution_2', 'refresh_rate', 'inch', 'display_technology', 'segment', 'others_yn', 'update_time', 'batch_id', 'execution_time']
            desired_cols = ['sku', 'country', 'title'] + [c for c in mo_cols if c in mo_df.columns]
            mo_df[desired_cols].to_excel(writer, sheet_name='Monitor', index=False)
            
    print("Export complete.")
