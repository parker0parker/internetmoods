#!/usr/bin/env python3
"""
Reddit Collector Test Suite
Tests the Reddit data collection fix with fallback system
"""

import sys
import os
sys.path.append('/app/backend')

from data_collectors import reddit_collector
import time
import json

def test_reddit_collector():
    """Test Reddit collector with fallback system"""
    print("🔍 Testing Reddit Collector with Fallback System")
    print("=" * 60)
    
    # Test 1: Get random posts (should work with fallback)
    print("\n--- Test 1: Reddit get_random_posts ---")
    try:
        posts = reddit_collector.get_random_posts(count=5)
        
        if not posts:
            print("❌ FAIL: No posts returned")
            return False
        
        print(f"✅ SUCCESS: Retrieved {len(posts)} posts")
        
        # Validate post structure
        for i, post in enumerate(posts):
            required_fields = ['id', 'title', 'text', 'subreddit', 'score', 'created_utc', 'num_comments', 'url']
            missing_fields = [field for field in required_fields if field not in post]
            
            if missing_fields:
                print(f"❌ FAIL: Post {i+1} missing fields: {missing_fields}")
                return False
            
            # Validate field types and values
            if not isinstance(post['score'], int) or post['score'] < 0:
                print(f"❌ FAIL: Post {i+1} invalid score: {post['score']}")
                return False
            
            if not isinstance(post['text'], str) or len(post['text']) < 10:
                print(f"❌ FAIL: Post {i+1} invalid text length: {len(post['text'])}")
                return False
            
            if not isinstance(post['subreddit'], str) or not post['subreddit']:
                print(f"❌ FAIL: Post {i+1} invalid subreddit: {post['subreddit']}")
                return False
            
            print(f"  Post {i+1}: r/{post['subreddit']} - {post['title'][:50]}...")
        
        print("✅ SUCCESS: All posts have correct structure")
        
    except Exception as e:
        print(f"❌ FAIL: Exception in get_random_posts: {e}")
        return False
    
    # Test 2: Test fallback posts directly
    print("\n--- Test 2: Reddit fallback posts ---")
    try:
        fallback_posts = reddit_collector._get_fallback_posts()
        
        if not fallback_posts:
            print("❌ FAIL: No fallback posts returned")
            return False
        
        print(f"✅ SUCCESS: Retrieved {len(fallback_posts)} fallback posts")
        
        # Check subreddit diversity in fallback
        subreddits = set(post['subreddit'] for post in fallback_posts)
        expected_subreddits = {'wholesomememes', 'UpliftingNews', 'MadeMeSmile', 'AskReddit', 'todayilearned', 'funny', 'HumansBeingBros', 'GetMotivated', 'aww'}
        
        found_expected = subreddits.intersection(expected_subreddits)
        if len(found_expected) >= 3:
            print(f"✅ SUCCESS: Fallback posts from {len(found_expected)} expected subreddits: {found_expected}")
        else:
            print(f"❌ FAIL: Only {len(found_expected)} expected subreddits in fallback: {found_expected}")
            return False
        
        # Test realistic content
        for post in fallback_posts[:3]:  # Check first 3
            if 'reddit_fb_' not in post['id']:
                print(f"❌ FAIL: Fallback post ID doesn't have correct prefix: {post['id']}")
                return False
            
            if len(post['text']) < 20:
                print(f"❌ FAIL: Fallback post text too short: {post['text']}")
                return False
            
            print(f"  Fallback: r/{post['subreddit']} - {post['text'][:60]}...")
        
        print("✅ SUCCESS: Fallback posts have realistic content")
        
    except Exception as e:
        print(f"❌ FAIL: Exception in fallback posts: {e}")
        return False
    
    # Test 3: Test multiple calls for consistency
    print("\n--- Test 3: Multiple calls consistency ---")
    try:
        posts1 = reddit_collector.get_random_posts(count=3)
        time.sleep(1)
        posts2 = reddit_collector.get_random_posts(count=3)
        
        if not posts1 or not posts2:
            print("❌ FAIL: One of the calls returned no posts")
            return False
        
        # Should get different posts (due to randomization)
        ids1 = set(post['id'] for post in posts1)
        ids2 = set(post['id'] for post in posts2)
        
        if len(ids1.intersection(ids2)) == len(ids1):
            print("⚠️  WARNING: Got identical posts in both calls (may be expected with fallback)")
        else:
            print("✅ SUCCESS: Got different posts in multiple calls")
        
        print(f"✅ SUCCESS: Multiple calls working consistently")
        
    except Exception as e:
        print(f"❌ FAIL: Exception in multiple calls: {e}")
        return False
    
    return True

def test_reddit_integration():
    """Test Reddit integration with sentiment analysis"""
    print("\n🔗 Testing Reddit Integration with Sentiment Analysis")
    print("=" * 60)
    
    try:
        # Import sentiment analyzer
        sys.path.append('/app/backend')
        from advanced_sentiment import advanced_analyzer
        
        # Get Reddit posts
        posts = reddit_collector.get_random_posts(count=3)
        
        if not posts:
            print("❌ FAIL: No posts for sentiment analysis")
            return False
        
        print(f"✅ SUCCESS: Got {len(posts)} posts for sentiment analysis")
        
        # Analyze sentiment for each post
        for i, post in enumerate(posts):
            try:
                sentiment_data = advanced_analyzer.analyze_sentiment(post['text'], 'reddit')
                
                # Validate sentiment data structure
                required_fields = ['happiness_score', 'label', 'confidence']
                missing_fields = [field for field in required_fields if field not in sentiment_data]
                
                if missing_fields:
                    print(f"❌ FAIL: Post {i+1} sentiment missing fields: {missing_fields}")
                    return False
                
                # Validate ranges
                happiness_score = sentiment_data['happiness_score']
                confidence = sentiment_data['confidence']
                label = sentiment_data['label']
                
                if not (0 <= happiness_score <= 100):
                    print(f"❌ FAIL: Post {i+1} happiness score out of range: {happiness_score}")
                    return False
                
                if not (0 <= confidence <= 1):
                    print(f"❌ FAIL: Post {i+1} confidence out of range: {confidence}")
                    return False
                
                if label not in ['positive', 'negative', 'neutral']:
                    print(f"❌ FAIL: Post {i+1} invalid label: {label}")
                    return False
                
                print(f"  Post {i+1}: r/{post['subreddit']} - {happiness_score:.1f}% ({label})")
                
            except Exception as e:
                print(f"❌ FAIL: Sentiment analysis error for post {i+1}: {e}")
                return False
        
        print("✅ SUCCESS: Sentiment analysis working with Reddit posts")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Integration test exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Reddit Collector Tests")
    
    success1 = test_reddit_collector()
    success2 = test_reddit_integration()
    
    print("\n" + "=" * 60)
    print("🏁 REDDIT COLLECTOR TEST SUMMARY")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 All Reddit collector tests passed!")
        print("✅ Reddit fallback system is working correctly")
        print("✅ Sentiment analysis integration is working")
        exit(0)
    else:
        print("⚠️  Some Reddit collector tests failed")
        if not success1:
            print("❌ Reddit collector tests failed")
        if not success2:
            print("❌ Reddit integration tests failed")
        exit(1)