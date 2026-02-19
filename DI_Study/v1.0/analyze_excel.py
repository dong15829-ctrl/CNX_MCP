import pandas as pd
import os

file_path = "251113_25 Oct AMZ Dashboard_TV_US_NFL.xlsm"

print(f"Analyzing: {file_path}")

try:
    # Load the Excel file (just the sheet names first to be fast)
    xl = pd.ExcelFile(file_path)
    print(f"\nSheet Names: {xl.sheet_names}")

    # Search for specific row signature
    sig_asin = 'B0F19KLHG3'
    # We look for a row containing this ASIN and maybe traffic/qty
    print(f"\n--- FIND ROW WITH {sig_asin} ---")
    
    for sheet in xl.sheet_names:
        try:
            df = xl.parse(sheet, header=None)
            for r in range(len(df)):
                row_vals = [str(x) for x in df.iloc[r, :].values]
                # Check for ASIN
                if any(sig_asin in x for x in row_vals):
                    # Found ASIN, print row
                    print(f"Sheet '{sheet}' Row {r}: {row_vals}")
        except Exception as e:
            pass
            
except Exception as e:
    print(f"Error opening file: {e}")

