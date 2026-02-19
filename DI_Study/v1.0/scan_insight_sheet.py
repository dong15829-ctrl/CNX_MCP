import pandas as pd
from openpyxl import load_workbook

FILE_PATH = "251113_25 Oct AMZ Dashboard_TV_US_NFL.xlsm"

def scan_insight():
    print(f"Scanning 'Insight' sheet in {FILE_PATH}...")
    try:
        # Load with data_only
        wb = load_workbook(FILE_PATH, data_only=True, read_only=True)
        ws = wb['Insight']
        data = list(ws.values)
        wb.close()
        df = pd.DataFrame(data)
        
        print(f"Sheet Shape: {df.shape}")
        
        # Scan for [1, 2, 3] sequences in all columns
        for c in range(len(df.columns)):
            col_vals = df.iloc[:, c].tolist()
            int_vals = []
            for x in col_vals:
                try:
                    val = float(x)
                    if val.is_integer():
                         int_vals.append(int(val))
                    else:
                         int_vals.append(-999)
                except:
                    int_vals.append(-999)
            
            # Use strict window
            found_rows = []
            for r in range(len(int_vals) - 3):
                if int_vals[r:r+3] == [1, 2, 3]:
                    found_rows.append(r)
            
            if found_rows:
                print(f"Column {c}: Found sequences starting at rows {found_rows}")
                # Print context (Header check)
                header_ctx = df.iloc[found_rows[0]-1, c] if found_rows[0]>0 else "N/A"
                print(f"  Header Context (Row-1): {header_ctx}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_insight()
