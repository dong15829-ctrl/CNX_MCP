import sys
import os
import asyncio
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from src.crawler.youtube_crawler import YouTubeCrawler
from src.analysis.visual_intelligence import VisualIntelligence

async def main():
    # 1. Run Crawler to get thumbnails
    print(">>> Starting Crawler...")
    crawler = YouTubeCrawler()
    results = await crawler.search_and_crawl("미국 S&P500 ETF", max_videos=3)
    
    # 2. Analyze Thumbnails
    print("\n>>> Starting Visual Analysis...")
    vi = VisualIntelligence()
    
    for video in results:
        thumb_path = video.get("thumbnail_path")
        if thumb_path and os.path.exists(thumb_path):
            print(f"\nAnalyzing: {video['title']}")
            analysis = vi.analyze_thumbnail(thumb_path)
            print(f"OCR Text: {analysis['ocr_text']}")
            print(f"Colors: {analysis['dominant_colors']}")
        else:
            print(f"\nSkipping (No thumbnail): {video['title']}")

if __name__ == "__main__":
    asyncio.run(main())
