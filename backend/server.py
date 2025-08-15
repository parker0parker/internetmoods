from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
from collections import deque
import threading
import time
import random
import re
import statistics
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Import our custom modules
from data_collectors import (
    reddit_collector, mastodon_collector, google_trends_collector,
    youtube_collector, news_collector, twitter_collector, forums_collector
)
from advanced_sentiment import advanced_analyzer

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize sentiment analyzers
vader_analyzer = SentimentIntensityAnalyzer()

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected_connections.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

manager = ConnectionManager()

# Global variables for happiness tracking
happiness_scores = deque(maxlen=1000)  # Store more scores for better analysis
current_happiness = 50.0  # Start with neutral
total_posts_analyzed = 0
source_breakdown = {
    "reddit": 0, 
    "mastodon": 0, 
    "google_trends": 0, 
    "youtube": 0, 
    "news": 0, 
    "twitter": 0, 
    "forums": 0
}
recent_posts = []  # Store recent posts for display
geographic_data = {}  # Store geographic sentiment data
historical_data = deque(maxlen=1440)  # Store 24 hours of minute-by-minute data
country_sentiment = {}  # Store country-specific sentiment data
country_happiness_history = {}  # Store happiness timeline per country

def generate_country_sentiment(base_happiness):
    """Generate country-specific sentiment data with significant variation and track history"""
    global country_happiness_history
    
    countries = [
        # North America
        'United States', 'Canada', 'Mexico',
        
        # South America  
        'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela', 'Uruguay', 'Ecuador',
        
        # Europe
        'United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Sweden',
        'Norway', 'Finland', 'Denmark', 'Belgium', 'Switzerland', 'Austria', 'Poland',
        'Czech Republic', 'Portugal', 'Greece', 'Russia', 'Ukraine', 'Turkey',
        
        # Asia
        'China', 'Japan', 'India', 'South Korea', 'Thailand', 'Vietnam', 'Indonesia',
        'Philippines', 'Malaysia', 'Singapore', 'Taiwan', 'Bangladesh', 'Pakistan',
        'Iran', 'Saudi Arabia', 'Israel', 'UAE', 'Mongolia', 'Kazakhstan',
        
        # Africa  
        'South Africa', 'Nigeria', 'Egypt', 'Kenya', 'Morocco', 'Ghana', 'Ethiopia',
        'Tanzania', 'Algeria', 'Libya', 'Tunisia', 'Cameroon', 'Uganda', 'Zimbabwe',
        
        # Oceania
        'Australia', 'New Zealand', 'Papua New Guinea', 'Fiji',
        
        # Middle East
        'Iraq', 'Afghanistan', 'Syria', 'Jordan', 'Lebanon'
    ]
    
    country_data = {}
    
    # Create regional and cultural patterns
    country_modifiers = {
        # Nordic countries - generally happier
        'Sweden': 18, 'Norway': 20, 'Finland': 16, 'Denmark': 22,
        
        # Western Europe - generally positive
        'Netherlands': 15, 'Switzerland': 17, 'Germany': 8, 'Austria': 10,
        'Belgium': 6, 'France': 4, 'United Kingdom': 5,
        
        # North America - mixed
        'Canada': 12, 'United States': -1,
        
        # Oceania - positive
        'Australia': 11, 'New Zealand': 14, 'Fiji': 8,
        
        # East Asia - mixed with work stress
        'Japan': -8, 'South Korea': -10, 'Singapore': 2, 'Taiwan': 0,
        
        # China and neighbors
        'China': -12, 'Mongolia': -6,
        
        # Southeast Asia - generally positive
        'Thailand': 6, 'Malaysia': 4, 'Philippines': 2, 'Vietnam': -2, 'Indonesia': 0,
        
        # South Asia - challenges
        'India': -8, 'Bangladesh': -12, 'Pakistan': -15,
        
        # Middle East - significant challenges
        'UAE': 5, 'Saudi Arabia': -3, 'Israel': -2, 'Iran': -18,
        'Iraq': -25, 'Afghanistan': -30, 'Syria': -28, 'Jordan': -8, 'Lebanon': -15,
        
        # Southern Europe - mixed
        'Italy': -2, 'Spain': 1, 'Portugal': -1, 'Greece': -8,
        
        # Eastern Europe - mixed to challenging
        'Poland': -3, 'Czech Republic': 2, 'Russia': -15, 'Ukraine': -22, 'Turkey': -10,
        
        # Africa - varied
        'South Africa': -5, 'Morocco': -3, 'Egypt': -10, 'Tunisia': -6,
        'Nigeria': -8, 'Ghana': 2, 'Kenya': -4, 'Ethiopia': -12,
        'Tanzania': -6, 'Algeria': -8, 'Libya': -20, 'Zimbabwe': -18,
        'Cameroon': -7, 'Uganda': -9,
        
        # South America - mixed
        'Brazil': 3, 'Argentina': -6, 'Chile': 4, 'Colombia': -2,
        'Peru': -4, 'Venezuela': -20, 'Uruguay': 8, 'Ecuador': -3,
        
        # Small nations
        'Papua New Guinea': -8, 'Kazakhstan': -10,
        'Mexico': 0
    }
    
    for country in countries:
        base_modifier = country_modifiers.get(country, 0)
        # Add some random variation
        random_variation = random.uniform(-5, 5)
        country_happiness = max(10, min(90, base_happiness + base_modifier + random_variation))
        country_data[country] = round(country_happiness, 1)
        
        # Track happiness history per country
        if country not in country_happiness_history:
            country_happiness_history[country] = deque(maxlen=100)  # Store last 100 data points per country
        
        country_happiness_history[country].append({
            'happiness': country_happiness,
            'timestamp': datetime.utcnow().isoformat(),
            'post_count': random.randint(1, 15)  # Simulate varying post counts
        })
    
    return country_data

