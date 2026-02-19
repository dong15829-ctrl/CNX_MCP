from googlesearch import search as google_search
import os
import pandas as pd
import openai
from duckduckgo_search import DDGS
from dotenv import load_dotenv
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import json
from datetime import datetime

import trafilatura
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import db_manager

# v11: Gemini 3.0 Pro Mode (Deep Reading + Long Context + Reasoning)
BATCH_ID = "Batch_v11_Gemini3Pro_DeepRead_20251223"

TRUSTED_DOMAINS = [
    'displayspecifications.com', 'rtings.com', 'tomshardware.com', 
    'samsung.com', 'lg.com', 'dell.com', 'hp.com', 'acer.com', 
    'asus.com', 'benq.com', 'msi.com', 'philips.com', 'sony.com',
    'manualslib.com' 
]

# 1. Setup
load_dotenv()
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Disabled for Gemini Switch

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

INPUT_FILE = 'new_sku_nov.xlsx'
OUTPUT_FILE = 'new_sku_nov_filled.xlsx'
TV_PROMPT_FILE = 'tv_prompt.txt'
MO_PROMPT_FILE = 'mo_prompt.txt'

PRINT_LOCK = threading.Lock()

def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

tv_prompt_template = load_prompt(TV_PROMPT_FILE)
mo_prompt_template = load_prompt(MO_PROMPT_FILE)

def get_amazon_tld(country_code):
    country_code = str(country_code).upper()
    mapping = {
        'US': 'com', 'GB': 'co.uk', 'DE': 'de', 'FR': 'fr', 'ES': 'es', 
        'IT': 'it', 'JP': 'co.jp', 'CA': 'ca', 'AU': 'com.au', 'IN': 'in',
        'NL': 'nl', 'BR': 'com.br', 'MX': 'com.mx', 'TR': 'com.tr', 
        'SA': 'sa', 'AE': 'ae', 'SE': 'se', 'PL': 'pl', 'SG': 'sg', 'BE': 'com.be'
    }
    return mapping.get(country_code, 'com') 

