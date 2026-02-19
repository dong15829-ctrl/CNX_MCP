"""
Test script for advanced crawlers with anti-detection measures.
Tests: Naver Blog, Naver Cafe, Stock Cafe, and Google Search.
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from naver_advanced import AdvancedNaverCrawler
from google_advanced import AdvancedGoogleCrawler


async def main():
    print("=" * 80)
    print("🚀 KODEX Marketing Intelligence - Advanced Crawler Test")
    print("=" * 80)
    print()
    
    # Test keyword
    test_keyword = "미국 S&P500 ETF"
    
    # Initialize crawlers
    naver = AdvancedNaverCrawler()
    google = AdvancedGoogleCrawler()
    
    # Test 1: Naver Blog
    print("\n" + "=" * 80)
    print("📝 TEST 1: Naver Blog Crawler (Advanced Stealth)")
    print("=" * 80)
    try:
        blog_results = await naver.search_blog(test_keyword, max_posts=10)
        print(f"\n✅ Blog Test Complete: {len(blog_results)} posts collected")
    except Exception as e:
        print(f"\n❌ Blog Test Failed: {e}")
    
    # Delay between tests
    print("\n⏳ Waiting 5 seconds before next test...")
    await asyncio.sleep(5)
    
    # Test 2: Naver Cafe
    print("\n" + "=" * 80)
    print("☕ TEST 2: Naver Cafe Crawler (Advanced Stealth)")
    print("=" * 80)
    try:
        cafe_results = await naver.search_cafe(test_keyword, max_posts=10)
        print(f"\n✅ Cafe Test Complete: {len(cafe_results)} posts collected")
    except Exception as e:
        print(f"\n❌ Cafe Test Failed: {e}")
    
    # Delay between tests
    print("\n⏳ Waiting 5 seconds before next test...")
    await asyncio.sleep(5)
    
    # Test 3: Stock Cafe
    print("\n" + "=" * 80)
    print("📈 TEST 3: Stock Cafe Crawler (Advanced Stealth)")
    print("=" * 80)
    try:
        stock_results = await naver.search_stock_cafe("KODEX 미국S&P500", max_posts=20)
        print(f"\n✅ Stock Cafe Test Complete: {len(stock_results)} posts collected")
    except Exception as e:
        print(f"\n❌ Stock Cafe Test Failed: {e}")
    
    # Delay before Google test
    print("\n⏳ Waiting 10 seconds before Google test...")
    await asyncio.sleep(10)
    
    # Test 4: Google Search
    print("\n" + "=" * 80)
    print("🔍 TEST 4: Google Search Crawler (Advanced Stealth)")
    print("=" * 80)
    print("⚠️  Note: If CAPTCHA appears, you have 15 seconds to solve it manually")
    try:
        google_results = await google.search(test_keyword, max_results=10)
        print(f"\n✅ Google Test Complete: {len(google_results)} results collected")
    except Exception as e:
        print(f"\n❌ Google Test Failed: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✓ All tests completed!")
    print(f"→ Check data/raw/naver/search_rank/ for Naver results")
    print(f"→ Check data/raw/google/ for Google results")
    print(f"→ Check debug_*.html files for debugging")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
