import asyncio
import json
import random
from datetime import datetime
from urllib.parse import quote
from playwright.async_api import async_playwright
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement, human_typing


class AdvancedNaverCrawler:
    """
    Advanced Naver crawler with comprehensive anti-detection measures.
    Supports: Blog, Cafe, and Stock Cafe crawling.
    """
    
    def __init__(self):
        self.base_url = "https://search.naver.com"
        
    async def search_blog(self, keyword: str, max_posts: int = 10):
        """
        Search Naver Blog with advanced stealth techniques.
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Direct navigation to blog search results (more reliable)
                encoded_keyword = quote(keyword)
                search_url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}"
                
                print(f"[1/3] Navigating to blog search: {keyword}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                await random_mouse_movement(page)
                
                # Scroll to load dynamic content
                print(f"[2/3] Scrolling to load content...")
                for i in range(5):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 300})")
                    await human_like_delay(500, 1000)
                
                # Save debug HTML
                with open("debug_naver_advanced.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Step 3: Extract blog posts
                print(f"[3/3] Extracting blog posts...")
                results = []
                
                # Try multiple selector strategies
                selectors_to_try = [
                    ".lst_total .bx",  # Total wrap
                    ".api_subject_bx .total_wrap",  # API subject box
                    ".sh_blog_top",  # Blog top
                    "li.bx:not(.lineup)",  # Box items (excluding lineup)
                    ".view_wrap",  # View wrap
                ]
                
                all_elements = []
                for selector in selectors_to_try:
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
                
                for elem in unique_elements[:max_posts * 3]:  # Process more to filter
                    if len(results) >= max_posts:
                        break
                    
                    try:
                        # Try to find title link
                        title_link = None
                        title_text = None
                        
                        # Multiple title selectors
                        title_selectors = [
                            "a.title_link",
                            "a.api_txt_lines",
                            ".total_tit",
                            "a.sh_blog_title",
                            ".title a"
                        ]
                        
                        for ts in title_selectors:
                            try:
                                title_elem = elem.locator(ts).first
                                if await title_elem.count() > 0:
                                    title_text = await title_elem.text_content()
                                    title_link = await title_elem.get_attribute("href")
                                    if title_text and title_link:
                                        break
                            except:
                                continue
                        
                        if not title_link or not title_text:
                            continue
                        
                        # Filter for blog links only
                        if "blog.naver.com" not in title_link and "blog.me" not in title_link:
                            continue
                        
                        # Extract date
                        date = "Unknown"
                        date_selectors = [".sub_time", ".sub", ".date", "span.sub"]
                        for ds in date_selectors:
                            try:
                                date_elem = elem.locator(ds).first
                                if await date_elem.count() > 0:
                                    date = await date_elem.text_content()
                                    break
                            except:
                                continue
                        
                        post_data = {
                            "keyword": keyword,
                            "title": title_text.strip(),
                            "url": title_link if title_link.startswith("http") else f"https://search.naver.com{title_link}",
                            "date": date.strip(),
                            "source": "blog",
                            "crawled_at": datetime.now().isoformat()
                        }
                        
                        results.append(post_data)
                        print(f"   ✓ [{len(results)}] {title_text[:50]}...")
                        
                    except Exception as e:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/raw/naver/search_rank/{timestamp}_{keyword}_blog.json"
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} blog posts to {filename}")
                
                await human_like_delay(1000, 2000)
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def search_cafe(self, keyword: str, max_posts: int = 10):
        """
        Search Naver Cafe with advanced stealth techniques.
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                print(f"[1/4] Visiting Naver homepage...")
                await page.goto("https://www.naver.com", wait_until="domcontentloaded")
                await human_like_delay(1000, 2000)
                
                print(f"[2/4] Searching for: {keyword}")
                await human_typing(page, "#query", keyword)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle", timeout=15000)
                await human_like_delay(1500, 2500)
                
                # Click Cafe tab
                print(f"[3/4] Clicking Cafe tab...")
                try:
                    cafe_selectors = [
                        'a[href*="where=article"]',
                        'a.tab:has-text("카페")',
                        '.lnb a:has-text("카페")'
                    ]
                    
                    for selector in cafe_selectors:
                        try:
                            await page.click(selector, timeout=3000)
                            print(f"   ✓ Clicked Cafe tab")
                            break
                        except:
                            continue
                    
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    await human_like_delay(1500, 2500)
                except Exception as e:
                    print(f"   ⚠ Could not click Cafe tab: {e}")
                
                # Scroll
                print(f"[4/4] Extracting cafe posts...")
                for i in range(5):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 300})")
                    await human_like_delay(500, 1000)
                
                results = []
                
                # Extract cafe posts
                selectors_to_try = [
                    ".lst_total .bx",
                    ".api_subject_bx .total_wrap",
                    "li.bx:not(.lineup)",
                ]
                
                all_elements = []
                for selector in selectors_to_try:
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            all_elements.extend(elements)
                    except:
                        continue
                
                for elem in all_elements[:max_posts * 3]:
                    if len(results) >= max_posts:
                        break
                    
                    try:
                        # Find title
                        title_link = None
                        title_text = None
                        
                        title_selectors = ["a.title_link", "a.api_txt_lines", ".total_tit"]
                        for ts in title_selectors:
                            try:
                                title_elem = elem.locator(ts).first
                                if await title_elem.count() > 0:
                                    title_text = await title_elem.text_content()
                                    title_link = await title_elem.get_attribute("href")
                                    if title_text and title_link:
                                        break
                            except:
                                continue
                        
                        if not title_link or not title_text:
                            continue
                        
                        # Filter for cafe links
                        if "cafe.naver.com" not in title_link:
                            continue
                        
                        # Extract cafe name
                        cafe_name = "Unknown Cafe"
                        cafe_selectors = [".name", ".txt_name", "a.name"]
                        for cs in cafe_selectors:
                            try:
                                cafe_elem = elem.locator(cs).first
                                if await cafe_elem.count() > 0:
                                    cafe_name = await cafe_elem.text_content()
                                    break
                            except:
                                continue
                        
                        post_data = {
                            "keyword": keyword,
                            "title": title_text.strip(),
                            "url": title_link if title_link.startswith("http") else f"https://search.naver.com{title_link}",
                            "cafe_name": cafe_name.strip(),
                            "source": "cafe",
                            "crawled_at": datetime.now().isoformat()
                        }
                        
                        results.append(post_data)
                        print(f"   ✓ [{len(results)}] {title_text[:50]}...")
                        
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/raw/naver/search_rank/{timestamp}_{keyword}_cafe.json"
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} cafe posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def search_stock_cafe(self, stock_keyword: str, max_posts: int = 20):
        """
        Search stock-related cafes (주식 카페) for specific keywords.
        Targets popular stock cafes like "주식투자 모임", "개미의 반란" etc.
        """
        # Popular stock cafe names
        stock_cafes = [
            "주식투자 모임",
            "개미의 반란",
            "주식 단타방",
            "ETF 투자 모임"
        ]
        
        all_results = []
        
        for cafe_name in stock_cafes:
            search_query = f"{cafe_name} {stock_keyword}"
            print(f"\n🔍 Searching in cafe: {cafe_name}")
            print(f"   Query: {search_query}")
            
            try:
                results = await self.search_cafe(search_query, max_posts=max_posts // len(stock_cafes))
                all_results.extend(results)
                
                # Add delay between cafe searches
                await asyncio.sleep(random.uniform(3, 6))
                
            except Exception as e:
                print(f"   ❌ Error searching {cafe_name}: {e}")
                continue
        
        # Save combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/raw/naver/search_rank/{timestamp}_{stock_keyword}_stock_cafe.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Total: Saved {len(all_results)} stock cafe posts to {filename}")
        
        return all_results
