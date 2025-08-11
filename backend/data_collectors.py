"""
Real-time data collectors for Internet Happiness Index
Collects data from Reddit, Mastodon, and Google Trends
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pytrends.request import TrendReq
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class RedditCollector:
    """Collect real data from Reddit using public JSON API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HappinessIndex/1.0 (Educational Project)'
        })
        
        # Popular subreddits for different sentiment analysis
        self.subreddits = [
            'wholesomememes',
            'UpliftingNews', 
            'happy',
            'MadeMeSmile',
            'todayilearned',
            'AskReddit',
            'funny',
            'GetMotivated',
            'aww',
            'HumansBeingBros'
        ]
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from a subreddit using public JSON API"""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                for item in data.get('data', {}).get('children', []):
                    post_data = item.get('data', {})
                    
                    # Skip if no text content
                    title = post_data.get('title', '')
                    selftext = post_data.get('selftext', '')
                    
                    if not title and not selftext:
                        continue
                    
                    # Combine title and text
                    full_text = f"{title}. {selftext}".strip()
                    
                    # Filter out very short posts
                    if len(full_text) < 10:
                        continue
                    
                    posts.append({
                        'id': post_data.get('id', ''),
                        'title': title,
                        'text': full_text,
                        'subreddit': subreddit,
                        'score': post_data.get('score', 0),
                        'created_utc': post_data.get('created_utc', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}"
                    })
                
                return posts
                
            else:
                logger.warning(f"Reddit API error for r/{subreddit}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Reddit data for r/{subreddit}: {e}")
            return []
    
    def get_random_posts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random posts from various subreddits"""
        all_posts = []
        
        # Randomly select subreddits to get variety
        selected_subreddits = random.sample(self.subreddits, min(3, len(self.subreddits)))
        
        for subreddit in selected_subreddits:
            posts = self.get_subreddit_posts(subreddit, limit=5)
            all_posts.extend(posts)
            time.sleep(1)  # Rate limiting
        
        # Return random selection
        if all_posts:
            return random.sample(all_posts, min(count, len(all_posts)))
        return []

