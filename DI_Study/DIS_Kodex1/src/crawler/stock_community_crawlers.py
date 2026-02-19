"""
Stock Community and Financial Site Crawlers
Targets: DC Inside, 주린이, Miraeasset
"""
from __future__ import annotations

import asyncio
import html
import json
import random
import re
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
import sys
import os

import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement


class DCInsideCrawler:
    """DC Inside (디시인사이드) 검색 API 기반 크롤러."""

    SEARCH_ENDPOINT = "https://search.dcinside.com/ajax/getSearch"

    def __init__(self):
        self.base_url = "https://gall.dcinside.com"
        self.gallery_id = "stock"
        self.debug_path = "/home/ubuntu/DI/DIS_Kodex1/debug_dcinside.html"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Referer": "https://search.dcinside.com/",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

    async def crawl_gallery(
        self,
        keyword: str = None,
        max_posts: int = 20,
        max_age_days: int = 32,
    ):
        """DC Inside 검색 API를 이용해 게시글을 수집."""

        search_keyword = keyword or self.gallery_id
        per_page = min(max_posts, 50)
        page = 1
        seen_urls = set()
        results = []
        cutoff = datetime.now() - timedelta(days=max_age_days)
        first_page_dumped = False

        while len(results) < max_posts and page <= 10:
            data = await self._fetch_search_page(search_keyword, page, per_page)
            if not data:
                break

            if not first_page_dumped:
                with open(self.debug_path, "w", encoding="utf-8") as dbg:
                    dbg.write(json.dumps(data, ensure_ascii=False, indent=2))
                first_page_dumped = True

            channel = data.get("channel") or {}
            items = channel.get("item") or []
            if not items:
                break

            for item in items:
                normalized = self._normalize_item(search_keyword, item)
                if not normalized:
                    continue

                published_at = normalized.get("published_at")
                if published_at:
                    try:
                        published_dt = datetime.fromisoformat(published_at)
                        if published_dt < cutoff:
                            continue
                    except ValueError:
                        pass

                url = normalized["url"]
                if url in seen_urls:
                    continue

                results.append(normalized)
                seen_urls.add(url)

                if len(results) >= max_posts:
                    break

            if len(results) >= max_posts:
                break

            if channel.get("isEnd"):
                break
            page += 1

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        keyword_str = keyword if keyword else "latest"
        output_dir = "/home/ubuntu/DI/DIS_Kodex1/data/raw/dcinside"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{timestamp}_{keyword_str}_stock.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Saved {len(results)} DC Inside posts to {filename}")
        return results

    async def _fetch_search_page(self, keyword: str, page: int, page_size: int):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._fetch_search_page_sync(keyword, page, page_size),
        )

    def _fetch_search_page_sync(self, keyword: str, page: int, page_size: int):
        encoded_keyword = quote(keyword)
        url = f"{self.SEARCH_ENDPOINT}/p/{page}/n/{page_size}/q/{encoded_keyword}?jsoncallback=?"
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        payload = response.text.strip()
        match = re.search(r"^[^(]*\(\s*(\{.*\})\s*\)\s*$", payload, re.S)
        if not match:
            return None
        return json.loads(match.group(1))

    @staticmethod
    def _clean_text(value: str):
        if not value:
            return ""
        no_tags = re.sub(r"<.*?>", " ", value)
        unescaped = html.unescape(no_tags)
        return re.sub(r"\s+", " ", unescaped).strip()

    @staticmethod
    def _parse_datetime(value: str):
        if not value:
            return None
        value = value.strip()
        date_formats = ["%Y.%m.%d %H:%M", "%Y/%m/%d %H:%M", "%y/%m/%d"]
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        if value.isdigit() and len(value) >= 12:
            try:
                return datetime.strptime(value[:14], "%Y%m%d%H%M%S")
            except ValueError:
                return None
        return None

    def _normalize_item(self, keyword: str, item: dict):
        title = self._clean_text(item.get("title"))
        url = item.get("url")
        if not title or not url:
            return None

        content = self._clean_text(item.get("content"))
        gallery_name = self._clean_text(item.get("gall_name"))
        board_id = item.get("board_id")
        published_raw = item.get("datetime") or item.get("ct")
        published_dt = self._parse_datetime(published_raw)

        return {
            "keyword": keyword,
            "title": title,
            "url": url,
            "gallery_name": gallery_name,
            "board_id": board_id,
            "excerpt": content,
            "published_at": published_dt.isoformat() if published_dt else None,
            "source": "dcinside_stock",
            "crawled_at": datetime.now().isoformat(),
        }


