from backend.data_loader import load_insight_data
import pandas as pd
import numpy as np

def debug_values():
    print("Loading Data...")
    data = load_insight_data()
    
    sections = ['market', 'product', 'size', 'price']
    for sec in sections:
        print(f"--- {sec.upper()} SECTION ---")
        if 'breakdown_share' in data[sec]:
            share_data = data[sec]['breakdown_share']
            print("Breakdown Share Keys:", share_data.keys())
            for k, v in share_data.items():
                print(f"  Key: {k}")
                print(f"  Values: {v}")
                # Check types
                types = [type(x) for x in v]
                print(f"  Types: {types}")
                # Check for NaNs
                has_nan = any(pd.isna(x) for x in v)
                print(f"  Has NaNs: {has_nan}")
        else:
            print("  No breakdown_share found!")

if __name__ == "__main__":
    debug_values()
