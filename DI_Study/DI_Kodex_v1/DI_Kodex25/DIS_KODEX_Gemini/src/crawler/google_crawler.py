import asyncio
import json
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright
from src.crawler.utils import get_stealth_context
from urllib.parse import quote

class GoogleCrawler:
    def __init__(self, output_dir="data/raw/google"):
        self.output_dir = output_dir
        os.makedirs(f"{self.output_dir}/serp", exist_ok=True)

    async def search(self, keyword: str, max_results: int = 10):
        """
        Searches for a keyword on Google and crawls SERP results.
        """
        async with async_playwright() as p:
            context, browser = await get_stealth_context(p, headless=True)
            page = await context.new_page()
            
            encoded_keyword = quote(keyword)
            url = f"https://www.google.com/search?q={encoded_keyword}"
            print(f"Searching Google: {keyword}")
            await page.goto(url, wait_until="domcontentloaded")
            
            # Human-like behavior
            await page.mouse.move(100, 100)
            await asyncio.sleep(random.uniform(1, 3))
            await page.mouse.move(200, 200)
            
            # Debug: Save HTML
            with open("debug_google.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            
            # Extract results
            # Google SERP structure: div.g
            results = []
            result_elements = await page.locator("div.g").all()
            
            for i, res in enumerate(result_elements):
                if i >= max_results:
                    break
                
                try:
                    title_el = res.locator("h3")
                    link_el = res.locator("a").first
                    snippet_el = res.locator("div.VwiC3b") # Common snippet class, might change
                    
                    if not await title_el.count():
                        continue
                        
                    title = await title_el.text_content()
                    link = await link_el.get_attribute("href")
                    snippet = await snippet_el.text_content() if await snippet_el.count() else ""
                    
                    data = {
                        "keyword": keyword,
                        "title": title.strip(),
                        "url": link,
                        "snippet": snippet.strip(),
                        "rank": i + 1,
                        "crawled_at": datetime.now().isoformat()
                    }
                    
                    results.append(data)
                    print(f"Found Google Result: {title.strip()}")
                    
                except Exception as e:
                    # print(f"Error parsing google result: {e}")
                    continue
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/serp/{timestamp}_{keyword}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
                
            print(f"Saved {len(results)} Google results to {filename}")
            
            await browser.close()
            return results

if __name__ == "__main__":
    crawler = GoogleCrawler(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/google")
    asyncio.run(crawler.search("미국 S&P500 ETF 추천"))
