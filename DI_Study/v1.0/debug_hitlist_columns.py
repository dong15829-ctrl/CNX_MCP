import pandas as pd
import os
from openpyxl import load_workbook

FILE_PATH = "251113_25 Oct AMZ Dashboard_TV_US_NFL.xlsm"

def inspect_hitlist_columns():
    print(f"Loading {FILE_PATH} with data_only=True...")
    try:
        wb = load_workbook(FILE_PATH, data_only=True, read_only=True)
        ws = wb['Insight_Hitlist']
        data = list(ws.values)
        wb.close()
        df = pd.DataFrame(data)
        
        # We know one table starts at Row 25 (Index 25) for Market Oct?
        # Or Row 15 from previous scan.
        # Let's inspect rows 15 (Sep) and 25 (Oct) around Column 6.
        
        # Print a block of columns 5 to 25 for Row 15
        print("\n--- Row 15 (Sep?) Data ---")
        row_15 = df.iloc[15, 5:25].values
        # Print with relative index
        for i, val in enumerate(row_15):
             print(f"Rel Col {i} (Abs {i+5}): {val}")

        print("\n--- Row 25 (Oct?) Data ---")
        row_25 = df.iloc[25, 5:25].values
        for i, val in enumerate(row_25):
             print(f"Rel Col {i} (Abs {i+5}): {val}")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_hitlist_columns()
