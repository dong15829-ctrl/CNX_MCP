import sys
import os
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from src.crawler.naver_crawler import NaverCrawler
from src.crawler.google_crawler import GoogleCrawler

async def main():
    print(">>> Testing Naver Blog Crawler...")
    naver = NaverCrawler()
    await naver.search_blog("미국 S&P500 ETF", max_posts=3)
    
    print("\n>>> Testing Naver Cafe Crawler...")
    await naver.search_cafe("미국 S&P500 ETF", max_posts=3)
    
    # print("\n>>> Testing Google Crawler...")
    # google_crawler = GoogleCrawler()
    # await google_crawler.search("미국 S&P500 ETF 추천", max_results=5)

if __name__ == "__main__":
    asyncio.run(main())
