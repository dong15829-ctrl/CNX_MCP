import pandas as pd
import json
from typing import List
import psycopg2
from src.db.connection import get_db_connection
from src.ingestion.models import IssueModel
from datetime import datetime

def parse_date(date_str):
    if pd.isna(date_str):
        return None
    # Adjust format based on actual CSV data. 
    # Example: "16/Jul/24 10:06 PM"
    try:
        return datetime.strptime(str(date_str), "%d/%b/%y %I:%M %p")
    except ValueError:
        return None

def load_csv_to_db(csv_path: str):
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.where(pd.notnull(df), None)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"Loading {len(df)} rows from {csv_path}...")
    
    for _, row in df.iterrows():
        # Map standard fields
        issue = IssueModel(
            issue_key=row.get('Issue key'),
            issue_id=row.get('Issue id'),
            summary=row.get('Summary', ''),
            description=row.get('Description', ''),
            status=row.get('Status'),
            issue_type=row.get('Issue Type'),
            priority=row.get('Priority'),
            created_at=parse_date(row.get('Created')),
            updated_at=parse_date(row.get('Updated')),
            assignee_id=row.get('Assignee'),
            reporter_id=row.get('Reporter'),
            custom_fields={} # TODO: Map custom fields dynamically
        )
        
        # Simple dynamic mapping for custom fields (columns starting with 'Custom field')
        for col in df.columns:
            if col.startswith('Custom field'):
                if not pd.isna(row[col]):
                    issue.custom_fields[col] = str(row[col])

        try:
            cur.execute("""
                INSERT INTO issues (
                    issue_key, issue_id, summary, description, status, issue_type, priority, 
                    created_at, updated_at, assignee_id, reporter_id, custom_fields
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (issue_key) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    custom_fields = EXCLUDED.custom_fields;
            """, (
                issue.issue_key, issue.issue_id, issue.summary, issue.description, issue.status, 
                issue.issue_type, issue.priority, issue.created_at, issue.updated_at, 
                issue.assignee_id, issue.reporter_id, json.dumps(issue.custom_fields)
            ))
        except Exception as e:
            print(f"Error inserting issue {issue.issue_key}: {e}")
            conn.rollback()
            continue
            
    conn.commit()
    cur.close()
    conn.close()
    print("Data loading complete.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load_csv_to_db(sys.argv[1])
    else:
        print("Usage: python loader.py <csv_path>")
