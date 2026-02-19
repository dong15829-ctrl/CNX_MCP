import pandas as pd
import os

def analyze_taxonomy():
    file_path = '/home/ubuntu/DI/DASH_JIRA_2/processed/dataset_modeling.csv'
    if not os.path.exists(file_path):
        print("Dataset not found.")
        return

    df = pd.read_csv(file_path)
    print(f"Total Records: {len(df)}")
    print("\n--- Columns ---")
    print(df.columns.tolist())

    print("\n--- Issue Type Distribution ---")
    if 'Issue Type' in df.columns:
        print(df['Issue Type'].value_counts().head(10))
    
    print("\n--- Project Name/Key Distribution ---")
    if 'Project name' in df.columns:
        print(df['Project name'].value_counts().head(10))
    elif 'Project key' in df.columns:
        print(df['Project key'].value_counts().head(10))

    print("\n--- Components Distribution ---")
    if 'Components' in df.columns:
        print(df['Components'].value_counts().head(10))

    print("\n--- Priority Distribution ---")
    if 'Priority' in df.columns:
        print(df['Priority'].value_counts().head(10))

if __name__ == "__main__":
    analyze_taxonomy()
