"""
Completely new test file to avoid Python caching issues
"""
import asyncio
import json
from datetime import datetime
from urllib.parse import quote
from playwright.async_api import async_playwright
import random
import sys
import os

# Import advanced stealth
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement


async def test_naver_blog_direct():
    """Test Naver blog search with direct URL navigation"""
    keyword = "미국 S&P500 ETF"
    
    async with async_playwright() as p:
        context, browser = await get_advanced_stealth_context(p, headless=True)
        page = await context.new_page()
        
        try:
            # Direct navigation
            encoded_keyword = quote(keyword)
            search_url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}"
            
            print(f"[1/3] Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await human_like_delay(2000, 3000)
            
            # Scroll
            print(f"[2/3] Scrolling...")
            for i in range(5):
                await page.evaluate(f"window.scrollTo(0, {(i+1) * 300})")
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Save HTML
            html_content = await page.content()
            with open("/home/ubuntu/DI/DIS_Kodex1/debug_naver_fresh.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"   ✓ Saved HTML ({len(html_content)} bytes)")
            
            # Extract
            print(f"[3/3] Extracting...")
            results = []
            
            # Try selectors
            selectors = [".lst_total .bx", "li.bx:not(.lineup)", ".view_wrap"]
            
            for selector in selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"   ✓ Found {len(elements)} elements with: {selector}")
                        
                        for elem in elements[:10]:
                            try:
                                # Get title
                                title_selectors = ["a.title_link", "a.api_txt_lines", ".total_tit"]
                                title = None
                                url = None
                                
                                for ts in title_selectors:
                                    try:
                                        title_elem = elem.locator(ts).first
                                        if await title_elem.count() > 0:
                                            title = await title_elem.text_content()
                                            url = await title_elem.get_attribute("href")
                                            if title and url and "blog.naver.com" in url:
                                                break
                                    except:
                                        continue
                                
                                if title and url:
                                    results.append({"title": title.strip(), "url": url})
                                    print(f"   ✓ [{len(results)}] {title[:50]}...")
                                    
                            except:
                                continue
                                
                        if results:
                            break
                except:
                    continue
            
            print(f"\n✅ Found {len(results)} blog posts")
            
            if results:
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/naver/search_rank/{timestamp}_{keyword}_blog_fresh.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"✅ Saved to {filename}")
            else:
                print(f"⚠️  No results - check debug_naver_fresh.html")
            
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_naver_blog_direct())
