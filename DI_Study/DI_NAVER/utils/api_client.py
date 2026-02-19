import requests
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class NaverApiClient:
    def __init__(self):
        self.client_id = Config.NAVER_CLIENT_ID
        self.client_secret = Config.NAVER_CLIENT_SECRET
        self._validate_credentials()

    def _validate_credentials(self):
        if not self.client_id or not self.client_secret:
            logger.error("API Credentials missing!")
            raise ValueError("API Credentials missing. Please check .env file.")

    def get_headers(self):
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

    def get(self, url, params=None):
        headers = self.get_headers()
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request Failed: {str(e)}")
            raise

    def post(self, url, data=None):
        headers = self.get_headers()
        try:
            response = requests.post(url, headers=headers, data=data) # data for form-urlencoded or json= for json
            # Papago often uses data, Datalab uses json. Handle nuance later or make generic.
            # Allowing caller to handle encoding if passing raw data, or we add a json param.
            # For now, simplistic.
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request Failed: {str(e)}")
            raise
