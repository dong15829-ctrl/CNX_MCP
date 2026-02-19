import os
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# Define path to credentials
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def get_service_account_credentials(scopes):
    """
    Authenticates using a Service Account JSON key.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[ERROR] Service Account key not found at: {os.path.abspath(CREDENTIALS_FILE)}")
        print("Please upload your service account JSON key and rename it to 'credentials.json'.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=scopes)
        return creds
    except Exception as e:
        print(f"[ERROR] Failed to load service account credentials: {e}")
        return None

def get_oauth_credentials(scopes):
    """
    Authenticates using OAuth 2.0 (User Login).
    Useful if running locally or if you can perform the browser dance.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                 print(f"[ERROR] OAuth Client Secret not found at: {os.path.abspath(CREDENTIALS_FILE)}")
                 return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, scopes)
            # generic approach used for remote environments
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds
