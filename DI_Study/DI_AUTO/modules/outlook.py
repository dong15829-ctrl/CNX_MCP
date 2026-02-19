import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_unread_emails(driver, url):
    """
    Checks for unread emails in Outlook.
    """
    print(f"Navigating to Outlook Mail: {url}")
    driver.get(url)
    
    try:
        print("Waiting for inbox to load...")
        # Wait for the main list of emails. 
        # Outlook class names are obfuscated (e.g., custom properties).
        # We look for elements that typically represent email rows.
        time.sleep(8) # Outlook is heavy, give it time
        
        unread_emails = []
        
        # Strategy: Look for specific aria-label or status indicators
        # Common in Outlook: aria-label="Unread" or similar
        
        # Searching for elements with 'aria-label' containing 'Unread'
        # This is a broad search suitable for initial version
        unread_elements = driver.find_elements(By.XPATH, "//*[@aria-label and contains(@aria-label, 'Unread')]")
        
        print(f"Found {len(unread_elements)} potential unread items.")
        
        for elem in unread_elements[:5]: # Limit to 5
            try:
                # Try to extract text. Usually aria-label has the full summary.
                summary = elem.get_attribute("aria-label")
                if summary:
                    unread_emails.append(summary)
            except:
                continue
                
        return unread_emails

    except Exception as e:
        print(f"Error checking emails: {e}")
        return []

def get_daily_schedule(driver):
    """
    Checks daily schedule (Calendar).
     Assumes user is already logged in (shared session).
    """
    calendar_url = "https://outlook.office.com/calendar/view/day"
    print(f"Navigating to Outlook Calendar: {calendar_url}")
    driver.get(calendar_url)
    
    events = []
    try:
        print("Waiting for calendar to load...")
        time.sleep(8)
        
        # Outlook Calendar events usually have specific roles or test-ids
        # We'll look for elements with role="button" inside the grid, or use aria-label
        # This is tricky without inspecting the specific version of Outlook.
        
        # Heuristic: Grab text from the day view container
        # Note: This might be messy.
        
        # Better: Look for elements with "event" in class name or specific known attributes?
        # Let's try to just dump the visible text of the "main" calendar area if possible.
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Naive extraction - just returning a placeholder for now as scraping exact events is complex
        # without precise selectors.
        
        events.append("Calendar access successful. Parsing specific events requires precise selectors.")
        
        return events

    except Exception as e:
        print(f"Error checking calendar: {e}")
        return [f"Error: {str(e)}"]
