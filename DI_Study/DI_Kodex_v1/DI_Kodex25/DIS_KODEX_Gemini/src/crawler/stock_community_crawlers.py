"""
Stock Community and Financial Site Crawlers
Targets: DC Inside, 주린이, Miraeasset
"""
import asyncio
import json
import random
from datetime import datetime
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement


class DCInsideCrawler:
    """
    DC Inside (디시인사이드) 주식 갤러리 크롤러
    Target: https://gall.dcinside.com/board/lists/?id=stock
    """
    
    def __init__(self):
        self.base_url = "https://gall.dcinside.com"
        self.gallery_id = "stock"  # 주식 갤러리
        
    async def crawl_gallery(self, keyword: str = None, max_posts: int = 20):
        """
        Crawl DC Inside stock gallery
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to stock gallery
                if keyword:
                    # Search within gallery
                    encoded_keyword = quote(keyword)
                    url = f"{self.base_url}/board/lists/?id={self.gallery_id}&s_type=search_subject_memo&s_keyword={encoded_keyword}"
                else:
                    # Get latest posts
                    url = f"{self.base_url}/board/lists/?id={self.gallery_id}"
                
                print(f"[1/3] Navigating to DC Inside stock gallery...")
                print(f"   URL: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Scroll
                print(f"[2/3] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Save debug HTML
                html_content = await page.content()
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_dcinside.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"   ✓ Saved debug HTML")
                
                # Extract posts
                print(f"[3/3] Extracting posts...")
                results = []
                
                # DC Inside selectors (mobile version)
                post_selectors = [
                    "ul.gall-detail-lst > li",  # Mobile list items
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts with: {selector}")
                            
                            for post in posts[:max_posts]:
                                try:
                                    # Extract title and link from mobile structure
                                    title_elem = post.locator(".subjectin").first
                                    link_elem = post.locator("a.lt").first
                                    
                                    if await title_elem.count() > 0 and await link_elem.count() > 0:
                                        title = await title_elem.text_content()
                                        link = await link_elem.get_attribute("href")
                                        
                                        # Extract author from ginfo list
                                        author = "Unknown"
                                        try:
                                            ginfo_items = await post.locator(".ginfo li").all()
                                            if len(ginfo_items) > 0:
                                                author = await ginfo_items[0].text_content()
                                        except:
                                            pass
                                        
                                        # Extract date
                                        date = "Unknown"
                                        try:
                                            ginfo_items = await post.locator(".ginfo li").all()
                                            if len(ginfo_items) > 1:
                                                date = await ginfo_items[1].text_content()
                                        except:
                                            pass
                                        
                                        # Extract views
                                        views = "0"
                                        try:
                                            ginfo_items = await post.locator(".ginfo li").all()
                                            for item in ginfo_items:
                                                text = await item.text_content()
                                                if "조회" in text:
                                                    views = text.replace("조회", "").strip()
                                                    break
                                        except:
                                            pass
                                        
                                        # Extract comments
                                        comments = "0"
                                        try:
                                            comments_elem = post.locator("a.rt .ct").first
                                            if await comments_elem.count() > 0:
                                                comments = await comments_elem.text_content()
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
                                                "views": views,
                                                "comments": comments,
                                                "source": "dcinside_stock",
                                                "crawled_at": datetime.now().isoformat()
                                            }
                                            
                                            results.append(post_data)
                                            print(f"   ✓ [{len(results)}] {title[:50]}...")
                                            
                                except Exception as e:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                keyword_str = keyword if keyword else "latest"
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/dcinside/{timestamp}_{keyword_str}_stock.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/dcinside", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} DC Inside posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results


class MiraeassetCrawler:
    """
    Miraeasset (미래에셋) ETF information crawler
    Target: https://securities.miraeasset.com/hki/hki3028/r01.do
    """
    
    def __init__(self):
        self.base_url = "https://securities.miraeasset.com"
        
    async def crawl_etf_info(self, keyword: str = "S&P500", max_items: int = 20):
        """
        Crawl Miraeasset ETF information
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to ETF page
                url = f"{self.base_url}/hki/hki3028/r01.do"
                
                print(f"[1/4] Navigating to Miraeasset ETF page...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Try to search if keyword provided
                if keyword:
                    print(f"[2/4] Searching for: {keyword}")
                    try:
                        # Look for search box
                        search_selectors = [
                            "input[type='text'][name*='search']",
                            "input[type='text'][placeholder*='검색']",
                            "#searchKeyword",
                        ]
                        
                        for selector in search_selectors:
                            try:
                                if await page.locator(selector).count() > 0:
                                    await page.fill(selector, keyword)
                                    await asyncio.sleep(0.5)
                                    await page.keyboard.press("Enter")
                                    await page.wait_for_load_state("networkidle", timeout=10000)
                                    break
                            except:
                                continue
                    except:
                        print(f"   → Could not search, getting all ETFs")
                
                # Scroll
                print(f"[3/4] Scrolling...")
                try:
                    for i in range(3):
                        await page.evaluate(f"window.scrollTo(0, {(i+1) * 400})")
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    print(f"   → Scroll error (page may have navigated): {e}")
                
                # Save debug HTML
                html_content = await page.content()
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_miraeasset.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"   ✓ Saved debug HTML")
                
                # Extract ETF data
                print(f"[4/4] Extracting ETF information...")
                results = []
                
                # Try different table selectors
                table_selectors = [
                    "table.tbl_ty1 tbody tr",
                    "table tbody tr",
                    ".etf_list tbody tr",
                ]
                
                for selector in table_selectors:
                    try:
                        rows = await page.locator(selector).all()
                        if rows:
                            print(f"   ✓ Found {len(rows)} rows with: {selector}")
                            
                            for row in rows[:max_items]:
                                try:
                                    cells = await row.locator("td").all()
                                    if len(cells) >= 3:
                                        # Extract data from cells
                                        etf_name = await cells[0].text_content() if len(cells) > 0 else ""
                                        etf_code = await cells[1].text_content() if len(cells) > 1 else ""
                                        
                                        # Try to get link
                                        link = ""
                                        try:
                                            link_elem = row.locator("a").first
                                            if await link_elem.count() > 0:
                                                link = await link_elem.get_attribute("href")
                                        except:
                                            pass
                                        
                                        if etf_name and etf_name.strip():
                                            etf_data = {
                                                "keyword": keyword,
                                                "etf_name": etf_name.strip(),
                                                "etf_code": etf_code.strip() if etf_code else "",
                                                "url": urljoin(self.base_url, link) if link else "",
                                                "source": "miraeasset",
                                                "crawled_at": datetime.now().isoformat()
                                            }
                                            
                                            results.append(etf_data)
                                            print(f"   ✓ [{len(results)}] {etf_name[:40]}...")
                                            
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/miraeasset/{timestamp}_{keyword}_etf.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/miraeasset", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Miraeasset ETFs to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results


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
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_fmkorea.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
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
                    "table.board_table tbody tr",
                    "tr.list0, tr.list1",
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts")
                            
                            for post in posts[:max_posts]:
                                try:
                                    # Extract title
                                    title_elem = post.locator("td.list_title a, td.eng a").first
                                    if await title_elem.count() > 0:
                                        title = await title_elem.text_content()
                                        link = await title_elem.get_attribute("href")
                                        
                                        if title and link:
                                            post_data = {
                                                "keyword": keyword or "latest",
                                                "title": title.strip(),
                                                "url": f"https://www.ppomppu.co.kr{link}" if not link.startswith("http") else link,
                                                "source": "ppomppu_stock",
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
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/ppomppu/{timestamp}_{keyword_str}_stock.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/ppomppu", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Ppomppu posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