def clean_text(text):
    """Clean and preprocess text for sentiment analysis"""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove mentions and hashtags for cleaner analysis
    text = re.sub(r'@\w+|#\w+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# Define Models
class HappinessData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    text: str
    sentiment_score: float
    sentiment_label: str
    subreddit: str = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

def analyze_sentiment(text: str, source: str = "unknown") -> Dict[str, Any]:
    """Analyze sentiment using advanced multi-method approach"""
    return advanced_analyzer.analyze_sentiment(text, source)

def update_happiness_index(sentiment_data: Dict[str, Any], source: str, post_data: dict = None):
    """Update the global happiness index with enhanced tracking"""
    global current_happiness, total_posts_analyzed, recent_posts, historical_data, country_sentiment
    
    sentiment_score = sentiment_data.get("happiness_score", 50.0)
    
    happiness_scores.append(sentiment_score)
    source_breakdown[source] += 1
    total_posts_analyzed += 1
    
    # Add to recent posts with enhanced data
    if post_data:
        enhanced_post = {
            **post_data,
            **sentiment_data,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        recent_posts.insert(0, enhanced_post)
        recent_posts = recent_posts[:50]  # Keep more posts for analysis
    
    # Calculate rolling average
    if happiness_scores:
        current_happiness = statistics.mean(happiness_scores)
    
    # Update country sentiment data
    country_sentiment = generate_country_sentiment(current_happiness)
    
    # Update historical data (minute-by-minute)
    current_time = datetime.utcnow()
    historical_data.append({
        "timestamp": current_time.isoformat(),
        "happiness": current_happiness,
        "posts_count": total_posts_analyzed,
        "source_breakdown": source_breakdown.copy(),
        "country_sentiment": country_sentiment.copy()
    })

class RealDataStreamer:
    """Real-time data streaming from multiple sources"""
    
    def __init__(self):
        self.running = False
        
    async def stream_all_sources(self):
        """Stream data from all available sources"""
        def data_stream():
            try:
                self.running = True
                cycle_count = 0
                
                while self.running:
                    cycle_count += 1
                    print(f"Data collection cycle {cycle_count}")
                    
                    # Rotate through different data sources (7 sources now)
                    source_rotation = cycle_count % 7
                    
                    if source_rotation == 0:
                        self._collect_reddit_data()
                    elif source_rotation == 1:
                        self._collect_mastodon_data()
                    elif source_rotation == 2:
                        self._collect_trends_data()
                    elif source_rotation == 3:
                        self._collect_youtube_data()
                    elif source_rotation == 4:
                        self._collect_news_data()
                    elif source_rotation == 5:
                        self._collect_twitter_data()
                    else:
                        self._collect_forums_data()
                    
                    # Wait between collections
                    time.sleep(8)  # Collect every 8 seconds with more sources
                    
            except Exception as e:
                print(f"Data streaming error: {e}")
                
        # Run in background thread
        thread = threading.Thread(target=data_stream, daemon=True)
        thread.start()
    
    def _collect_reddit_data(self):
        """Collect real Reddit data"""
        try:
            posts = reddit_collector.get_random_posts(count=3)
            
            for post in posts:
                if not post.get('text'):
                    continue
                    
                # Analyze sentiment
                sentiment_data = analyze_sentiment(post['text'], 'reddit')
                
                # Create post data
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "reddit", 
                    "text": post['text'][:300] + "..." if len(post['text']) > 300 else post['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"], 
                    "confidence": sentiment_data["confidence"],
                    "subreddit": post.get('subreddit', 'unknown'),
                    "original_score": post.get('score', 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "url": post.get('url', '')
                }
                
                # Update global happiness index
                update_happiness_index(sentiment_data, "reddit", post_data)
                
                print(f"Reddit r/{post.get('subreddit')}: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            print(f"Reddit collection error: {e}")
    
    def _collect_mastodon_data(self):
        """Collect real Mastodon data"""
        try:
            posts = mastodon_collector.get_random_posts(count=2)
            
            for post in posts:
                if not post.get('text'):
                    continue
                    
                # Analyze sentiment  
                sentiment_data = analyze_sentiment(post['text'], 'mastodon')
                
                # Create post data
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "mastodon",
                    "text": post['text'][:300] + "..." if len(post['text']) > 300 else post['text'],
                    "sentiment_score": sentiment_data["happiness_score"], 
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "instance": post.get('instance', 'unknown'),
                    "favourites_count": post.get('favourites_count', 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "url": post.get('url', '')
                }
                
                # Update global happiness index
                update_happiness_index(sentiment_data, "mastodon", post_data)
                
                print(f"Mastodon {post.get('instance')}: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(2)  # Rate limiting for Mastodon
                
        except Exception as e:
            print(f"Mastodon collection error: {e}")
    
    def _collect_trends_data(self):
        """Collect Google Trends data"""
        try:
            trends = google_trends_collector.get_happiness_trends()
            
            for trend in trends:
                if not trend.get('text'):
                    continue
                    
                # Analyze sentiment
                sentiment_data = analyze_sentiment(trend['text'], 'google_trends')
                
                # Create post data
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "google_trends",
                    "text": trend['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "keyword": trend.get('keyword', ''),
                    "interest_level": trend.get('interest_level', 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Update global happiness index
                update_happiness_index(sentiment_data, "google_trends", post_data)
                
                print(f"Google Trends '{trend.get('keyword')}': {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
        except Exception as e:
            print(f"Google Trends collection error: {e}")
    
    def _collect_youtube_data(self):
        """Collect YouTube comments data"""
        try:
            comments = youtube_collector.get_trending_comments()
            
            for comment in comments:
                if not comment.get('text'):
                    continue
                    
                sentiment_data = analyze_sentiment(comment['text'], 'youtube')
                
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "youtube",
                    "text": comment['text'][:300] + "..." if len(comment['text']) > 300 else comment['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "video_title": comment.get('video_title', 'Unknown'),
                    "url": comment.get('url', ''),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                update_happiness_index(sentiment_data, "youtube", post_data)
                print(f"YouTube {comment.get('video_title', 'Video')}: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"YouTube collection error: {e}")
    
    def _collect_news_data(self):
        """Collect news headlines data"""
        try:
            headlines = news_collector.get_news_headlines()
            
            for headline in headlines:
                if not headline.get('text'):
                    continue
                    
                sentiment_data = analyze_sentiment(headline['text'], 'news')
                
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "news",
                    "text": headline['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "category": headline.get('category', 'general'),
                    "url": headline.get('url', ''),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                update_happiness_index(sentiment_data, "news", post_data)
                print(f"News {headline.get('category', 'General')}: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"News collection error: {e}")
    
    def _collect_twitter_data(self):
        """Collect Twitter/X data"""
        try:
            tweets = twitter_collector.get_public_tweets()
            
            for tweet in tweets:
                if not tweet.get('text'):
                    continue
                    
                sentiment_data = analyze_sentiment(tweet['text'], 'twitter')
                
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "twitter",
                    "text": tweet['text'][:300] + "..." if len(tweet['text']) > 300 else tweet['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "hashtags": tweet.get('hashtags', []),
                    "url": tweet.get('url', ''),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                update_happiness_index(sentiment_data, "twitter", post_data)
                print(f"Twitter: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(2)
                
        except Exception as e:
            print(f"Twitter collection error: {e}")
    
    def _collect_forums_data(self):
        """Collect public forums data"""
        try:
            posts = forums_collector.get_forum_posts()
            
            for post in posts:
                if not post.get('text'):
                    continue
                    
                sentiment_data = analyze_sentiment(post['text'], 'forums')
                
                post_data = {
                    "id": str(uuid.uuid4()),
                    "source": "forums",
                    "text": post['text'][:300] + "..." if len(post['text']) > 300 else post['text'],
                    "sentiment_score": sentiment_data["happiness_score"],
                    "sentiment_label": sentiment_data["label"],
                    "confidence": sentiment_data["confidence"],
                    "forum": post.get('forum', 'general'),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                update_happiness_index(sentiment_data, "forums", post_data)
                print(f"Forums {post.get('forum', 'General')}: {sentiment_data['happiness_score']:.1f}% ({sentiment_data['label']})")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"Forums collection error: {e}")
    
    def stop_streaming(self):
        """Stop the data streaming"""
        self.running = False

# Initialize data streamer
data_streamer = RealDataStreamer()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Real-time Internet Happiness Index API"}

@api_router.get("/happiness")
async def get_happiness_status():
    """Get current happiness index and statistics"""
    return {
        "current_happiness": round(current_happiness, 2),
        "total_posts_analyzed": total_posts_analyzed,
        "source_breakdown": source_breakdown,
        "happiness_trend": list(happiness_scores)[-20:],  # Last 20 scores
        "country_sentiment": country_sentiment,
        "last_updated": datetime.utcnow().isoformat()
    }

@api_router.get("/recent-posts")
async def get_recent_posts(limit: int = 20):
    """Get recent analyzed posts"""
    return recent_posts[:limit]

@api_router.post("/start-streaming")
async def start_streaming():
    """Start the multi-source data streaming"""
    await data_streamer.stream_all_sources()
    return {
        "message": "Multi-source streaming started", 
        "sources": ["reddit", "mastodon", "google_trends"],
        "collection_interval": "10 seconds"
    }

# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial happiness status
        await websocket.send_json({
            "type": "initial_status",
            "data": {
                "current_happiness": current_happiness,
                "total_analyzed": total_posts_analyzed,
                "source_breakdown": source_breakdown.copy()
            }
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Start streaming on startup"""
    global country_sentiment
    
    # Initialize country sentiment data
    country_sentiment = generate_country_sentiment(current_happiness)
    
    # Start background tasks
    asyncio.create_task(periodic_broadcast())
    await asyncio.sleep(3)  # Give server time to start
    await data_streamer.stream_all_sources()
    print("Real-time happiness index data streaming started!")

async def periodic_broadcast():
    """Periodically broadcast happiness updates"""
    while True:
        if manager.active_connections and total_posts_analyzed > 0:
            message = {
                "type": "happiness_update",
                "data": {
                    "current_happiness": current_happiness,
                    "total_analyzed": total_posts_analyzed,
                    "source_breakdown": source_breakdown.copy(),
                    "country_sentiment": country_sentiment.copy(),
                    "recent_posts": recent_posts[:8]  # Send last 8 posts
                }
            }
            await manager.broadcast(message)
        await asyncio.sleep(5)  # Broadcast every 5 seconds

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()