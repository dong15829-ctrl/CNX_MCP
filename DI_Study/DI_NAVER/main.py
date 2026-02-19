import sys
import json
from modules.search import NaverSearch
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting Naver API Pipeline...")
    
    # Init DB
    from database import init_db
    init_db()
    
    try:
        # Search Module Test
        search_client = NaverSearch()
        
        # Keyword
        keyword = "인공지능"
        if len(sys.argv) > 1:
            keyword = sys.argv[1]
            
        logger.info(f"Testing Search API with keyword: {keyword}")
        
        # 1. Search News
        news_result = search_client.search_news(keyword, display=3)
        print("\n[Latest News]")
        if 'items' in news_result:
            for item in news_result['items']:
                print(f"- {item['title']} ({item['pubDate']})")
                print(f"  Link: {item['link']}")
            
            # DB Save
            from database import SessionLocal
            from modules.store import save_news
            db = SessionLocal()
            try:
                save_news(db, keyword, news_result['items'])
            finally:
                db.close()
        
        # 2. Search Blog
        blog_result = search_client.search_blog(keyword, display=2)
        print("\n[Blog Posts]")
        if 'items' in blog_result:
            for item in blog_result['items']:
                print(f"- {item['title']}")
                print(f"  Link: {item['link']}")

        # 3. Datalab Trend Test
        from modules.datalab import NaverDatalab
        datalab_client = NaverDatalab()
        
        print("\n[Datalab Search Trend]")
        import datetime
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        keyword_groups = [
            {"groupName": keyword, "keywords": [keyword]},
            {"groupName": "AI", "keywords": ["AI", "Artificial Intelligence"]}
        ]
        
        try:
            trend_result = datalab_client.search_trend(start_date, end_date, "date", keyword_groups)
            if 'results' in trend_result:
                print(f"- Period: {trend_result['startDate']} ~ {trend_result['endDate']}")
                for data in trend_result['results']:
                    print(f"- Topic: {data['title']}")
                    # Showing last 3 data points
                    if data['data']:
                        print(f"  Last 3 days: {[d['ratio'] for d in data['data'][-3:]]}")
                
                # DB Save
                from modules.store import save_trends
                db = SessionLocal()
                try:
                    save_trends(db, trend_result)
                finally:
                    db.close()

        except Exception as e:
            print(f"- Datalab Error (Check if API is added in Console): {e}")

        logger.info("Pipeline test finished successfully.")

    except ValueError as ve:
        logger.error(f"Configuration Error: {ve}")
        print("\n[ERROR] 환결 설정 오류: .env 파일에 Client ID와 Secret을 설정해주세요.")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        print(f"\n[ERROR] 실행 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
