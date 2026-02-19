import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_driver(headless=False):
    chrome_options = Options()
    
    # Load user data directory
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR", "./chrome_profile")
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    
    # Binary Location Logic
    binary_location = os.getenv("CHROME_BINARY_LOCATION")
    if not binary_location:
         possible_paths = [
             "/usr/bin/google-chrome",
             "/usr/bin/chromium-browser",
             "/usr/bin/chromium", 
             "/snap/bin/chromium",
             "/snap/bin/chromium-browser"
         ]
         for path in possible_paths:
             if os.path.exists(path):
                 binary_location = path
                 break
    
    if binary_location:
        print(f"Using Chrome Binary at: {binary_location}")
        chrome_options.binary_location = binary_location

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    
    if headless:
        chrome_options.add_argument("--headless=new")
        
    print(f"Initializing Chrome Driver (Headless: {headless})...")
    # REMOVED: webdriver_manager. Using Selenium's built-in manager.
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver
