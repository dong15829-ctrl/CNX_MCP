import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from src.crawler.ultra_stealth import UltraStealth

class YouTubeCrawler:
    def __init__(self, output_dir="data/raw/youtube"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "video_meta"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "thumbnails"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "comments"), exist_ok=True)

    async def collect_comments(self, page, video_url: str, max_comments: int = 50):
        """
        Collects comments from a YouTube video page.
        
        Args:
            page: Playwright page object
            video_url: URL of the YouTube video
            max_comments: Maximum number of comments to collect
            
        Returns:
            List of comment dictionaries
        """
        try:
            print(f"   [Comments] Navigating to video page...")
            await page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Scroll down to load comments section
            print(f"   [Comments] Scrolling to load comments...")
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await asyncio.sleep(1.5)
            
            # Wait for comments to load
            try:
                await page.wait_for_selector("ytd-comment-thread-renderer", timeout=10000)
            except:
                print(f"   ⚠️  No comments found or comments disabled")
                return []
            
            # Scroll to load more comments
            print(f"   [Comments] Loading more comments...")
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while scroll_attempts < max_scroll_attempts:
                # Scroll down
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                
                # Count current comments
                comment_elements = await page.locator("ytd-comment-thread-renderer").all()
                current_count = len(comment_elements)
                
                print(f"   [Comments] Loaded {current_count} comments...")
                
                # Stop if we have enough or no new comments loaded
                if current_count >= max_comments or current_count == last_count:
                    break
                    
                last_count = current_count
                scroll_attempts += 1
            
            # Extract comments
            print(f"   [Comments] Extracting comment data...")
            comment_elements = await page.locator("ytd-comment-thread-renderer").all()
            
            comments = []
            for i, comment_el in enumerate(comment_elements):
                if i >= max_comments:
                    break
                    
                try:
                    # Extract author
                    author = "Unknown"
                    try:
                        author_el = comment_el.locator("#author-text")
                        author = await author_el.text_content()
                        author = author.strip() if author else "Unknown"
                    except:
                        pass
                    
                    # Extract comment text
                    text = ""
                    try:
                        text_el = comment_el.locator("#content-text")
                        text = await text_el.text_content()
                        text = text.strip() if text else ""
                    except:
                        pass
                    
                    # Extract published time
                    published = "Unknown"
                    try:
                        time_el = comment_el.locator("#published-time-text a")
                        published = await time_el.text_content()
                        published = published.strip() if published else "Unknown"
                    except:
                        pass
                    
                    # Extract like count
                    likes = "0"
                    try:
                        like_el = comment_el.locator("#vote-count-middle")
                        likes = await like_el.text_content()
                        likes = likes.strip() if likes else "0"
                    except:
                        pass
                    
                    # Extract reply count
                    reply_count = 0
                    try:
                        reply_el = comment_el.locator("#more-replies span#text")
                        reply_text = await reply_el.text_content()
                        if reply_text and "답글" in reply_text:
                            # Extract number from text like "답글 5개"
                            import re
                            match = re.search(r'\d+', reply_text)
                            if match:
                                reply_count = int(match.group())
                    except:
                        pass
                    
                    if text:  # Only add if we have text
                        comment_data = {
                            "author": author,
                            "text": text,
                            "published": published,
                            "likes": likes,
                            "reply_count": reply_count,
                            "crawled_at": datetime.now().isoformat()
                        }
                        comments.append(comment_data)
                        
                except Exception as e:
                    print(f"   ⚠️  Error parsing comment: {e}")
                    continue
            
            print(f"   ✓ Collected {len(comments)} comments")
            return comments
            
        except Exception as e:
            print(f"   ❌ Error collecting comments: {e}")
            return []

    async def search_and_crawl(self, keyword: str, max_videos: int = 10, collect_comments: bool = True, max_comments_per_video: int = 50):
        """
        Searches for a keyword and crawls video metadata with comments.
        
        Args:
            keyword: Search keyword
            max_videos: Maximum number of videos to crawl
            collect_comments: Whether to collect comments for each video
            max_comments_per_video: Maximum comments to collect per video
        """
        async with async_playwright() as p:
            context, browser = await UltraStealth.create_ultra_stealth_context(p, headless=True)
            page = await context.new_page()
            
            print(f"Searching for: {keyword}")
            await page.goto(f"https://www.youtube.com/results?search_query={keyword}", wait_until="networkidle")
            
            # Scroll to load more videos
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
            
            # Extract video elements
            video_elements = await page.locator("ytd-video-renderer").all()
            
            results = []
            for i, video in enumerate(video_elements):
                if i >= max_videos:
                    break
                
                try:
                    title_el = video.locator("#video-title")
                    title = await title_el.text_content()
                    url = await title_el.get_attribute("href")
                    full_url = f"https://www.youtube.com{url}"
                    
                    meta_el = video.locator("#metadata-line")
                    meta_text = await meta_el.text_content()
                    
                    channel_el = video.locator("#channel-info #text")
                    channel_name = await channel_el.text_content()
                    
                    video_data = {
                        "keyword": keyword,
                        "title": title.strip(),
                        "url": full_url,
                        "meta": meta_text.strip(),
                        "channel": channel_name.strip(),
                        "crawled_at": datetime.now().isoformat()
                    }
                    
                    # Download Thumbnail
                    try:
                        thumb_url = await video.locator("ytd-thumbnail img").get_attribute("src")
                        if not thumb_url or "data:image" in thumb_url:
                            # Try to construct high-res URL from video ID
                            video_id = url.split("v=")[-1].split("&")[0]
                            thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                        
                        if thumb_url:
                            # Use requests to download image
                            import requests
                            img_data = requests.get(thumb_url).content
                            video_id = url.split("v=")[-1].split("&")[0]
                            img_path = f"{self.output_dir}/thumbnails/{video_id}.jpg"
                            with open(img_path, "wb") as f:
                                f.write(img_data)
                            video_data["thumbnail_path"] = img_path
                    except Exception as e:
                        print(f"Error downloading thumbnail: {e}")

                    # Collect comments if enabled
                    if collect_comments:
                        print(f"\n[{i+1}/{max_videos}] Collecting comments for: {title.strip()}")
                        comments = await self.collect_comments(page, full_url, max_comments_per_video)
                        video_data["comments"] = comments
                        video_data["comment_count"] = len(comments)
                        
                        # Save comments separately
                        if comments:
                            video_id = url.split("v=")[-1].split("&")[0]
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            comment_filename = f"{self.output_dir}/comments/{timestamp}_{video_id}_comments.json"
                            with open(comment_filename, "w", encoding="utf-8") as f:
                                json.dump({
                                    "video_id": video_id,
                                    "video_title": title.strip(),
                                    "video_url": full_url,
                                    "keyword": keyword,
                                    "comments": comments,
                                    "crawled_at": datetime.now().isoformat()
                                }, f, ensure_ascii=False, indent=2)
                            print(f"   ✓ Saved comments to {comment_filename}")
                        
                        # Go back to search results
                        await page.goto(f"https://www.youtube.com/results?search_query={keyword}", wait_until="domcontentloaded")
                        await asyncio.sleep(2)

                    results.append(video_data)
                    print(f"✓ [{i+1}/{max_videos}] {title.strip()} ({len(comments) if collect_comments else 0} comments)")
                    
                except Exception as e:
                    print(f"Error parsing video: {e}")
                    continue
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/video_meta/{timestamp}_{keyword}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
                
            print(f"\n✅ Saved {len(results)} videos to {filename}")
            
            await browser.close()
            return results

if __name__ == "__main__":
    crawler = YouTubeCrawler(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/youtube")
    asyncio.run(crawler.search_and_crawl("미국 S&P500 ETF", max_videos=3, collect_comments=True, max_comments_per_video=30))
