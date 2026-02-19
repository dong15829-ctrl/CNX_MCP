import asyncio
import json
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright
from src.crawler.utils import get_stealth_context

from urllib.parse import quote

class NaverCrawler:
    def __init__(self, output_dir="data/raw/naver"):
        self.output_dir = output_dir
        os.makedirs(f"{self.output_dir}/search_rank", exist_ok=True)
        os.makedirs(f"{self.output_dir}/blog_posts", exist_ok=True)

    async def search_blog(self, keyword: str, max_posts: int = 10):
        """
        Searches for a keyword on Naver Blog (Mobile) and crawls post content.
        """
        async with async_playwright() as p:
            # Use mobile viewport
            context, browser = await get_stealth_context(p, headless=True)
            page = await context.new_page()
            await page.set_viewport_size({"width": 375, "height": 812})
            
            # Naver Mobile Search (Blog)
            encoded_keyword = quote(keyword)
            url = f"https://m.search.naver.com/search.naver?where=blog&query={encoded_keyword}"
            print(f"Searching Naver Blog (Mobile): {keyword}")
            
            await page.goto(url, wait_until="networkidle")
            
            # Scroll
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(1, 2))
            
            # Debug: Save mobile HTML
            with open("debug_naver_mobile.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            print("Saved mobile HTML to debug_naver_mobile.html")
            
            # Wait for at least one title to be visible
            try:
                await page.wait_for_selector(".total_tit, .api_txt_lines", timeout=5000)
            except:
                print("No titles found after wait.")

            # Extract post links (Mobile)
            potential_elements = await page.locator(".bx").all()
            
            results = []
            print(f"Found {len(potential_elements)} potential elements")
            
            for i, post in enumerate(potential_elements):
                if len(results) >= max_posts:
                    break
                
                try:
                    # Skip "lineup" (Sort options)
                    class_attr = await post.get_attribute("class")
                    if class_attr and "lineup" in class_attr:
                        # print("Skipping lineup element")
                        continue

                    # Title
                    title_el = post.locator(".total_tit, .api_txt_lines")
                    if not await title_el.count():
                        # print("No title element found")
                        continue

                    title = await title_el.first.text_content()
                    
                    # Link
                    link_el = post.locator("a.total_tit, a.api_txt_lines")
                    if await link_el.count():
                        link = await link_el.first.get_attribute("href")
                    else:
                        link_el = post.locator("a")
                        link = await link_el.first.get_attribute("href") if await link_el.count() else None
                    
                    if not link:
                        continue
                        
                    # Date
                    date_el = post.locator(".sub_time, .sub_txt")
                    date = await date_el.first.text_content() if await date_el.count() else "Unknown"
                    
                    post_data = {
                        "keyword": keyword,
                        "title": title.strip(),
                        "url": link,
                        "date": date.strip(),
                        "source": "blog",
                        "crawled_at": datetime.now().isoformat()
                    }
                    
                    results.append(post_data)
                    print(f"Found Blog: {title.strip()}")
                    
                except Exception as e:
                    # print(f"Error: {e}")
                    continue
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/search_rank/{timestamp}_{keyword}_blog.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
                
            print(f"Saved {len(results)} blog posts to {filename}")
            
            await browser.close()
            return results

    async def search_cafe(self, keyword: str, max_posts: int = 10):
        """
        Searches for a keyword on Naver Cafe (Mobile) and crawls post content.
        """
        async with async_playwright() as p:
            context, browser = await get_stealth_context(p, headless=True)
            page = await context.new_page()
            await page.set_viewport_size({"width": 375, "height": 812})
            
            # Naver Mobile Search (Cafe)
            encoded_keyword = quote(keyword)
            url = f"https://m.search.naver.com/search.naver?where=article&query={encoded_keyword}"
            print(f"Searching Naver Cafe (Mobile): {keyword}")
            
            await page.goto(url, wait_until="networkidle")
            
            # Scroll
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(1, 2))
            
            # Extract post links
            potential_elements = await page.locator(".bx").all()
            
            results = []
            for i, post in enumerate(potential_elements):
                if len(results) >= max_posts:
                    break
                
                try:
                    title_el = post.locator(".total_tit, .api_txt_lines")
                    if not await title_el.count():
                        continue

                    title = await title_el.first.text_content()
                    
                    link_el = post.locator("a.total_tit, a.api_txt_lines")
                    if await link_el.count():
                        link = await link_el.first.get_attribute("href")
                    else:
                        link_el = post.locator("a")
                        link = await link_el.first.get_attribute("href") if await link_el.count() else None
                    
                    if not link:
                        continue
                        
                    # Filter for cafe links
                    if "cafe.naver.com" not in link:
                        continue
                    
                    # Cafe Name
                    cafe_el = post.locator(".name, .txt_name")
                    cafe_name = await cafe_el.first.text_content() if await cafe_el.count() else "Unknown Cafe"

                    post_data = {
                        "keyword": keyword,
                        "title": title.strip(),
                        "url": link,
                        "cafe_name": cafe_name.strip(),
                        "source": "cafe",
                        "crawled_at": datetime.now().isoformat()
                    }
                    
                    results.append(post_data)
                    print(f"Found Cafe Post: {title.strip()}")
                    
                except Exception as e:
                    continue
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/search_rank/{timestamp}_{keyword}_cafe.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
                
            print(f"Saved {len(results)} cafe posts to {filename}")
            
            await browser.close()
            return results

if __name__ == "__main__":
    crawler = NaverCrawler(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/naver")
    asyncio.run(crawler.search_blog("미국 S&P500 ETF"))