class MiraeassetCrawler:
    """ETF 정보 수집 (네이버 ETF API 기반)."""

    API_URL = "https://finance.naver.com/api/sise/etfItemList.nhn"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://finance.naver.com/sise/etf.naver",
            }
        )

    async def crawl_etf_info(self, keyword: str = "S&P500", max_items: int = 20):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None,
            lambda: self._fetch_etf_list(keyword),
        )

        results = []
        etf_items = (data or {}).get("result", {}).get("etfItemList", [])
        for item in etf_items[:max_items]:
            etf_data = {
                "keyword": keyword,
                "item_code": item.get("itemcode"),
                "item_name": item.get("itemname"),
                "price": item.get("nowVal"),
                "change_value": item.get("changeVal"),
                "change_rate": item.get("changeRate"),
                "rise_fall": item.get("risefall"),
                "nav": item.get("nav"),
                "three_month_return": item.get("threeMonthEarnRate"),
                "volume": item.get("quant"),
                "trading_amount": item.get("amonut"),
                "market_cap": item.get("marketSum"),
                "source": "naver_etf_api",
                "crawled_at": datetime.now().isoformat(),
            }
            results.append(etf_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "/home/ubuntu/DI/DIS_Kodex1/data/raw/miraeasset"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/{timestamp}_{keyword}_etf.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        with open("/home/ubuntu/DI/DIS_Kodex1/debug_miraeasset.html", "w", encoding="utf-8") as dbg:
            dbg.write(json.dumps(data, ensure_ascii=False, indent=2))

        print(f"\n✅ Saved {len(results)} Miraeasset ETFs to {filename}")
        return results

    def _fetch_etf_list(self, keyword: str):
        params = {
            "code": "ETF",
            "target": "fundName",
            "query": keyword,
        }
        response = self.session.get(self.API_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()


class FMKoreaCrawler:
    """
    FMKorea (에펨코리아) 주식 게시판 크롤러
    Target: https://www.fmkorea.com/index.php?mid=stock
    """
    
    def __init__(self):
        self.base_url = "https://www.fmkorea.com"
        self.board_id = "stock"  # 주식 게시판
        
    async def crawl_stock_board(self, keyword: str = None, max_posts: int = 20):
        """Crawl FMKorea stock board"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to stock board
                if keyword:
                    encoded_keyword = quote(keyword)
                    url = f"{self.base_url}/index.php?mid={self.board_id}&search_target=title_content&search_keyword={encoded_keyword}"
                else:
                    url = f"{self.base_url}/index.php?mid={self.board_id}"
                
                print(f"[1/3] Navigating to FMKorea stock board...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Scroll
                print(f"[2/3] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                html_content = await page.content()
                if "에펨코리아 보안 시스템" in html_content:
                    raise RuntimeError(
                        "FMKorea blocked the crawler with a security challenge. "
                        "Provide valid FMKorea cookies (cf_clearance) before retrying."
                    )
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_fmkorea.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"   ✓ Saved debug HTML")
                
                # Extract
                print(f"[3/3] Extracting posts...")
                results = []
                
                # FMKorea selectors
                post_selectors = [
                    "li.li_best_li",  # Best posts
                    "tbody tr",  # Regular table rows
                    ".bd_lst li",  # List items
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts with: {selector}")
                            
                            for post in posts[:max_posts]:
                                try:
                                    # Extract title and link
                                    title_elem = post.locator("a.hx").first
                                    if await title_elem.count() == 0:
                                        title_elem = post.locator(".title a, a.subject").first
                                    
                                    if await title_elem.count() > 0:
                                        title = await title_elem.text_content()
                                        link = await title_elem.get_attribute("href")
                                        
                                        # Extract author
                                        author = "Unknown"
                                        try:
                                            author_elem = post.locator(".author, .nickname").first
                                            if await author_elem.count() > 0:
                                                author = await author_elem.text_content()
                                        except:
                                            pass
                                        
                                        # Extract date
                                        date = "Unknown"
                                        try:
                                            date_elem = post.locator(".time, .date").first
                                            if await date_elem.count() > 0:
                                                date = await date_elem.text_content()
                                        except:
                                            pass
                                        
                                        if title and link:
                                            full_url = urljoin(self.base_url, link) if not link.startswith("http") else link
                                            
                                            post_data = {
                                                "keyword": keyword or "latest",
                                                "title": title.strip(),
                                                "url": full_url,
                                                "author": author.strip() if author else "Unknown",
                                                "date": date.strip() if date else "Unknown",
                                                "source": "fmkorea_stock",
                                                "crawled_at": datetime.now().isoformat()
                                            }
                                            
                                            results.append(post_data)
                                            print(f"   ✓ [{len(results)}] {title[:50]}...")
                                            
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                keyword_str = keyword if keyword else "latest"
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/fmkorea/{timestamp}_{keyword_str}_stock.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/fmkorea", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} FMKorea posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results


class StockDiscussionCrawler:
    """
    종목토론방 크롤러
    Target: Naver Finance stock discussion boards
    """
    
    def __init__(self):
        self.base_url = "https://finance.naver.com"
        
    async def crawl_stock_discussion(self, stock_code: str, max_posts: int = 20):
        """Crawl Naver Finance stock discussion board"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to stock discussion
                url = f"{self.base_url}/item/board.naver?code={stock_code}"
                
                print(f"[1/3] Navigating to stock discussion for {stock_code}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Scroll
                print(f"[2/3] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_stock_discussion.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Extract
                print(f"[3/3] Extracting posts...")
                results = []
                
                # Stock discussion selectors
                post_selectors = [
                    "table.type2 tbody tr",  # Discussion table
                    ".tb_cont tbody tr",  # Alternative table
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts with: {selector}")
                            
                            for post in posts[:max_posts]:
                                try:
                                    # Extract title and link
                                    title_elem = post.locator("td.title a").first
                                    if await title_elem.count() > 0:
                                        title = await title_elem.text_content()
                                        link = await title_elem.get_attribute("href")
                                        
                                        # Extract author
                                        author = "Unknown"
                                        try:
                                            author_elem = post.locator("td.p11").first
                                            if await author_elem.count() > 0:
                                                author = await author_elem.text_content()
                                        except:
                                            pass
                                        
                                        # Extract date
                                        date = "Unknown"
                                        try:
                                            date_elem = post.locator("td.date").first
                                            if await date_elem.count() > 0:
                                                date = await date_elem.text_content()
                                        except:
                                            pass
                                        
                                        # Extract views
                                        views = "0"
                                        try:
                                            views_elem = post.locator("td.num").first
                                            if await views_elem.count() > 0:
                                                views = await views_elem.text_content()
                                        except:
                                            pass
                                        
                                        if title and link:
                                            full_url = urljoin(self.base_url, link) if not link.startswith("http") else link
                                            
                                            post_data = {
                                                "stock_code": stock_code,
                                                "title": title.strip(),
                                                "url": full_url,
                                                "author": author.strip() if author else "Unknown",
                                                "date": date.strip() if date else "Unknown",
                                                "views": views.strip() if views else "0",
                                                "source": "naver_stock_discussion",
                                                "crawled_at": datetime.now().isoformat()
                                            }
                                            
                                            results.append(post_data)
                                            print(f"   ✓ [{len(results)}] {title[:50]}...")
                                            
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/stock_discussion/{timestamp}_{stock_code}_discussion.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/stock_discussion", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} stock discussion posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results


class JulineCrawler:
    """
    주린이 (Juline) 커뮤니티 크롤러
    Note: 주린이는 여러 커뮤니티에 분산되어 있으므로, 
    주요 주식 커뮤니티 사이트들을 타겟팅합니다.
    """
    
    def __init__(self):
        # 주린이 관련 주요 커뮤니티 URLs
        self.communities = {
            "ppomppu": "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock",
            "clien": "https://www.clien.net/service/board/cm_stock",
        }
        
    async def crawl_ppomppu(self, keyword: str = None, max_posts: int = 20):
        """Crawl Ppomppu stock board"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                url = self.communities["ppomppu"]
                if keyword:
                    encoded_keyword = quote(keyword)
                    url = f"{url}&s_type=subject&s_keyword={encoded_keyword}"
                
                print(f"[1/3] Navigating to Ppomppu stock board...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Scroll
                print(f"[2/3] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_ppomppu.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                
                # Extract
                print(f"[3/3] Extracting posts...")
                results = []
                
                # Ppomppu selectors
                post_selectors = [
                    "tr.baseList",
                    "table.board_table tbody tr",
                    "tr.list0, tr.list1",
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts")
                            
                            for post in posts:
                                if len(results) >= max_posts:
                                    break
                                try:
                                    classes = (await post.get_attribute("class")) or ""
                                    if "baseNotice" in classes:
                                        continue

                                    title_elem = post.locator("a.baseList-title, td.list_title a, td.eng a").first
                                    if await title_elem.count() == 0:
                                        continue
                                    title = (await title_elem.text_content()) or ""
                                    link = await title_elem.get_attribute("href") or ""
                                    if not title.strip() or not link:
                                        continue

                                    full_url = (
                                        link
                                        if link.startswith("http")
                                        else urljoin("https://www.ppomppu.co.kr/zboard/", link.lstrip("/"))
                                    )

                                    author = "Unknown"
                                    author_elem = post.locator(".baseList-name span, .list_vspace span").first
                                    if await author_elem.count() > 0:
                                        author_text = await author_elem.text_content()
                                        if author_text:
                                            author = author_text.strip()

                                    date_elem = post.locator("time.baseList-time").first
                                    published_iso = None
                                    if await date_elem.count() > 0:
                                        date_attr = await date_elem.get_attribute("title")
                                        if not date_attr:
                                            parent = date_elem.locator("xpath=..")
                                            if await parent.count() > 0:
                                                date_attr = await parent.get_attribute("title")
                                        date_text = await date_elem.text_content()
                                        published_iso = self._parse_ppomppu_datetime(date_attr or date_text)

                                    views = ""
                                    views_elem = post.locator(".baseList-views").first
                                    if await views_elem.count() > 0:
                                        views_text = await views_elem.text_content()
                                        if views_text:
                                            views = views_text.strip()

                                    recommendations = ""
                                    rec_elem = post.locator(".baseList-rec").first
                                    if await rec_elem.count() > 0:
                                        rec_text = await rec_elem.text_content()
                                        if rec_text:
                                            recommendations = rec_text.strip()

                                    comments = "0"
                                    comment_elem = post.locator(".baseList-c").first
                                    if await comment_elem.count() > 0:
                                        comment_text = await comment_elem.text_content()
                                        if comment_text:
                                            comments = comment_text.strip()

                                    post_data = {
                                        "keyword": keyword or "latest",
                                        "title": title.strip(),
                                        "url": full_url,
                                        "author": author,
                                        "published_at": published_iso,
                                        "views": views,
                                        "recommendations": recommendations,
                                        "comments": comments,
                                        "source": "ppomppu_stock",
                                        "crawled_at": datetime.now().isoformat()
                                    }
                                    
                                    results.append(post_data)
                                    print(f"   ✓ [{len(results)}] {title[:50]}...")
                                except Exception:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                keyword_str = keyword if keyword else "latest"
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/ppomppu/{timestamp}_{keyword_str}_stock.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/ppomppu", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Ppomppu posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results

    @staticmethod
    def _parse_ppomppu_datetime(value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        date_formats = [
            "%y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M:%S",
            "%y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%y/%m/%d",
            "%Y/%m/%d",
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        return None
