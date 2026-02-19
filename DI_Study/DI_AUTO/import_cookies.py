import json
import time
import os
from modules.browser import get_driver

def load_cookies_from_file(driver, url, cookie_file):
    if not os.path.exists(cookie_file):
        print(f"[SKIP] Cookie file not found: {cookie_file}")
        return

    print(f"Loading cookies for {url} from {cookie_file}...")
    
    # Navigate to domain first to set cookie context
    try:
        driver.get(url)
    except Exception as e:
        print(f"Warning: Could not navigate to {url} initially: {e}")

    try:
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
            
        added_count = 0
        for cookie in cookies:
            # Selenium expects matching domain. 
            # Sometimes exported cookies have dot prefixes (e.g. .shiftee.io)
            # Depending on driver version, strictness varies.
            
            # Clean up cookie fields that Selenium doesn't like
            if 'sameSite' in cookie:
                if cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite'] 
            if 'storeId' in cookie:
                del cookie['storeId']
            if 'hostOnly' in cookie:
                del cookie['hostOnly']
            if 'session' in cookie:
                del cookie['session']

            try:
                driver.add_cookie(cookie)
                added_count += 1
            except Exception as e:
                # Common error: Domain mismatch. 
                # E.g. trying to add .google.com cookie when current url is google.com/foo
                pass
                
        print(f"Successfully added {added_count} cookies.")
        
        # Refresh to apply
        driver.refresh()
        time.sleep(3)
        print(f"Refreshed page. Current URL: {driver.current_url}")
        
    except Exception as e:
        print(f"Error loading cookies: {e}")

def main():
    driver = get_driver(headless=True)
    
    try:
        # 1. Shiftee
        shiftee_url = os.getenv("SHIFTEE_URL", "https://shiftee.io")
        load_cookies_from_file(driver, shiftee_url, "shiftee_cookies.json")
        
        # Outlook removed per request
        
        print("\nCookie import finished. Run 'main.py --dry-run' to verify access.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
