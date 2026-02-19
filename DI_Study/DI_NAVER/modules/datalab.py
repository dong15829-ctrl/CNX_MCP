from utils.api_client import NaverApiClient
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class NaverDatalab(NaverApiClient):
    def __init__(self):
        super().__init__()
        self.base_url = Config.DATALAB_API_URL

    def search_trend(self, startDate, endDate, timeUnit, keywordGroups):
        """
        통합 검색어 트렌드 조회
        :param startDate: 조회 기간 시작 날짜 (YYYY-MM-DD)
        :param endDate: 조회 기간 종료 날짜 (YYYY-MM-DD)
        :param timeUnit: 구간 단위 (date, week, month)
        :param keywordGroups: 주제어와 검색어 묶음 리스트
        Example keywordGroups:
        [
            {
                "groupName": "한글",
                "keywords": ["한글", "korean"]
            },
            {
                "groupName": "영어",
                "keywords": ["영어", "english"]
            }
        ]
        """
        body = {
            "startDate": startDate,
            "endDate": endDate,
            "timeUnit": timeUnit,
            "keywordGroups": keywordGroups
        }
        
        logger.info(f"Requesting Datalab trend for: {[g['groupName'] for g in keywordGroups]}")
        
        try:
            # Datalab API는 JSON body를 요구합니다.
            headers = self.get_headers()
            headers['Content-Type'] = 'application/json'
            
            import requests # Local import to avoid circular or extra deps, though api_client has it
            response = requests.post(self.base_url, headers=headers, json=body)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Datalab request failed: {e}")
            raise
