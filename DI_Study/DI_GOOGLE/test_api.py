from googleapiclient.discovery import build
import auth

# --- CONFIGURATION ---
# API Service Name (e.g., 'drive', 'sheets', 'analytics')
API_SERVICE_NAME = 'drive'
# API Version (e.g., 'v3', 'v4')
API_VERSION = 'v3'
# Scopes (Modify based on the API you are using)
# For Drive Read-Only: ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def main():
    print(f"--- Starting Google {API_SERVICE_NAME.upper()} API Test ---")

    # 1. Authenticate
    # Try Service Account first
    print("Attempting Service Account Authentication...")
    creds = auth.get_service_account_credentials(SCOPES)
    
    if not creds:
        print("Service Account failed or not found. You might need to check 'credentials.json'.")
        return

    # 2. Build Service
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        print("Successfully built service object.")
    except Exception as e:
        print(f"[ERROR] Failed to build service: {e}")
        return

    # 3. Make a Test Call
    try:
        print("run drive.files.list ...")
        # Example for Drive API: List first 10 files
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found (or access denied/empty drive).')
        else:
            print('Files:')
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))
        
        print("\n[SUCCESS] API Call Completed Successfully!")
        
    except Exception as e:
        print(f"[ERROR] API Call Failed: {e}")
        print("Common causes: API not enabled in Console, wrong scope, or permission issues.")

if __name__ == '__main__':
    main()
