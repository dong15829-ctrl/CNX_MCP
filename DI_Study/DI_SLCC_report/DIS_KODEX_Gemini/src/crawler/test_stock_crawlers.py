"""
Test script for stock community crawlers
Tests: DC Inside, Miraeasset, Ppomppu, FMKorea, Stock Discussion
"""
import asyncio
from stock_community_crawlers import (
    DCInsideCrawler, 
    MiraeassetCrawler, 
    JulineCrawler,
    FMKoreaCrawler,
    StockDiscussionCrawler
)


async def main():
    print("=" * 80)
    print("🚀 Stock Community Crawlers Test")
    print("=" * 80)
    print()
    
    test_keyword = "미국 ETF"
    
    # Test 1: DC Inside
    print("\n" + "=" * 80)
    print("📰 TEST 1: DC Inside Stock Gallery")
    print("=" * 80)
    try:
        dc = DCInsideCrawler()
        results = await dc.crawl_gallery(keyword=test_keyword, max_posts=10)
        print(f"\n✅ DC Inside Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ DC Inside Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(3)
    
    # Test 2: Miraeasset
    print("\n" + "=" * 80)
    print("💰 TEST 2: Miraeasset ETF Information")
    print("=" * 80)
    try:
        miraeasset = MiraeassetCrawler()
        results = await miraeasset.crawl_etf_info(keyword="S&P500", max_items=10)
        print(f"\n✅ Miraeasset Test Complete: {len(results)} ETFs collected")
    except Exception as e:
        print(f"\n❌ Miraeasset Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(3)
    
    # Test 3: Ppomppu (주린이 커뮤니티)
    print("\n" + "=" * 80)
    print("💬 TEST 3: Ppomppu Stock Board (주린이)")
    print("=" * 80)
    try:
        juline = JulineCrawler()
        results = await juline.crawl_ppomppu(keyword=test_keyword, max_posts=10)
        print(f"\n✅ Ppomppu Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ Ppomppu Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: FMKorea
    print("\n" + "=" * 80)
    print("🎮 TEST 4: FMKorea Stock Board")
    print("=" * 80)
    try:
        fmkorea = FMKoreaCrawler()
        results = await fmkorea.crawl_stock_board(keyword=test_keyword, max_posts=10)
        print(f"\n✅ FMKorea Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ FMKorea Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(3)
    
    # Test 5: Stock Discussion (종토방)
    print("\n" + "=" * 80)
    print("📈 TEST 5: Stock Discussion Board (종토방)")
    print("=" * 80)
    try:
        stock_disc = StockDiscussionCrawler()
        # Test with Samsung Electronics (005930)
        results = await stock_disc.crawl_stock_discussion(stock_code="005930", max_posts=10)
        print(f"\n✅ Stock Discussion Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ Stock Discussion Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✓ All stock community crawler tests completed!")
    print(f"→ Check data/raw/dcinside/ for DC Inside results")
    print(f"→ Check data/raw/miraeasset/ for Miraeasset results")
    print(f"→ Check data/raw/ppomppu/ for Ppomppu results")
    print(f"→ Check data/raw/fmkorea/ for FMKorea results")
    print(f"→ Check data/raw/stock_discussion/ for Stock Discussion results")
    print(f"→ Check debug_*.html files for debugging")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