def search_serper(query):
    print(f"      [Serper] Searching: {query}...")
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": 3  # Get top 3
    })
    headers = {
        'X-API-KEY': os.getenv('SERPER_API_KEY'),
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        results_text = ""
        # Handle organic results
        if 'organic' in data:
            for item in data['organic']:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                results_text += f"\nSource: {title}\nLink: {link}\nContent: {snippet}\n"
        return results_text
    except Exception as e:
        print(f"      [Serper Error] {e}")
        return ""

def search_with_strategy(sku, country, brand, model_code, title, strategy):
    ddgs = DDGS()
    tld = get_amazon_tld(country)
    
    query = ""
    # Enhanced Queries for Accuracy
    if strategy == 'ASIN':
        query = f"site:amazon.{tld} {sku}"
    elif strategy == 'MODEL':
        if brand and model_code and str(model_code).lower() != 'nan':
            # Primary: Generic spec search
            query = f"{brand} {model_code} specifications"
            # Secondary: Targeted high-quality source (displayspecifications is great for screens)
            query_targeted = f"site:displayspecifications.com {brand} {model_code}"
        else:
            return None 
    elif strategy == 'TITLE':
        query = f"{title} specs"
    elif strategy == 'AGGRESSIVE':
        # Last resort: explicitly ask for key fields AND raw documents
        query = f"{title} resolution refresh rate specifications datasheet manual"
    
    print(f"    [Strategy: {strategy}] Searching: {query}...")
    
    results_text = ""
    
    # 1. Execute Serper (Google) - Primary Context
    try:
        serper_res = search_serper(query)
        if serper_res:
             results_text += f"\n--- [Serper (Google)] ---\n{serper_res}\n"
        
        # If MODEL strategy, try targeted search too
        if strategy == 'MODEL' and 'query_targeted' in locals():
             extra_res = search_serper(query_targeted)
             if extra_res:
                 results_text += f"\n--- [Serper (Targeted)] ---\n{extra_res}\n"

    except Exception as e:
        print(f"      [Serper Error] {e}")

    # 2. Execute DuckDuckGo - Supplementary Context
    try:
        ddg_res_text = ""
        # Increased limit for better coverage
        results = ddgs.text(query, max_results=3)
        if results:
            for r in results:
                ddg_res_text += f"\nSource: {r['title']}\nLink: {r['href']}\nContent: {r['body']}\n"
        
        if ddg_res_text:
             results_text += f"\n--- [DuckDuckGo] ---\n{ddg_res_text}\n"
    except Exception as e:
        print(f"      [DDG Error] {e}")

    return results_text[:20000] # Doubled buffer for Raw Data Extraction

def call_gemini(system_prompt, user_query):
    """
    Calls Gemini 3.0 Pro (Preview) for state-of-the-art reasoning and massive context.
    """
    try:
        # Using Gemini 3.0 Pro Preview (Dec 2025 SOTA)
        model = genai.GenerativeModel('models/gemini-3-pro-preview')
        
        full_prompt = f"{system_prompt}\n\nUser Query:\n{user_query}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        return response.text
    except Exception as e:
        print(f"      [Gemini Error] {e}")
        return None

def parse_gpt_response(response_text):
    # Parses TSV output from LLM
    if not response_text: return []
    
    # Remove markdown code blocks if present
    clean_text = re.sub(r"```(tsv|csv|plaintext|python|text)?", "", response_text).replace("```", "").strip()
    
    lines = clean_text.split('\n')
    parsed_data = []
    
    for line in lines:
        if not line.strip(): continue
        parts = line.split('\t')
        parsed_data.append([p.strip() for p in parts])
        
    return parsed_data

def is_valid_result(data_dict, category):
    # Definition of "Valid": Key fields are not '-' and meaningful data has been added.
    
    # Input file has 'resolution_1' pre-filled with garbage (Brand names) for TV.
    # Input file has 'inch' as empty/NaN.
    # So we check 'inch' (or 'refresh_rate' for Monitor) to determine if we have processed it.
    
    val_inch = data_dict.get('inch', '-')
    others = data_dict.get('others_yn', '-')
    
    if str(others).lower() == 'others':
        return True # Valid classification as Others
    
    # If inch is missing, we assume it's NOT valid/processed yet.
    if pd.isna(val_inch) or str(val_inch).strip() in ['-', 'nan', 'NaN', '']:
        return False 
        
    return True

def process_sku(row, sheet_name, processed_skus_set, config):
    sku = str(row['sku']).strip()
    
    # Resume Check
    if sku in processed_skus_set:
        return # Skip
    
    # Identify Info
    country = row['country']
    brand = row.get('brand_1', '') 
    if pd.isna(brand): brand = row.get('brand_2', '')
    model = row.get('model_code', '')
    title = row['title']
    
    with PRINT_LOCK:
        print(f"[Start] Processing {sku}...")
        
    t_start = time.time()
    
    # Accumulate search results from all strategies
    combined_search_res = ""
    start_strategies = ['ASIN', 'MODEL', 'TITLE', 'AGGRESSIVE']
    
    # Needs global access or passed config
    prompt_template = load_prompt(config['prompt_file'])
    target_cols = config['cols']
    
    # Search Phase
    for strategy in start_strategies:
        search_res_for_strategy = search_with_strategy(sku, country, brand, model, title, strategy)
        if search_res_for_strategy:
            combined_search_res += f"\n--- Search Results for Strategy: {strategy} ---\n{search_res_for_strategy}\n"

    # Gemini Phase
    full_query = f"Target SKU: {sku}\nBrand: {brand}\nModel: {model}\nTitle: {title}\n\nSearch Context:\n{combined_search_res}"
    
    gpt_response = call_gemini(prompt_template, full_query)
    
    if gpt_response:
        parsed_rows = parse_gpt_response(gpt_response)
        
        if parsed_rows:
            parts = parsed_rows[0]
            expected_data_cols_count = len(target_cols) - 1
            
            if len(parts) == expected_data_cols_count:
                temp_data = {target_cols[i]: parts[i] for i in range(expected_data_cols_count)}
                
                # Rule: Gaming > HRM > Mainstream (Monitor)
                if sheet_name == 'Monitor':
                    try:
                        rr_val = 60
                        if 'refresh_rate' in temp_data and temp_data['refresh_rate'].replace('.','',1).isdigit():
                            rr_val = float(temp_data['refresh_rate'])
                        
                        res_width = 0
                        if 'resolution_1' in temp_data and 'x' in temp_data['resolution_1']:
                            res_width = int(temp_data['resolution_1'].split('x')[0].strip())

                        if rr_val >= 144:
                            temp_data['segment'] = 'Gaming'
                        elif res_width >= 3440:
                            temp_data['segment'] = 'HRM'
                        elif temp_data.get('segment') not in ['Gaming', 'HRM', 'Others']:
                            temp_data['segment'] = 'Mainstream'
                    except:
                        pass 

                # DB Record
                db_record = temp_data.copy()
                db_record['sku'] = sku
                db_record['category'] = sheet_name
                db_record['country'] = country
                db_record['title'] = title
                db_record['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db_record['execution_time'] = round(time.time() - t_start, 2)
                
                # Validity check
                if is_valid_result(temp_data, sheet_name):
                    with PRINT_LOCK:
                        print(f"      -> [Success] {sku} ({db_record['execution_time']}s)")
                    
                    # DB Insert is thread-safe (new connection per call)
                    db_manager.insert_result(db_record, BATCH_ID)
                    return
                else:
                    with PRINT_LOCK:
                        print(f"      -> [Failed Validation] {sku}")
                    return

            else:
                 with PRINT_LOCK:
                     print(f"      -> [Column Mismatch] {sku}")
                 return

    with PRINT_LOCK:
        print(f"      -> [No Result] {sku}")

def main():
    print(f"Loading input data: {INPUT_FILE}")
    print(f"Current Batch ID: {BATCH_ID}")
    
    if not os.path.exists(INPUT_FILE):
        print("Input file not found.")
        return

    # Initialize DB & Helper
    db_manager.init_db()
    
    # Migrate any legacy data (from the 370 records we stopped) to this batch
    # This allows us to resume strictly from where we left off in THIS batch context.
    db_manager.migrate_legacy_data(BATCH_ID)
    
    # Get SKUs done in THIS batch
    processed_skus = db_manager.get_processed_skus(BATCH_ID)
    print(f"Resuming... {len(processed_skus)} SKUs already in DB for this batch.")

    try:
        all_sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    sheet_configs = [
        {'name': 'TV', 'prompt_file': TV_PROMPT_FILE, 
         'cols': ['brand_1', 'brand_2', 'resolution_1', 'resolution_2', 'inch', 'display_technology', 'led_type', 'others_yn', 'update_time']},
        {'name': 'Monitor', 'prompt_file': MO_PROMPT_FILE, 
         'cols': ['brand_1', 'brand_2', 'resolution_1', 'resolution_2', 'refresh_rate', 'inch', 'display_technology', 'segment', 'others_yn', 'update_time']}
    ]

    for config in sheet_configs:
        sheet_name = config['name']
        if sheet_name not in all_sheets:
            print(f"Sheet '{sheet_name}' not found. Skipping.")
            continue
            
        print(f"\n=== Processing {sheet_name} ===")
        df = all_sheets[sheet_name]
        
        # Parallel Execution
        print(f"Starting parallel processing for {len(df)} SKUs with 5 workers...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            for index, row in df.iterrows():
                executor.submit(process_sku, row, sheet_name, processed_skus, config)
                
        print(f"Sheet {sheet_name} processing submitted.")

    # Final Export
    print("\nProcessing complete. Exporting final Excel (Latest Version)...")
    db_manager.export_to_excel(OUTPUT_FILE)
    print("Done.")

if __name__ == "__main__":
    main()
