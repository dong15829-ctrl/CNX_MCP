import asyncio
from playwright.async_api import async_playwright
from src.crawler.utils import get_stealth_context

async def test_youtube_search():
    """Test YouTube search to see what's happening"""
    async with async_playwright() as p:
        context, browser = await get_stealth_context(p, headless=True)
        page = await context.new_page()
        
        keyword = "미국 S&P500 ETF"
        print(f"Searching for: {keyword}")
        
        try:
            await page.goto(f"https://www.youtube.com/results?search_query={keyword}", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # Save debug HTML
            with open("/home/ubuntu/DI/DIS_Kodex1/debug_youtube_search.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            print("✓ Saved debug HTML")
            
            # Try to find video elements
            video_elements = await page.locator("ytd-video-renderer").all()
            print(f"Found {len(video_elements)} video elements with 'ytd-video-renderer'")
            
            # Try alternative selectors
            alt_selectors = [
                "ytd-video-renderer",
                "ytd-rich-item-renderer",
                "div#contents ytd-video-renderer",
                "ytd-item-section-renderer ytd-video-renderer"
            ]
            
            for selector in alt_selectors:
                elements = await page.locator(selector).all()
                print(f"  - '{selector}': {len(elements)} elements")
            
            # Check page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check if blocked
            content = await page.content()
            if "captcha" in content.lower() or "blocked" in content.lower():
                print("⚠️  Possible CAPTCHA or block detected")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_youtube_search())
