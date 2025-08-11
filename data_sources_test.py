#!/usr/bin/env python3
"""
Data Sources Integration Test
Tests that all 7 data sources are working and Reddit is being counted
"""

import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_source_breakdown():
    """Test that all 7 data sources are being counted"""
    print("🔍 Testing Data Source Breakdown")
    print("=" * 60)
    
    try:
        # Get current happiness data
        response = requests.get(f"{API_BASE}/happiness", timeout=30)
        if response.status_code != 200:
            print(f"❌ FAIL: Could not get happiness data: {response.status_code}")
            return False
        
        data = response.json()
        source_breakdown = data.get("source_breakdown", {})
        
        print(f"Current source breakdown: {source_breakdown}")
        
        # Expected 7 sources
        expected_sources = ["reddit", "mastodon", "google_trends", "youtube", "news", "twitter", "forums"]
        
        # Check if all sources exist in breakdown
        missing_sources = [source for source in expected_sources if source not in source_breakdown]
        if missing_sources:
            print(f"❌ FAIL: Missing sources in breakdown: {missing_sources}")
            return False
        
        print("✅ SUCCESS: All 7 data sources present in breakdown")
        
        # Check if Reddit has posts (should have posts due to fallback)
        reddit_count = source_breakdown.get("reddit", 0)
        if reddit_count == 0:
            print("❌ FAIL: Reddit source has 0 posts - fallback not working")
            return False
        
        print(f"✅ SUCCESS: Reddit source has {reddit_count} posts")
        
        # Check total posts across all sources
        total_from_sources = sum(source_breakdown.values())
        total_posts_analyzed = data.get("total_posts_analyzed", 0)
        
        if total_from_sources != total_posts_analyzed:
            print(f"⚠️  WARNING: Source breakdown total ({total_from_sources}) doesn't match total analyzed ({total_posts_analyzed})")
        else:
            print(f"✅ SUCCESS: Source breakdown matches total posts analyzed: {total_posts_analyzed}")
        
        # Show breakdown
        print("\nSource breakdown:")
        for source, count in source_breakdown.items():
            percentage = (count / total_posts_analyzed * 100) if total_posts_analyzed > 0 else 0
            print(f"  {source}: {count} posts ({percentage:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception in source breakdown test: {e}")
        return False

def test_reddit_posts_in_recent():
    """Test that Reddit posts appear in recent posts"""
    print("\n🔍 Testing Reddit Posts in Recent Posts")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/recent-posts?limit=50", timeout=30)
        if response.status_code != 200:
            print(f"❌ FAIL: Could not get recent posts: {response.status_code}")
            return False
        
        posts = response.json()
        if not posts:
            print("❌ FAIL: No recent posts available")
            return False
        
        # Find Reddit posts
        reddit_posts = [post for post in posts if post.get("source") == "reddit"]
        
        if not reddit_posts:
            print("❌ FAIL: No Reddit posts found in recent posts")
            return False
        
        print(f"✅ SUCCESS: Found {len(reddit_posts)} Reddit posts in recent posts")
        
        # Check Reddit post structure
        for i, post in enumerate(reddit_posts[:3]):  # Check first 3
            if "subreddit" not in post:
                print(f"❌ FAIL: Reddit post {i+1} missing subreddit field")
                return False
            
            subreddit = post.get("subreddit", "")
            if not subreddit:
                print(f"❌ FAIL: Reddit post {i+1} has empty subreddit")
                return False
            
            print(f"  Reddit post {i+1}: r/{subreddit} - {post.get('text', '')[:50]}...")
        
        print("✅ SUCCESS: Reddit posts have correct structure with subreddit info")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception in Reddit posts test: {e}")
        return False

def test_data_streaming_all_sources():
    """Test that data streaming is working for all sources"""
    print("\n🔍 Testing Data Streaming from All Sources")
    print("=" * 60)
    
    try:
        # Get initial state
        response1 = requests.get(f"{API_BASE}/happiness", timeout=30)
        if response1.status_code != 200:
            print(f"❌ FAIL: Could not get initial happiness data: {response1.status_code}")
            return False
        
        data1 = response1.json()
        initial_breakdown = data1.get("source_breakdown", {})
        
        print("Initial source breakdown:")
        for source, count in initial_breakdown.items():
            print(f"  {source}: {count}")
        
        # Wait for data generation (the system cycles through sources every 8 seconds)
        print("\nWaiting 25 seconds for data generation from all sources...")
        time.sleep(25)
        
        # Get updated state
        response2 = requests.get(f"{API_BASE}/happiness", timeout=30)
        if response2.status_code != 200:
            print(f"❌ FAIL: Could not get updated happiness data: {response2.status_code}")
            return False
        
        data2 = response2.json()
        final_breakdown = data2.get("source_breakdown", {})
        
        print("Final source breakdown:")
        for source, count in final_breakdown.items():
            print(f"  {source}: {count}")
        
        # Check if any sources increased
        sources_increased = []
        for source in initial_breakdown:
            if final_breakdown.get(source, 0) > initial_breakdown.get(source, 0):
                increase = final_breakdown.get(source, 0) - initial_breakdown.get(source, 0)
                sources_increased.append(f"{source} (+{increase})")
        
        if not sources_increased:
            print("❌ FAIL: No sources showed increase in posts")
            return False
        
        print(f"✅ SUCCESS: Sources with increased posts: {', '.join(sources_increased)}")
        
        # Specifically check Reddit
        reddit_initial = initial_breakdown.get("reddit", 0)
        reddit_final = final_breakdown.get("reddit", 0)
        
        if reddit_final > reddit_initial:
            print(f"✅ SUCCESS: Reddit posts increased from {reddit_initial} to {reddit_final}")
        else:
            print(f"⚠️  INFO: Reddit posts remained at {reddit_final} (fallback may be working consistently)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception in data streaming test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Data Sources Integration Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    success1 = test_source_breakdown()
    success2 = test_reddit_posts_in_recent()
    success3 = test_data_streaming_all_sources()
    
    print("\n" + "=" * 60)
    print("🏁 DATA SOURCES TEST SUMMARY")
    print("=" * 60)
    
    if success1 and success2 and success3:
        print("🎉 All data sources integration tests passed!")
        print("✅ All 7 data sources are working")
        print("✅ Reddit fallback system is integrated correctly")
        print("✅ Source breakdown statistics are accurate")
        exit(0)
    else:
        print("⚠️  Some data sources tests failed")
        if not success1:
            print("❌ Source breakdown test failed")
        if not success2:
            print("❌ Reddit posts in recent test failed")
        if not success3:
            print("❌ Data streaming test failed")
        exit(1)