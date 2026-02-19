from utils.api_client import NaverApiClient
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class NaverPapago(NaverApiClient):
    def __init__(self):
        super().__init__()
        self.base_url = Config.PAPAGO_API_URL

    def translate(self, text, source='ko', target='en'):
        """
        Papago NMT 번역
        :param text: 번역할 텍스트
        :param source: 원본 언어 코드 (ko: 한국어, en: 영어, ja: 일본어 등)
        :param target: 목적 언어 코드
        """
        data = {
            "source": source,
            "target": target,
            "text": text
        }
        logger.info(f"Translating text: {text[:20]}... ({source} -> {target})")
        
        try:
            # Papago는 POST 요청을 사용하며 form-urlencoded 방식을 주로 사용하지만,
            # requests의 data parameter가 이를 처리해줍니다.
            response = self.post(self.base_url, data=data)
            return response.get('message', {}).get('result', {}).get('translatedText')
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return None
