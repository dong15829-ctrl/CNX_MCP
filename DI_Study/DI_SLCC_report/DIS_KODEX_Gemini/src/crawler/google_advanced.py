import asyncio
import json
import random
from datetime import datetime
from playwright.async_api import async_playwright
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement, human_typing


class AdvancedGoogleCrawler:
    """
    Advanced Google SERP crawler with comprehensive anti-detection measures.
    """
    
    def __init__(self):
        self.base_url = "https://www.google.com"
        
    async def search(self, keyword: str, max_results: int = 10):
        """
        Search Google with advanced stealth techniques to avoid CAPTCHA.
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Step 1: Visit Google homepage
                print(f"[1/5] Visiting Google homepage...")
                await page.goto("https://www.google.com", wait_until="domcontentloaded")
                await human_like_delay(2000, 3000)
                await random_mouse_movement(page)
                
                # Step 2: Accept cookies if prompted
                print(f"[2/5] Handling cookie consent...")
                try:
                    accept_selectors = [
                        'button:has-text("Accept all")',
                        'button:has-text("I agree")',
                        'button:has-text("동의")',
                        '#L2AGLb',
                    ]
                    
                    for selector in accept_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            print(f"   ✓ Accepted cookies")
                            await human_like_delay(500, 1000)
                            break
                        except:
                            continue
                except:
                    print(f"   → No cookie consent needed")
                
                # Step 3: Type search query
                print(f"[3/5] Searching for: {keyword}")
                
                search_selectors = [
                    'textarea[name="q"]',
                    'input[name="q"]',
                    'textarea[title="Search"]',
                ]
                
                search_box = None
                for selector in search_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            search_box = selector
                            break
                    except:
                        continue
                
                if not search_box:
                    raise Exception("Could not find Google search box")
                
                await human_typing(page, search_box, keyword)
                await human_like_delay(500, 1000)
                
                # Step 4: Press Enter
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=20000)
                await human_like_delay(2000, 3000)
                
                # Save debug HTML
                with open("debug_google_advanced.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Check for CAPTCHA
                page_content = await page.content()
                if "captcha" in page_content.lower() or "unusual traffic" in page_content.lower():
                    print(f"\n⚠️  WARNING: Google CAPTCHA detected!")
                    print(f"   → Waiting 15 seconds for manual CAPTCHA solving...")
                    await asyncio.sleep(15)
                    await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Step 5: Scroll and extract results
                print(f"[4/5] Scrolling to load results...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                    await human_like_delay(800, 1500)
                
                print(f"[5/5] Extracting search results...")
                results = []
                
                # Google search result selectors
                result_selectors = [
                    "div.g",
                    "div[data-sokoban-container]",
                    ".tF2Cxc",
                ]
                
                all_elements = []
                for selector in result_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            print(f"   ✓ Found {len(elements)} elements with: {selector}")
                            all_elements.extend(elements)
                    except:
                        continue
                
                # Remove duplicates
                unique_elements = []
                seen_texts = set()
                for elem in all_elements:
                    try:
                        text = await elem.text_content()
                        if text and text not in seen_texts:
                            unique_elements.append(elem)
                            seen_texts.add(text)
                    except:
                        continue
                
                print(f"   → Processing {len(unique_elements)} unique elements...")
                
                for elem in unique_elements[:max_results * 2]:
                    if len(results) >= max_results:
                        break
                    
                    try:
                        # Extract title
                        title = None
                        title_selectors = ["h3", ".LC20lb", ".DKV0Md"]
                        for ts in title_selectors:
                            try:
                                title_elem = elem.locator(ts).first
                                if await title_elem.count() > 0:
                                    title = await title_elem.text_content()
                                    if title:
                                        break
                            except:
                                continue
                        
                        if not title:
                            continue
                        
                        # Extract URL
                        url = None
                        try:
                            link_elem = elem.locator("a").first
                            if await link_elem.count() > 0:
                                url = await link_elem.get_attribute("href")
                        except:
                            pass
                        
                        if not url or not url.startswith("http"):
                            continue
                        
                        # Extract snippet
                        snippet = ""
                        snippet_selectors = [".VwiC3b", ".lEBKkf", "div[data-sncf]"]
                        for ss in snippet_selectors:
                            try:
                                snippet_elem = elem.locator(ss).first
                                if await snippet_elem.count() > 0:
                                    snippet = await snippet_elem.text_content()
                                    if snippet:
                                        break
                            except:
                                continue
                        
                        result_data = {
                            "keyword": keyword,
                            "title": title.strip(),
                            "url": url,
                            "snippet": snippet.strip() if snippet else "",
                            "source": "google",
                            "crawled_at": datetime.now().isoformat()
                        }
                        
                        results.append(result_data)
                        print(f"   ✓ [{len(results)}] {title[:60]}...")
                        
                    except Exception as e:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/raw/google/{timestamp}_{keyword}_serp.json"
                
                os.makedirs("data/raw/google", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Google results to {filename}")
                
                await human_like_delay(1000, 2000)
                
            finally:
                await context.close()
                await browser.close()
        
        return results
