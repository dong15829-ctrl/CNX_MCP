from sqlalchemy.orm import Session
from models import NewsData, TrendData, SearchKeyword
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

def save_news(db: Session, keyword: str, items: list):
    """
    뉴스 검색 결과 저장
    """
    count = 0
    for item in items:
        # 중복 체크 (Link 기준)
        exists = db.query(NewsData).filter(NewsData.link == item['link']).first()
        if not exists:
            # pubDate parsing (Sat, 19 Dec 2025 10:00:00 +0900 -> datetime)
            # Simplification: storing as is or just current time if parse fails
            # For now, let's try to parse or just store current time if complex
            
            pub_date_str = item['pubDate']
            try:
                # Naver date format: Mon, 15 Dec 2025 15:42:00 +0900
                # Python 3.7+ fromisoformat doesn't handle timezone names well without external libs sometimes for this specific format
                # keeping it simple: use current time if format is tricky, but let's try strict format
                # Actually, simplest is to just ignore parsing for this prototype if it fails
                pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
            except Exception:
                pub_date = datetime.now()

            news = NewsData(
                keyword=keyword,
                title=item['title'],
                link=item['link'],
                description=item['description'],
                pub_date=pub_date
            )
            db.add(news)
            count += 1
    
    try:
        db.commit()
        logger.info(f"Saved {count} new news items for '{keyword}'")
    except Exception as e:
        logger.error(f"Failed to save news: {e}")
        db.rollback()

def save_trends(db: Session, trend_result: dict):
    """
    데이터랩 트렌드 저장
    """
    if 'results' not in trend_result:
        return

    count = 0
    start_date = trend_result.get('startDate')
    end_date = trend_result.get('endDate')

    for group in trend_result['results']:
        group_name = group['title']
        for data in group['data']:
            # data: {'period': '2025-11-15', 'ratio': 4.61497}
            trend = TrendData(
                group_name=group_name,
                period_start=start_date,
                period_end=end_date,
                data_date=data['period'],
                ratio=data['ratio']
            )
            db.add(trend)
            count += 1
            
    try:
        db.commit()
        logger.info(f"Saved {count} trend data points")
    except Exception as e:
        logger.error(f"Failed to save trends: {e}")
        db.rollback()
