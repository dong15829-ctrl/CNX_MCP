"""
Test script for social media crawlers
Tests: Instagram, Facebook, Twitter/X

WARNING: Social media platforms require login credentials.
Set environment variables or update this file with your credentials.
"""
import asyncio
import os
from social_media_crawlers import InstagramCrawler, FacebookCrawler, TwitterCrawler


async def main():
    print("=" * 80)
    print("🚀 Social Media Crawlers Test")
    print("=" * 80)
    print()
    
    # Test query
    test_query = "KODEX"
    test_hashtag = "ETF"
    
    # Get credentials from environment (recommended) or set directly
    ig_username = os.getenv("INSTAGRAM_USERNAME", None)
    ig_password = os.getenv("INSTAGRAM_PASSWORD", None)
    
    fb_email = os.getenv("FACEBOOK_EMAIL", None)
    fb_password = os.getenv("FACEBOOK_PASSWORD", None)
    
    tw_username = os.getenv("TWITTER_USERNAME", None)
    tw_password = os.getenv("TWITTER_PASSWORD", None)
    
    # Test 1: Instagram
    print("\n" + "=" * 80)
    print("📸 TEST 1: Instagram Hashtag Search")
    print("=" * 80)
    if ig_username and ig_password:
        print(f"Using credentials: {ig_username[:3]}***")
    else:
        print("⚠️  No Instagram credentials - may have limited access")
    
    try:
        instagram = InstagramCrawler(username=ig_username, password=ig_password)
        results = await instagram.search_hashtag(hashtag=test_hashtag, max_posts=10)
        print(f"\n✅ Instagram Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ Instagram Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(5)
    
    # Test 2: Facebook
    print("\n" + "=" * 80)
    print("📘 TEST 2: Facebook Search")
    print("=" * 80)
    if fb_email and fb_password:
        print(f"Using credentials: {fb_email[:3]}***")
    else:
        print("⚠️  No Facebook credentials - may have limited access")
    
    try:
        facebook = FacebookCrawler(email=fb_email, password=fb_password)
        results = await facebook.search_posts(query=test_query, max_posts=10)
        print(f"\n✅ Facebook Test Complete: {len(results)} posts collected")
    except Exception as e:
        print(f"\n❌ Facebook Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(5)
    
    # Test 3: Twitter/X
    print("\n" + "=" * 80)
    print("🐦 TEST 3: Twitter/X Search")
    print("=" * 80)
    if tw_username and tw_password:
        print(f"Using credentials: {tw_username[:3]}***")
    else:
        print("⚠️  No Twitter credentials - may have limited access")
    
    try:
        twitter = TwitterCrawler(username=tw_username, password=tw_password)
        results = await twitter.search_tweets(query=test_query, max_tweets=10)
        print(f"\n✅ Twitter Test Complete: {len(results)} tweets collected")
    except Exception as e:
        print(f"\n❌ Twitter Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✓ All social media crawler tests completed!")
    print(f"→ Check data/raw/instagram/ for Instagram results")
    print(f"→ Check data/raw/facebook/ for Facebook results")
    print(f"→ Check data/raw/twitter/ for Twitter results")
    print(f"→ Check debug_*.html files for debugging")
    print()
    print("⚠️  IMPORTANT NOTES:")
    print("   • Social media platforms require login for most content")
    print("   • Set credentials via environment variables:")
    print("     export INSTAGRAM_USERNAME='your_username'")
    print("     export INSTAGRAM_PASSWORD='your_password'")
    print("     export FACEBOOK_EMAIL='your_email'")
    print("     export FACEBOOK_PASSWORD='your_password'")
    print("     export TWITTER_USERNAME='your_username'")
    print("     export TWITTER_PASSWORD='your_password'")
    print("   • Consider using official APIs for production use")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
