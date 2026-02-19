import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from src.crawler.ultra_stealth import get_ultra_stealth_context, UltraStealth

class YouTubeCrawlerUltraStealth:
    def __init__(self, output_dir="data/raw/youtube"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "video_meta"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "thumbnails"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "comments"), exist_ok=True)

    async def collect_comments(self, page, video_url: str, max_comments: int = 50):
        """
        YouTube 비디오 댓글 수집 (Ultra Stealth)
        """
        try:
            print(f"   [Comments] Navigating to video page...")
            await page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
            await UltraStealth.human_like_delay(2000, 4000)
            
            # 페이지 읽기 시뮬레이션
            await UltraStealth.simulate_reading(page, 2000)
            
            # 댓글 섹션까지 스크롤
            print(f"   [Comments] Scrolling to comments section...")
            await UltraStealth.random_scroll(page, scrolls=3)
            
            # 댓글 로딩 대기
            try:
                await page.wait_for_selector("ytd-comment-thread-renderer", timeout=10000)
            except:
                print(f"   ⚠️  No comments found or comments disabled")
                return []
            
            # 더 많은 댓글 로드
            print(f"   [Comments] Loading more comments...")
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 10
            
            while scroll_attempts < max_scroll_attempts:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await UltraStealth.human_like_delay(1500, 2500)
                
                comment_elements = await page.locator("ytd-comment-thread-renderer").all()
                current_count = len(comment_elements)
                
                print(f"   [Comments] Loaded {current_count} comments...")
                
                if current_count >= max_comments or current_count == last_count:
                    break
                    
                last_count = current_count
                scroll_attempts += 1
                
                # 랜덤 마우스 움직임
                if random.random() < 0.3:
                    await UltraStealth.random_mouse_movement(page)
            
            # 댓글 추출
            print(f"   [Comments] Extracting comment data...")
            comment_elements = await page.locator("ytd-comment-thread-renderer").all()
            
            comments = []
            for i, comment_el in enumerate(comment_elements):
                if i >= max_comments:
                    break
                    
                try:
                    author = "Unknown"
                    try:
                        author_el = comment_el.locator("#author-text")
                        author = await author_el.text_content()
                        author = author.strip() if author else "Unknown"
                    except:
                        pass
                    
                    text = ""
                    try:
                        text_el = comment_el.locator("#content-text")
                        text = await text_el.text_content()
                        text = text.strip() if text else ""
                    except:
                        pass
                    
                    published = "Unknown"
                    try:
                        time_el = comment_el.locator("#published-time-text a")
                        published = await time_el.text_content()
                        published = published.strip() if published else "Unknown"
                    except:
                        pass
                    
                    likes = "0"
                    try:
                        like_el = comment_el.locator("#vote-count-middle")
                        likes = await like_el.text_content()
                        likes = likes.strip() if likes else "0"
                    except:
                        pass
                    
                    reply_count = 0
                    try:
                        reply_el = comment_el.locator("#more-replies span#text")
                        reply_text = await reply_el.text_content()
                        if reply_text and "답글" in reply_text:
                            import re
                            match = re.search(r'\d+', reply_text)
                            if match:
                                reply_count = int(match.group())
                    except:
                        pass
                    
                    if text:
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
        YouTube 검색 및 크롤링 (Ultra Stealth)
        """
        async with async_playwright() as p:
            context, browser = await get_ultra_stealth_context(p, headless=True)
            page = await context.new_page()
            
            try:
                print(f"🔍 Searching YouTube for: {keyword}")
                
                # YouTube 검색 페이지로 이동
                search_url = f"https://www.youtube.com/results?search_query={keyword}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                
                # 페이지 로딩 대기 및 읽기 시뮬레이션
                await UltraStealth.simulate_reading(page, 3000)
                
                # 디버그 HTML 저장
                debug_path = f"{self.output_dir}/debug_youtube_ultra.html"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(await page.content())
                print(f"   ✓ Saved debug HTML to {debug_path}")
                
                # 스크롤하여 더 많은 비디오 로드
                print(f"📜 Scrolling to load more videos...")
                await UltraStealth.random_scroll(page, scrolls=3)
                
                # 비디오 요소 추출
                print(f"🎥 Extracting video elements...")
                video_elements = await page.locator("ytd-video-renderer").all()
                
                if not video_elements:
                    print(f"   ⚠️  No video elements found with 'ytd-video-renderer'")
                    # 대체 셀렉터 시도
                    video_elements = await page.locator("ytd-rich-item-renderer").all()
                    print(f"   ℹ️  Found {len(video_elements)} with 'ytd-rich-item-renderer'")
                
                print(f"   ✓ Found {len(video_elements)} video elements")
                
                results = []
                for i, video in enumerate(video_elements):
                    if i >= max_videos:
                        break
                    
                    try:
                        # 제목 및 URL 추출
                        title_el = video.locator("#video-title")
                        title = await title_el.text_content()
                        url = await title_el.get_attribute("href")
                        
                        if not url:
                            continue
                            
                        full_url = f"https://www.youtube.com{url}" if url.startswith("/") else url
                        
                        # 메타데이터 추출
                        meta_text = ""
                        try:
                            meta_el = video.locator("#metadata-line")
                            meta_text = await meta_el.text_content()
                        except:
                            pass
                        
                        # 채널명 추출
                        channel_name = ""
                        try:
                            channel_el = video.locator("#channel-info #text, #channel-name #text")
                            channel_name = await channel_el.first.text_content()
                        except:
                            pass
                        
                        video_data = {
                            "keyword": keyword,
                            "title": title.strip() if title else "",
                            "url": full_url,
                            "meta": meta_text.strip() if meta_text else "",
                            "channel": channel_name.strip() if channel_name else "",
                            "crawled_at": datetime.now().isoformat()
                        }
                        
                        # 썸네일 다운로드
                        try:
                            thumb_url = await video.locator("ytd-thumbnail img, img").first.get_attribute("src")
                            if thumb_url and "data:image" not in thumb_url:
                                import requests
                                img_data = requests.get(thumb_url).content
                                video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
                                img_path = f"{self.output_dir}/thumbnails/{video_id}.jpg"
                                with open(img_path, "wb") as f:
                                    f.write(img_data)
                                video_data["thumbnail_path"] = img_path
                        except Exception as e:
                            print(f"   ⚠️  Thumbnail error: {e}")

                        # 댓글 수집
                        if collect_comments and full_url:
                            print(f"\n💬 [{i+1}/{max_videos}] Collecting comments for: {title.strip()[:50]}...")
                            comments = await self.collect_comments(page, full_url, max_comments_per_video)
                            video_data["comments"] = comments
                            video_data["comment_count"] = len(comments)
                            
                            # 댓글 별도 저장
                            if comments:
                                video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
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
                                print(f"   ✓ Saved {len(comments)} comments")
                            
                            # 검색 결과로 돌아가기
                            await page.goto(search_url, wait_until="domcontentloaded")
                            await UltraStealth.human_like_delay(2000, 3000)

                        results.append(video_data)
                        print(f"✅ [{i+1}/{max_videos}] {title.strip()[:60]}... ({len(comments) if collect_comments else 0} comments)")
                        
                    except Exception as e:
                        print(f"   ❌ Error parsing video {i+1}: {e}")
                        continue
                
                # 결과 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.output_dir}/video_meta/{timestamp}_{keyword}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                    
                print(f"\n🎉 Saved {len(results)} videos to {filename}")
                
                return results
                
            except Exception as e:
                print(f"❌ Critical error: {e}")
                import traceback
                traceback.print_exc()
                return []
            finally:
                await browser.close()

if __name__ == "__main__":
    import random
    crawler = YouTubeCrawlerUltraStealth(output_dir="/home/ubuntu/DI/DIS_Kodex1/data/raw/youtube")
    asyncio.run(crawler.search_and_crawl("KODEX ETF", max_videos=5, collect_comments=True, max_comments_per_video=30))
