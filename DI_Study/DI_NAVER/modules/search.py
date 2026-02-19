from utils.api_client import NaverApiClient
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class NaverSearch(NaverApiClient):
    def __init__(self):
        super().__init__()
        self.base_url = Config.SEARCH_API_URL

    def search_news(self, query, display=10, start=1, sort='date'):
        """
        뉴스 검색
        :param query: 검색어
        :param display: 출력 건수 (10~100)
        :param start: 시작 위치 (1~1000)
        :param sort: 정렬 (sim: 유사도순, date: 날짜순)
        """
        url = f"{self.base_url}/news.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        logger.info(f"Searching news for: {query}")
        return self.get(url, params=params)

    def search_blog(self, query, display=10, start=1, sort='sim'):
        """
        블로그 검색
        """
        url = f"{self.base_url}/blog.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        logger.info(f"Searching blog for: {query}")
        return self.get(url, params=params)

    def search_shop(self, query, display=10, start=1, sort='sim'):
        """
        쇼핑 검색 (sim, date, asc, dsc)
        """
        url = f"{self.base_url}/shop.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        logger.info(f"Searching shop for: {query}")
        return self.get(url, params=params)
