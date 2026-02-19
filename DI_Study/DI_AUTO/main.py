import argparse
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from modules.browser import get_driver
from modules.shiftee import check_attendance
# Outlook modules removed per user request
from modules.notifier import send_report

def run_setup():
    """
    Runs in headed mode to allow user to log in and save session.
    """
    print("=== SETUP MODE ===")
    print("Opening browser... Please log in to Shiftee and Outlook manually.")
    print("Make sure to check 'Stay signed in' options.")
    
    driver = get_driver(headless=False)
    
    shiftee_url = os.getenv("SHIFTEE_URL")
    outlook_url = os.getenv("OUTLOOK_URL")
    
    try:
        driver.get(shiftee_url)
        print(f"Opened {shiftee_url}")
        input("Press Enter after you have logged in to Shiftee...")
        
        # Outlook login removed
        
        print("Session data should be saved in the profile directory.")
    except KeyboardInterrupt:
        print("\nSetup interrupted.")
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Morning Automation Script")
    parser.add_argument("--setup", action="store_true", help="Run in setup mode (headed) for manual login")
    parser.add_argument("--dry-run", action="store_true", help="Run without performing mutating actions")
    
    args = parser.parse_args()
    
    if args.setup:
        run_setup()
        sys.exit(0)
        
    print("=== STARTING MORNING AUTOMATION ===")
    
    # Initialize Driver
    # Default to headless unless debugging, but for visual confirmation user might want headed initially.
    # We will use headless=True by default for production.
    driver = get_driver(headless=True)
    
    report_lines = []
    messages = []
    
    try:
        # 1. Shiftee Attendance
        print("\n[1/3] Checking Attendance...")
        shiftee_url = os.getenv("SHIFTEE_URL")
        
        if args.dry_run:
            status, msg = True, "Dry Run: Skipped actual check-in"
        else:
            status, msg = check_attendance(driver, shiftee_url)
            
        report_lines.append(f"Attendance: {'OK' if status else 'FAILED'} ({msg})")
        
        # Outlook steps removed

    except Exception as e:
        error_msg = f"CRITICAL ERROR: {str(e)}"
        print(error_msg)
        report_lines.append(error_msg)
    finally:
        driver.quit()
        
    # 3. Notify
    print("\n[3/3] Generating Report...")
    final_report = "\n".join(report_lines)
    print("="*30)
    print(final_report)
    print("="*30)
    
    send_report(final_report)
    print("Done.")

if __name__ == "__main__":
    main()