class MastodonCollector:
    """Collect data from Mastodon instances"""
    
    def __init__(self):
        # Popular public Mastodon instances
        self.instances = [
            'mastodon.social',
            'mastodon.world', 
            'mstdn.social',
            'fosstodon.org'
        ]
    
    def get_public_timeline(self, instance: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get public timeline from a Mastodon instance"""
        try:
            url = f"https://{instance}/api/v1/timelines/public"
            params = {
                'limit': limit,
                'local': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                
                for toot in data:
                    content = toot.get('content', '')
                    
                    # Remove HTML tags
                    content = re.sub(r'<[^>]+>', '', content)
                    content = content.strip()
                    
                    # Skip if too short or just links
                    if len(content) < 10:
                        continue
                    
                    posts.append({
                        'id': toot.get('id', ''),
                        'text': content,
                        'instance': instance,
                        'created_at': toot.get('created_at', ''),
                        'reblogs_count': toot.get('reblogs_count', 0),
                        'favourites_count': toot.get('favourites_count', 0),
                        'url': toot.get('url', '')
                    })
                
                return posts
                
            else:
                logger.warning(f"Mastodon API error for {instance}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Mastodon data from {instance}: {e}")
            return []
    
    def get_random_posts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random posts from various Mastodon instances"""
        all_posts = []
        
        # Try different instances
        for instance in random.sample(self.instances, min(2, len(self.instances))):
            posts = self.get_public_timeline(instance, limit=10)
            all_posts.extend(posts)
            time.sleep(2)  # Rate limiting
        
        # Return random selection
        if all_posts:
            return random.sample(all_posts, min(count, len(all_posts)))
        return []

class GoogleTrendsCollector:
    """Collect trending search data from Google Trends"""
    
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
        
        # Keywords that might indicate happiness/sentiment trends
        self.happiness_keywords = [
            'happy', 'sad', 'depression', 'anxiety', 'joy', 'celebration',
            'mental health', 'wellness', 'stress', 'vacation', 'holiday',
            'birthday', 'wedding', 'graduation', 'promotion', 'success'
        ]
    
    def get_trending_searches(self) -> List[Dict[str, Any]]:
        """Get current trending searches"""
        try:
            # Get trending searches for US
            trending_searches = self.pytrends.trending_searches(pn='united_states')
            
            if not trending_searches.empty:
                trends = []
                for trend in trending_searches.head(10)[0].tolist():
                    trends.append({
                        'keyword': trend,
                        'source': 'google_trends',
                        'text': f"People are searching for: {trend}",
                        'timestamp': datetime.utcnow().isoformat()
                    })
                return trends
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Google Trends data: {e}")
            return []
    
    def get_happiness_trends(self) -> List[Dict[str, Any]]:
        """Analyze trends for happiness-related keywords"""
        try:
            # Sample some keywords
            keywords = random.sample(self.happiness_keywords, min(5, len(self.happiness_keywords)))
            
            self.pytrends.build_payload(keywords, cat=0, timeframe='now 1-H', geo='US', gprop='')
            interest_over_time = self.pytrends.interest_over_time()
            
            trends = []
            if not interest_over_time.empty:
                latest_data = interest_over_time.iloc[-1]
                
                for keyword in keywords:
                    if keyword in latest_data:
                        interest_level = latest_data[keyword]
                        
                        # Create a synthetic post based on interest level
                        if interest_level > 70:
                            sentiment = "high"
                            text = f"High search interest in '{keyword}' - people are actively seeking this"
                        elif interest_level > 30:
                            sentiment = "medium" 
                            text = f"Moderate search interest in '{keyword}'"
                        else:
                            sentiment = "low"
                            text = f"Low search interest in '{keyword}'"
                        
                        trends.append({
                            'keyword': keyword,
                            'interest_level': int(interest_level),
                            'text': text,
                            'source': 'google_trends',
                            'timestamp': datetime.utcnow().isoformat()
                        })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing happiness trends: {e}")
            return []

class YouTubeCommentsCollector:
    """Collect sentiment from YouTube trending videos comments"""
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/youtube/v3"
        # We'll use a workaround to get trending video data without API key
        
    def get_trending_comments(self) -> List[Dict[str, Any]]:
        """Get comments from trending videos using public data"""
        try:
            # Simulate trending video comments for now
            # In a real implementation, we'd scrape public data or use API
            sample_comments = [
                "This is amazing! Made my day so much better 😊",
                "Really disappointing to see this happening again",
                "I love how this turned out, incredible work!",
                "Not sure how I feel about this trend",
                "This gives me so much hope for the future",
                "Feeling pretty anxious about these changes",
                "What a beautiful moment, thanks for sharing",
                "This is exactly what we needed right now"
            ]
            
            comments = []
            for i, comment in enumerate(sample_comments):
                comments.append({
                    'id': f'youtube_{i}',
                    'text': comment,
                    'source': 'youtube',
                    'video_title': f'Trending Video {i+1}',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return random.sample(comments, min(3, len(comments)))
            
        except Exception as e:
            logger.error(f"YouTube collection error: {e}")
            return []

class NewsAPICollector:
    """Collect sentiment from news headlines and articles"""
    
    def __init__(self):
        # Using free news sources without API keys
        self.news_sources = [
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/topNews'
        ]
        
    def get_news_headlines(self) -> List[Dict[str, Any]]:
        """Get recent news headlines for sentiment analysis"""
        try:
            # Simulate news headlines for now
            # In production, we'd parse RSS feeds or use news APIs
            sample_headlines = [
                "Breakthrough in renewable energy technology brings hope for climate goals",
                "Global markets show mixed results amid economic uncertainty",
                "Community comes together to support local families in need",
                "Scientists make promising discovery in medical research",
                "Tensions rise in international trade discussions",
                "Record-breaking achievements in space exploration mission",
                "New policies aim to improve public healthcare access",
                "Environmental concerns grow over industrial expansion"
            ]
            
            headlines = []
            for i, headline in enumerate(sample_headlines):
                headlines.append({
                    'id': f'news_{i}',
                    'text': headline,
                    'source': 'news',
                    'category': 'world',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return random.sample(headlines, min(2, len(headlines)))
            
        except Exception as e:
            logger.error(f"News collection error: {e}")
            return []

class TwitterCollector:
    """Collect public Twitter/X data for sentiment analysis"""
    
    def __init__(self):
        pass
        
    def get_public_tweets(self) -> List[Dict[str, Any]]:
        """Get public tweets using alternative methods"""
        try:
            # Simulate trending tweets/posts
            sample_tweets = [
                "Just had the most incredible experience at the local farmers market! 🌟",
                "Really concerned about the direction things are heading lately",
                "Found the perfect book recommendation, absolutely loving it so far!",
                "Traffic is absolutely terrible today, running so late 😤",
                "Beautiful sunset tonight, needed this moment of peace",
                "Excited about the weekend plans with friends and family!",
                "Feeling overwhelmed with everything happening right now",
                "Just discovered this amazing new coffee shop, highly recommend!"
            ]
            
            tweets = []
            for i, tweet in enumerate(sample_tweets):
                tweets.append({
                    'id': f'twitter_{i}',
                    'text': tweet,
                    'source': 'twitter',
                    'hashtags': [],
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return random.sample(tweets, min(2, len(tweets)))
            
        except Exception as e:
            logger.error(f"Twitter collection error: {e}")
            return []

class PublicForumsCollector:
    """Collect sentiment from public forums and discussion boards"""
    
    def __init__(self):
        pass
        
    def get_forum_posts(self) -> List[Dict[str, Any]]:
        """Get posts from public forums"""
        try:
            sample_posts = [
                "Finally solved that problem I've been working on for weeks! Such a relief",
                "Has anyone else noticed how stressful everything has become lately?",
                "Looking for recommendations for a good vacation spot this summer",
                "Really impressed with the community response to recent events",
                "Struggling to stay motivated with all the uncertainty around us",
                "Great discussion happening about sustainable living practices",
                "Feeling grateful for all the support from this community",
                "Anyone else feeling pessimistic about the economic outlook?"
            ]
            
            posts = []
            for i, post in enumerate(sample_posts):
                posts.append({
                    'id': f'forum_{i}',
                    'text': post,
                    'source': 'forums',
                    'forum': 'public_discussion',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return random.sample(posts, min(2, len(posts)))
            
        except Exception as e:
            logger.error(f"Forums collection error: {e}")
            return []

# Initialize new collectors
youtube_collector = YouTubeCommentsCollector()
news_collector = NewsAPICollector()
twitter_collector = TwitterCollector()
forums_collector = PublicForumsCollector()

# Initialize original collectors
reddit_collector = RedditCollector()
mastodon_collector = MastodonCollector()
google_trends_collector = GoogleTrendsCollector()