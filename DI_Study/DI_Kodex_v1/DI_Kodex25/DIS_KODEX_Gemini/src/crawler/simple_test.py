"""
Simple test to verify advanced stealth crawler works
"""
import asyncio
from naver_advanced import AdvancedNaverCrawler


async def main():
    print("Testing Naver Blog Crawler...")
    naver = AdvancedNaverCrawler()
    
    try:
        results = await naver.search_blog("미국 S&P500 ETF", max_posts=5)
        print(f"\n✅ Success! Found {len(results)} blog posts")
        
        if results:
            print("\nFirst result:")
            print(f"  Title: {results[0]['title']}")
            print(f"  URL: {results[0]['url']}")
        else:
            print("\n⚠️  No results found - check debug_naver_advanced.html")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
