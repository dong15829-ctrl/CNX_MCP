import asyncio
from src.crawler.youtube_crawler import YouTubeCrawler

async def main():
    crawler = YouTubeCrawler()
    await crawler.search_and_crawl('OpenAI', max_videos=1, collect_comments=False)

if __name__ == '__main__':
    asyncio.run(main())
