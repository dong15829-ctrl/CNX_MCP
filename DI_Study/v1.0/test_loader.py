import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from backend.data_loader import load_insight_data
    print("Attempting to load data...")
    data = load_insight_data()
    
    if not data:
        print("ERROR: Data is empty.")
    else:
        print("Data loaded successfully!")
        print("Keys:", data.keys())
        if 'dates' in data:
            print("Dates:", data['dates'][:5])
        if 'summary' in data:
            print("Summary Keys:", data['summary'].keys())
            print("Market Insights:", data['summary'].get('market_insights', ['N/A'])[0][:20] if data['summary'].get('market_insights') else "Empty")
        
        # Check Sections
        for sec in ['market', 'product', 'size', 'price']:
            if sec in data:
                keys = list(data[sec].keys())
                hitlists = data[sec].get('hitlists', [])
                print(f"Section '{sec}' keys: {keys}, Hitlists Count: {len(hitlists)}")
                if len(hitlists) > 0:
                    print(f"  First Hitlist Month: {hitlists[0].get('month')}, Rows: {len(hitlists[0].get('rows'))}")
            else:
                print(f"WARNING: Section '{sec}' is MISSING.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
