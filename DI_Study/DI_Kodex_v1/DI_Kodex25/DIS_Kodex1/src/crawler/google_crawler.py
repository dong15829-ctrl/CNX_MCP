import asyncio
import json
import os
import random
from datetime import datetime
from urllib.parse import quote

from playwright.async_api import async_playwright

from src.crawler.google_news_rss import GoogleNewsRSSCrawler
from src.crawler.utils import get_stealth_context

class GoogleCrawler:
    def __init__(self, output_dir="data/raw/google"):
        self.output_dir = output_dir
        os.makedirs(f"{self.output_dir}/serp", exist_ok=True)
        self._rss_fallback = GoogleNewsRSSCrawler()

    async def _fetch_via_rss(self, keyword: str, max_results: int) -> list[dict]:
        return await asyncio.to_thread(
            self._rss_fallback.search,
            keyword,
            max_results,
        )

    def _map_time_range(self, time_range: str | None) -> str:
        if not time_range:
            return ""
        mapping = {
            "1h": "qdr:h",
            "1d": "qdr:d",
            "1w": "qdr:w",
            "1m": "qdr:m",
            "1y": "qdr:y",
        }
        return mapping.get(time_range, "")

    async def search(self, keyword: str, max_results: int = 10, time_range: str | None = None):
        """
        Searches for a keyword on Google and crawls SERP results.
        """
        async with async_playwright() as p:
            context, browser = await get_stealth_context(p, headless=True)
            page = await context.new_page()
            try:
                encoded_keyword = quote(keyword)
                tbs_param = self._map_time_range(time_range)
                url = f"https://www.google.com/search?q={encoded_keyword}"
                if tbs_param:
                    url += f"&tbs={tbs_param}"
                print(f"Searching Google: {keyword}")
                await page.goto(url, wait_until="domcontentloaded")

                # Human-like behavior
                await page.mouse.move(100, 100)
                await asyncio.sleep(random.uniform(1, 3))
                await page.mouse.move(200, 200)

                page_html = await page.content()

                # Debug: Save HTML
                with open("debug_google.html", "w", encoding="utf-8") as f:
                    f.write(page_html)

                if "captcha" in page_html.lower() or "비정상적인 트래픽" in page_html:
                    print("⚠  Google CAPTCHA detected, falling back to RSS feed.")
                    results = await self._fetch_via_rss(keyword, max_results)
                    return await self._save_results(keyword, results, rss_fallback=True)

                # Extract results using multiple selectors to cope with frequent DOM changes
                results = []
                candidate_selectors = [
                    "div.g",
                    "div[data-sokoban-container]",
                    ".tF2Cxc",
                    ".Ww4FFb",
                ]

                seen_texts = set()
                candidate_elements = []
                for selector in candidate_selectors:
                    try:
                        elems = await page.locator(selector).all()
                    except Exception:
                        elems = []
                    if not elems:
                        continue
                    for elem in elems:
                        try:
                            txt = await elem.text_content()
                        except Exception:
                            txt = None
                        if not txt or txt in seen_texts:
                            continue
                        seen_texts.add(txt)
                        candidate_elements.append(elem)

                for elem in candidate_elements:
                    if len(results) >= max_results:
                        break

                    try:
                        title = None
                        for title_sel in ["h3", "div[role='heading']"]:
                            try:
                                title_handle = elem.locator(title_sel).first
                                if await title_handle.count():
                                    title = (await title_handle.text_content() or "").strip()
                                    if title:
                                        break
                            except Exception:
                                continue
                        if not title:
                            continue

                        link = None
                        try:
                            link_handle = elem.locator("a").first
                            if await link_handle.count():
                                link = await link_handle.get_attribute("href")
                        except Exception:
                            pass
                        if not link or not link.startswith("http"):
                            continue

                        snippet = ""
                        for snip_sel in [".VwiC3b", ".IJl0Z", ".GI74Re"]:
                            try:
                                snip_handle = elem.locator(snip_sel).first
                                if await snip_handle.count():
                                    snippet = (await snip_handle.text_content() or "").strip()
                                    if snippet:
                                        break
                            except Exception:
                                continue

                        data = {
                            "keyword": keyword,
                            "title": title,
                            "url": link,
                            "snippet": snippet,
                            "source": "google_serp",
                            "rank": len(results) + 1,
                            "crawled_at": datetime.now().isoformat()
                        }
                        results.append(data)
                        print(f"Found Google Result: {title}")
                    except Exception:
                        continue

                if not results:
                    print("⚠  SERP returned 0 items, falling back to Google News RSS.")
                    rss_results = await self._fetch_via_rss(keyword, max_results)
                    return await self._save_results(keyword, rss_results, rss_fallback=True)

                return await self._save_results(keyword, results)
            finally:
                await browser.close()

    async def _save_results(self, keyword: str, results: list[dict], rss_fallback: bool = False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/serp/{timestamp}_{keyword}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        label = "Google RSS fallback" if rss_fallback else "Google SERP"
        print(f"Saved {len(results)} results via {label} to {filename}")
        return results

if __name__ == "__main__":
    crawler = GoogleCrawler(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/google")
    asyncio.run(crawler.search("미국 S&P500 ETF 추천"))
