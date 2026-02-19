import asyncio
import json
import os
import random
import re
from datetime import datetime, timedelta
from urllib.parse import quote

from playwright.async_api import async_playwright

from advanced_stealth import (
    get_advanced_stealth_context,
    human_like_delay,
    random_mouse_movement,
    human_typing,
)


class AdvancedNaverCrawler:
    """
    Advanced Naver crawler with comprehensive anti-detection measures.
    Supports: Blog, Cafe, and Stock Cafe crawling.
    """
    
    def __init__(self):
        self.base_url = "https://search.naver.com"

    @staticmethod
    def _clean_text(value: str) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _infer_source_from_url(url: str) -> str:
        if not url:
            return "unknown"
        if "cafe.naver.com" in url:
            return "cafe"
        if "blog.naver.com" in url or "m.blog.naver.com" in url or "blog.me" in url:
            return "blog"
        return "web"

    @staticmethod
    def _build_nso_param(date_range: str | None) -> str:
        if not date_range:
            return ""
        allowed = {"1d", "1w", "1m", "1y"}
        if date_range in allowed:
            return f"&nso=p:{date_range}"
        return ""

    def _normalize_date_text(self, raw_text: str) -> str:
        if not raw_text:
            return ""

        text = raw_text.strip()
        if not text:
            return ""

        absolute_match = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", text)
        if absolute_match:
            year, month, day = map(int, absolute_match.groups())
            try:
                return datetime(year, month, day).isoformat()
            except ValueError:
                return ""

        now = datetime.now()
        simple_map = {
            "오늘": 0,
            "어제": 1,
            "그제": 2,
            "그저께": 2,
        }
        if text in simple_map:
            return (now - timedelta(days=simple_map[text])).isoformat()

        relative_match = re.match(r"(\d+)\s*(초|분|시간|일|주|개월|달|년)\s*전", text)
        if relative_match:
            value = int(relative_match.group(1))
            unit = relative_match.group(2)
            delta = timedelta()
            if unit == "초":
                delta = timedelta(seconds=value)
            elif unit == "분":
                delta = timedelta(minutes=value)
            elif unit == "시간":
                delta = timedelta(hours=value)
            elif unit == "일":
                delta = timedelta(days=value)
            elif unit == "주":
                delta = timedelta(weeks=value)
            elif unit in {"개월", "달"}:
                delta = timedelta(days=value * 30)
            elif unit == "년":
                delta = timedelta(days=value * 365)
            return (now - delta).isoformat()

        return ""

    def _build_result_record(
        self,
        *,
        keyword: str,
        source_label: str,
        title: str,
        url: str,
        snippet: str = "",
        date_text: str = "",
        outlet: str = "",
        cafe_name: str = "",
        thumbnail: str = "",
    ) -> dict:
        record = {
            "keyword": keyword,
            "title": title,
            "url": url,
            "snippet": snippet,
            "date": date_text,
            "published_at": self._normalize_date_text(date_text),
            "source": source_label,
            "crawled_at": datetime.now().isoformat(),
        }
        if outlet:
            record["outlet"] = outlet
        if cafe_name:
            record["cafe_name"] = cafe_name
        if thumbnail:
            record["thumbnail"] = thumbnail
        return record

    async def _extract_view_results(
        self,
        page,
        *,
        max_posts: int,
        allowed_domains: list[str] | None = None,
    ) -> list[dict]:
        script = """
        ({ maxItems, allowedDomains }) => {
            const sanitize = (value) =>
                (value || "").replace(/\\s+/g, " ").trim();
            const matchesDomain = (href) => {
                if (!allowedDomains || allowedDomains.length === 0) {
                    return true;
                }
                try {
                    const host = new URL(href).hostname;
                    return allowedDomains.some((domain) => host.includes(domain));
                } catch (err) {
                    return false;
                }
            };

            const anchors = Array.from(
                document.querySelectorAll("#main_pack a[href]")
            );
            const results = [];
            const seen = new Set();

            for (const anchor of anchors) {
                const href = anchor.href;
                if (!href || seen.has(href) || !matchesDomain(href)) {
                    continue;
                }

                const cardRoot =
                    anchor.closest("div[data-fender-root]") ||
                    anchor.closest(".total_wrap") ||
                    anchor.closest("li") ||
                    anchor;

                const titleNode =
                    anchor.querySelector("span.sds-comps-text-type-headline1") ||
                    anchor.querySelector("span.sds-comps-text-type-headline2") ||
                    anchor.querySelector("span.sds-comps-text-type-body2") ||
                    anchor;
                const title = sanitize(titleNode?.textContent || "");
                if (!title) {
                    continue;
                }

                const snippetNode =
                    cardRoot?.querySelector("span.sds-comps-text-type-body1") ||
                    cardRoot?.querySelector("span.sds-comps-text-ellipsis-3") ||
                    cardRoot?.querySelector(".total_dsc") ||
                    cardRoot?.querySelector(".api_txt_lines");
                let snippet = sanitize(snippetNode?.textContent || "");

                const dateNode =
                    cardRoot?.querySelector(".sds-comps-profile-info-subtext") ||
                    cardRoot?.querySelector("span.txt_sub") ||
                    cardRoot?.querySelector("span.sub_time") ||
                    cardRoot?.querySelector("span.sub");
                const dateText = sanitize(dateNode?.textContent || "");

                const outletNode =
                    cardRoot?.querySelector(".sds-comps-profile-info-title-text") ||
                    cardRoot?.querySelector(".source_box") ||
                    cardRoot?.querySelector(".txt_info") ||
                    cardRoot?.querySelector(".name");
                const outlet = sanitize(outletNode?.textContent || "");

                const imageNode =
                    cardRoot?.querySelector("img") || anchor.querySelector("img");
                const thumbnail = imageNode?.getAttribute("src") || "";

                if (title.length <= 2 && snippet.length <= 2) {
                    continue;
                }
                if (snippet.length <= 2) {
                    snippet = "";
                }

                results.push({
                    title,
                    url: href,
                    snippet,
                    dateText,
                    outlet,
                    thumbnail,
                });
                seen.add(href);

                if (results.length >= Math.max(maxItems * 3, maxItems)) {
                    break;
                }
            }
            return results;
        }
        """
        raw_items = await page.evaluate(
            script,
            {
                "maxItems": max_posts,
                "allowedDomains": allowed_domains or [],
            },
        )

        deduped = []
        seen = set()
        for item in raw_items:
            url = item.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            deduped.append(item)
            if len(deduped) >= max_posts:
                break
        return deduped

    async def _extract_blog_cards_legacy(self, page, *, max_posts: int) -> list[dict]:
        selectors_to_try = [
            ".lst_total .bx",
            ".api_subject_bx .total_wrap",
            ".sh_blog_top",
            "li.bx:not(.lineup)",
            ".view_wrap",
        ]

        snippet_selectors = [
            ".total_dsc",
            ".api_txt_lines.dsc_txt",
            ".dsc_txt",
        ]

        results = []
        seen_urls = set()

        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
            except Exception:
                elements = []
            if not elements:
                continue

            for elem in elements:
                if len(results) >= max_posts * 2:
                    break
                try:
                    title_elem = elem.locator("a.title_link, a.api_txt_lines, .total_tit").first
                    if not await title_elem.count():
                        continue
                    title_text = self._clean_text(await title_elem.text_content())
                    title_link = await title_elem.get_attribute("href")
                    if not title_link:
                        continue
                    if (
                        "blog.naver.com" not in title_link
                        and "m.blog.naver.com" not in title_link
                        and "blog.me" not in title_link
                    ):
                        continue
                    url = (
                        title_link
                        if title_link.startswith("http")
                        else f"https://search.naver.com{title_link}"
                    )
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    date_text = ""
                    for ds in [".sub_time", ".sub", ".date", "span.sub"]:
                        try:
                            date_elem = elem.locator(ds).first
                            if await date_elem.count():
                                date_text = self._clean_text(
                                    await date_elem.text_content()
                                )
                                break
                        except Exception:
                            continue

                    snippet_text = ""
                    for ss in snippet_selectors:
                        try:
                            snip_elem = elem.locator(ss).first
                            if await snip_elem.count():
                                snippet_text = self._clean_text(
                                    await snip_elem.text_content()
                                )
                                break
                        except Exception:
                            continue

                    results.append(
                        {
                            "title": title_text,
                            "url": url,
                            "dateText": date_text,
                            "snippet": snippet_text,
                        }
                    )
                except Exception:
                    continue

        return results[:max_posts]

    async def _extract_cafe_cards_legacy(self, page, *, max_posts: int) -> list[dict]:
        selectors_to_try = [
            ".lst_total .bx",
            ".api_subject_bx .total_wrap",
            "li.bx:not(.lineup)",
        ]

        results = []
        seen_urls = set()

        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
            except Exception:
                elements = []
            if not elements:
                continue

            for elem in elements:
                if len(results) >= max_posts * 2:
                    break
                try:
                    title_elem = elem.locator("a.title_link, a.api_txt_lines, .total_tit").first
                    if not await title_elem.count():
                        continue
                    title_text = self._clean_text(await title_elem.text_content())
                    title_link = await title_elem.get_attribute("href")
                    if not title_link or "cafe.naver.com" not in title_link:
                        continue
                    url = (
                        title_link
                        if title_link.startswith("http")
                        else f"https://search.naver.com{title_link}"
                    )
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    cafe_name = ""
                    for cs in [".name", ".txt_name", "a.name"]:
                        try:
                            cafe_elem = elem.locator(cs).first
                            if await cafe_elem.count():
                                cafe_name = self._clean_text(
                                    await cafe_elem.text_content()
                                )
                                break
                        except Exception:
                            continue

                    results.append(
                        {
                            "title": title_text,
                            "url": url,
                            "dateText": "",
                            "snippet": "",
                            "cafeName": cafe_name,
                        }
                    )
                except Exception:
                    continue

        return results[:max_posts]
        
    async def search_blog(
        self,
        keyword: str,
        max_posts: int = 10,
        date_range: str | None = None,
    ):
        """
        Search Naver Blog with advanced stealth techniques.
        """
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Direct navigation to blog search results (more reliable)
                encoded_keyword = quote(keyword)
                nso_param = self._build_nso_param(date_range)
                search_url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}{nso_param}"
                
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

                print(f"[3/3] Extracting blog posts...")
                try:
                    await page.wait_for_selector(
                        "#main_pack a[href*='blog.naver.com'], #main_pack a[href*='m.blog.naver.com']",
                        timeout=15000,
                    )
                except Exception:
                    print("   ⚠ VIEW anchors not detected before timeout; continuing with legacy selectors.")
                modern_items = await self._extract_view_results(
                    page,
                    max_posts=max_posts,
                    allowed_domains=[
                        "blog.naver.com",
                        "m.blog.naver.com",
                        "blog.me",
                    ],
                )
                print(f"   → Modern VIEW candidate count: {len(modern_items)}")

                results = []
                for item in modern_items:
                    record = self._build_result_record(
                        keyword=keyword,
                        source_label="blog",
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        date_text=item.get("dateText", ""),
                        outlet=item.get("outlet", ""),
                        thumbnail=item.get("thumbnail", ""),
                    )
                    results.append(record)

                if not results:
                    print("   → Modern VIEW parsing empty, falling back to legacy selectors")
                    legacy_items = await self._extract_blog_cards_legacy(
                        page, max_posts=max_posts
                    )
                    for item in legacy_items:
                        record = self._build_result_record(
                            keyword=keyword,
                            source_label="blog",
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            date_text=item.get("dateText", ""),
                        )
                        results.append(record)

                results = results[:max_posts]

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/raw/naver/search_rank/{timestamp}_{keyword}_blog.json"
                os.makedirs(os.path.dirname(filename), exist_ok=True)

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} blog posts to {filename}")
                
                await human_like_delay(1000, 2000)
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def search_cafe(
        self,
        keyword: str,
        max_posts: int = 10,
        date_range: str | None = None,
    ):
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

                try:
                    await page.wait_for_selector(
                        "#main_pack a[href*='cafe.naver.com']",
                        timeout=15000,
                    )
                except Exception:
                    print("   ⚠ VIEW cafe anchors not detected before timeout; continuing with legacy selectors.")
                if date_range:
                    print(f"   → Applying date filter: {date_range}")
                    encoded_keyword = quote(keyword)
                    nso_param = self._build_nso_param(date_range)
                    cafe_url = f"https://search.naver.com/search.naver?where=article&query={encoded_keyword}{nso_param}"
                    await page.goto(cafe_url, wait_until="domcontentloaded", timeout=30000)
                    await human_like_delay(1500, 2500)

                modern_items = await self._extract_view_results(
                    page,
                    max_posts=max_posts,
                    allowed_domains=["cafe.naver.com"],
                )
                print(f"   → Modern VIEW candidate count: {len(modern_items)}")

                results = []
                for item in modern_items:
                    source_type = self._infer_source_from_url(item.get("url", ""))
                    cafe_name = item.get("outlet", "")
                    record = self._build_result_record(
                        keyword=keyword,
                        source_label=source_type if source_type != "web" else "cafe",
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        date_text=item.get("dateText", ""),
                        outlet=item.get("outlet", ""),
                        cafe_name=cafe_name,
                        thumbnail=item.get("thumbnail", ""),
                    )
                    results.append(record)

                if not results:
                    print("   → Modern VIEW parsing empty, falling back to legacy selectors")
                    legacy_items = await self._extract_cafe_cards_legacy(
                        page, max_posts=max_posts
                    )
                    for item in legacy_items:
                        record = self._build_result_record(
                            keyword=keyword,
                            source_label="cafe",
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            date_text=item.get("dateText", ""),
                            cafe_name=item.get("cafeName", ""),
                        )
                        results.append(record)

                results = results[:max_posts]

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/raw/naver/search_rank/{timestamp}_{keyword}_cafe.json"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} cafe posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def search_stock_cafe(
        self,
        stock_keyword: str,
        max_posts: int = 20,
        date_range: str | None = None,
    ):
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
                results = await self.search_cafe(
                    search_query,
                    max_posts=max_posts // len(stock_cafes),
                    date_range=date_range,
                )
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
