import asyncio
from src.crawler.naver_advanced import AdvancedNaverCrawler


class NaverCrawler:
    """
    Lightweight wrapper that delegates to the AdvancedNaverCrawler.
    Maintained for backward compatibility with existing imports.
    """

    def __init__(self, output_dir="data/raw/naver"):
        self.output_dir = output_dir
        self._advanced = AdvancedNaverCrawler()

    async def search_blog(self, keyword: str, max_posts: int = 10):
        return await self._advanced.search_blog(keyword, max_posts=max_posts)

    async def search_cafe(self, keyword: str, max_posts: int = 10):
        return await self._advanced.search_cafe(keyword, max_posts=max_posts)


if __name__ == "__main__":
    crawler = NaverCrawler(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/naver")
    asyncio.run(crawler.search_blog("미국 S&P500 ETF"))
