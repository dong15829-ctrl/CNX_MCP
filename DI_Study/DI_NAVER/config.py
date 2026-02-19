import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    # API Base URLs
    SEARCH_API_URL = "https://openapi.naver.com/v1/search"
    PAPAGO_API_URL = "https://openapi.naver.com/v1/papago/n2mt"
    DATALAB_API_URL = "https://openapi.naver.com/v1/datalab/search"

    @classmethod
    def validate(cls):
        if not cls.NAVER_CLIENT_ID or not cls.NAVER_CLIENT_SECRET:
            raise ValueError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set in .env file")
