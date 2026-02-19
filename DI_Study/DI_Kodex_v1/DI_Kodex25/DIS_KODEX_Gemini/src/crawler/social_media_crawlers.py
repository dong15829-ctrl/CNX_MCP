"""
Social Media Crawlers for KODEX Marketing Intelligence
Supports: Instagram, Facebook, Twitter/X

Note: Social media platforms have strict anti-bot measures.
These crawlers use advanced stealth techniques but may require:
- Login credentials (stored securely)
- CAPTCHA solving services
- API access (recommended for production)
"""

import asyncio
import random
import json
import os
from datetime import datetime
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
from advanced_stealth import get_advanced_stealth_context, human_like_delay, random_mouse_movement, human_typing


class InstagramCrawler:
    """
    Instagram crawler for hashtag and profile searches
    
    Note: Instagram heavily restricts scraping. Recommended approaches:
    1. Use official Instagram Graph API (requires Facebook Developer account)
    2. Use login + session cookies
    3. Use third-party APIs (e.g., Apify, ScraperAPI)
    
    This implementation uses web scraping with stealth techniques.
    """
    
    def __init__(self, username=None, password=None):
        self.base_url = "https://www.instagram.com"
        self.username = username
        self.password = password
        
    async def search_hashtag(self, hashtag: str, max_posts: int = 20):
        """Search Instagram by hashtag"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to hashtag
                clean_hashtag = hashtag.replace("#", "")
                url = f"{self.base_url}/explore/tags/{clean_hashtag}/"
                
                print(f"[1/4] Navigating to Instagram hashtag: #{clean_hashtag}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(3000, 5000)
                
                # Check if login required
                if "login" in page.url.lower():
                    print("   ⚠️  Login required - Instagram blocks unauthenticated access")
                    if self.username and self.password:
                        await self._login(page)
                    else:
                        print("   ❌ No credentials provided. Cannot proceed.")
                        return []
                
                # Scroll to load posts
                print(f"[2/4] Scrolling to load posts...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 800})")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_instagram.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Extract posts
                print(f"[3/4] Extracting posts...")
                results = []
                
                # Instagram selectors (may change frequently)
                post_selectors = [
                    "article a[href*='/p/']",  # Post links
                    "div[role='button'] a[href*='/p/']",  # Alternative
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts with: {selector}")
                            
                            for post in posts[:max_posts]:
                                try:
                                    link = await post.get_attribute("href")
                                    
                                    # Get post image
                                    img_url = None
                                    try:
                                        img_elem = post.locator("img").first
                                        if await img_elem.count() > 0:
                                            img_url = await img_elem.get_attribute("src")
                                    except:
                                        pass
                                    
                                    if link:
                                        full_url = urljoin(self.base_url, link)
                                        
                                        post_data = {
                                            "hashtag": f"#{clean_hashtag}",
                                            "url": full_url,
                                            "image_url": img_url,
                                            "source": "instagram",
                                            "crawled_at": datetime.now().isoformat()
                                        }
                                        
                                        results.append(post_data)
                                        print(f"   ✓ [{len(results)}] {full_url}")
                                        
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                print(f"[4/4] Saving results...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/instagram/{timestamp}_{clean_hashtag}_posts.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/instagram", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Instagram posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def _login(self, page):
        """Login to Instagram"""
        print("   [Login] Attempting Instagram login...")
        try:
            # Fill username
            await human_typing(page, "input[name='username']", self.username)
            await human_like_delay(500, 1000)
            
            # Fill password
            await human_typing(page, "input[name='password']", self.password)
            await human_like_delay(500, 1000)
            
            # Click login
            await page.click("button[type='submit']")
            await human_like_delay(3000, 5000)
            
            print("   ✓ Login successful")
        except Exception as e:
            print(f"   ❌ Login failed: {e}")


class FacebookCrawler:
    """
    Facebook crawler for page and group searches
    
    Note: Facebook has extremely strict anti-scraping measures:
    1. Requires login for most content
    2. Uses sophisticated bot detection
    3. Frequently changes HTML structure
    
    Recommended: Use Facebook Graph API instead
    """
    
    def __init__(self, email=None, password=None):
        self.base_url = "https://www.facebook.com"
        self.email = email
        self.password = password
        
    async def search_posts(self, query: str, max_posts: int = 20):
        """Search Facebook posts"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to Facebook
                print(f"[1/4] Navigating to Facebook...")
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Check if login required
                if self.email and self.password:
                    await self._login(page)
                else:
                    print("   ⚠️  No credentials provided - limited access")
                
                # Navigate to search
                encoded_query = quote(query)
                search_url = f"{self.base_url}/search/posts/?q={encoded_query}"
                
                print(f"[2/4] Searching for: {query}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(3000, 5000)
                
                # Scroll
                print(f"[3/4] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 800})")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_facebook.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Extract posts
                print(f"[4/4] Extracting posts...")
                results = []
                
                # Facebook selectors (highly variable)
                post_selectors = [
                    "div[role='article']",
                    "div[data-pagelet*='FeedUnit']",
                ]
                
                for selector in post_selectors:
                    try:
                        posts = await page.locator(selector).all()
                        if posts:
                            print(f"   ✓ Found {len(posts)} posts with: {selector}")
                            
                            for post in posts[:max_posts]:
                                try:
                                    # Extract text content
                                    text = await post.text_content()
                                    
                                    # Extract link
                                    link = None
                                    try:
                                        link_elem = post.locator("a[href*='/posts/'], a[href*='/permalink/']").first
                                        if await link_elem.count() > 0:
                                            link = await link_elem.get_attribute("href")
                                    except:
                                        pass
                                    
                                    if text and len(text.strip()) > 10:
                                        post_data = {
                                            "query": query,
                                            "text": text.strip()[:500],  # Limit text length
                                            "url": urljoin(self.base_url, link) if link else None,
                                            "source": "facebook",
                                            "crawled_at": datetime.now().isoformat()
                                        }
                                        
                                        results.append(post_data)
                                        print(f"   ✓ [{len(results)}] {text[:50]}...")
                                        
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/facebook/{timestamp}_{query}_posts.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/facebook", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Facebook posts to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def _login(self, page):
        """Login to Facebook"""
        print("   [Login] Attempting Facebook login...")
        try:
            # Fill email
            await human_typing(page, "input[name='email']", self.email)
            await human_like_delay(500, 1000)
            
            # Fill password
            await human_typing(page, "input[name='pass']", self.password)
            await human_like_delay(500, 1000)
            
            # Click login
            await page.click("button[name='login']")
            await human_like_delay(5000, 7000)
            
            print("   ✓ Login successful")
        except Exception as e:
            print(f"   ❌ Login failed: {e}")


class TwitterCrawler:
    """
    Twitter/X crawler for hashtag and keyword searches
    
    Note: Twitter/X has strict rate limits and requires authentication:
    1. Free tier: Very limited access
    2. API access: Requires developer account ($100+/month)
    3. Web scraping: Requires login, frequently blocked
    
    Recommended: Use Twitter API v2 instead
    """
    
    def __init__(self, username=None, password=None):
        self.base_url = "https://twitter.com"
        self.username = username
        self.password = password
        
    async def search_tweets(self, query: str, max_tweets: int = 20):
        """Search Twitter/X for tweets"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to Twitter
                print(f"[1/4] Navigating to Twitter/X...")
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Check if login required
                if "login" in page.url.lower() or "i/flow/login" in page.url:
                    print("   ⚠️  Login required")
                    if self.username and self.password:
                        await self._login(page)
                    else:
                        print("   ❌ No credentials provided. Cannot proceed.")
                        return []
                
                # Navigate to search
                encoded_query = quote(query)
                search_url = f"{self.base_url}/search?q={encoded_query}&src=typed_query&f=live"
                
                print(f"[2/4] Searching for: {query}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(3000, 5000)
                
                # Scroll
                print(f"[3/4] Scrolling...")
                for i in range(5):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 800})")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_twitter.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Extract tweets
                print(f"[4/4] Extracting tweets...")
                results = []
                
                # Twitter selectors
                tweet_selectors = [
                    "article[data-testid='tweet']",
                    "div[data-testid='cellInnerDiv']",
                ]
                
                for selector in tweet_selectors:
                    try:
                        tweets = await page.locator(selector).all()
                        if tweets:
                            print(f"   ✓ Found {len(tweets)} tweets with: {selector}")
                            
                            for tweet in tweets[:max_tweets]:
                                try:
                                    # Extract text
                                    text = None
                                    try:
                                        text_elem = tweet.locator("div[data-testid='tweetText']").first
                                        if await text_elem.count() > 0:
                                            text = await text_elem.text_content()
                                    except:
                                        pass
                                    
                                    # Extract author
                                    author = None
                                    try:
                                        author_elem = tweet.locator("div[data-testid='User-Name'] span").first
                                        if await author_elem.count() > 0:
                                            author = await author_elem.text_content()
                                    except:
                                        pass
                                    
                                    # Extract link
                                    link = None
                                    try:
                                        link_elem = tweet.locator("a[href*='/status/']").first
                                        if await link_elem.count() > 0:
                                            link = await link_elem.get_attribute("href")
                                    except:
                                        pass
                                    
                                    if text:
                                        post_data = {
                                            "query": query,
                                            "text": text.strip(),
                                            "author": author.strip() if author else "Unknown",
                                            "url": urljoin(self.base_url, link) if link else None,
                                            "source": "twitter",
                                            "crawled_at": datetime.now().isoformat()
                                        }
                                        
                                        results.append(post_data)
                                        print(f"   ✓ [{len(results)}] @{author}: {text[:50]}...")
                                        
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/twitter/{timestamp}_{query}_tweets.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/twitter", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} tweets to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results
    
    async def _login(self, page):
        """Login to Twitter/X"""
        print("   [Login] Attempting Twitter login...")
        try:
            # Navigate to login
            await page.goto(f"{self.base_url}/i/flow/login", wait_until="domcontentloaded")
            await human_like_delay(2000, 3000)
            
            # Fill username
            await human_typing(page, "input[autocomplete='username']", self.username)
            await human_like_delay(500, 1000)
            
            # Click next
            await page.click("div[role='button']:has-text('Next')")
            await human_like_delay(2000, 3000)
            
            # Fill password
            await human_typing(page, "input[name='password']", self.password)
            await human_like_delay(500, 1000)
            
            # Click login
            await page.click("div[role='button']:has-text('Log in')")
            await human_like_delay(5000, 7000)
            
            print("   ✓ Login successful")
        except Exception as e:
            print(f"   ❌ Login failed: {e}")


class NaverNewsCrawler:
    """
    Naver News crawler for keyword searches.
    """
    
    def __init__(self, username=None, password=None):
        self.base_url = "https://search.naver.com"
        self.username = username
        self.password = password
        
    async def search_news(self, query: str, max_articles: int = 20):
        """Search Naver News for articles"""
        async with async_playwright() as p:
            context, browser = await get_advanced_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                # Navigate to Naver News search
                encoded_query = quote(query)
                search_url = f"{self.base_url}/search.naver?where=news&query={encoded_query}"
                
                print(f"[1/4] Navigating to Naver News search for: {query}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await human_like_delay(2000, 3000)
                
                # Scroll
                print(f"[2/4] Scrolling...")
                for i in range(3):
                    await page.evaluate(f"window.scrollTo(0, {(i+1) * 800})")
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                
                # Save debug
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1", exist_ok=True)
                with open("/home/ubuntu/DI/DIS_Kodex1/debug_naver_news.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML")
                
                # Extract articles
                print(f"[3/4] Extracting articles...")
                results = []
                
                article_selectors = [
                    "ul.list_news > li.bx",
                ]
                
                for selector in article_selectors:
                    try:
                        articles = await page.locator(selector).all()
                        if articles:
                            print(f"   ✓ Found {len(articles)} articles with: {selector}")
                            
                            for article in articles[:max_articles]:
                                try:
                                    title_elem = article.locator("a.news_tit")
                                    title = await title_elem.get_attribute("title")
                                    link = await title_elem.get_attribute("href")
                                    
                                    desc_elem = article.locator("div.news_dsc")
                                    description = await desc_elem.text_content()
                                    
                                    if title and link:
                                        article_data = {
                                            "query": query,
                                            "title": title.strip(),
                                            "description": description.strip(),
                                            "url": link,
                                            "source": "naver_news",
                                            "crawled_at": datetime.now().isoformat()
                                        }
                                        
                                        results.append(article_data)
                                        print(f"   ✓ [{len(results)}] {title[:50]}...")
                                        
                                except:
                                    continue
                            
                            if results:
                                break
                    except:
                        continue
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/ubuntu/DI/DIS_Kodex1/data/raw/naver_news/{timestamp}_{query}_articles.json"
                
                os.makedirs("/home/ubuntu/DI/DIS_Kodex1/data/raw/naver_news", exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"\n✅ Saved {len(results)} Naver News articles to {filename}")
                
            finally:
                await context.close()
                await browser.close()
        
        return results

    async def _login(self, page):
        """Login to Naver (not implemented)"""
        print("   [Login] Naver login not required for news search.")
        pass
