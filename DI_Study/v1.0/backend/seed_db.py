from database import engine, Base
from etl_service import process_excel_to_db
import os

# Create Tables
Base.metadata.create_all(bind=engine)

# File Path
FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "251113_25 Oct AMZ Dashboard_TV_US_NFL.xlsm")

if os.path.exists(FILE_PATH):
    print("Seeding Database...")
    success = process_excel_to_db(FILE_PATH, "US", "2025-10")
    if success:
        print("Database Seeded Successfully!")
    else:
        print("Seeding Failed.")
else:
    print(f"File not found: {FILE_PATH}")
