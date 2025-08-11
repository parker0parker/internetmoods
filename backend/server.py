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
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import statistics
from collections import deque
import threading
import time
import random

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

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

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
happiness_scores = deque(maxlen=100)  # Store last 100 scores
current_happiness = 50.0  # Start with neutral
total_posts_analyzed = 0
source_breakdown = {"reddit": 0, "mastodon": 0}
recent_posts = []  # Store recent posts for display

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

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment using VADER"""
    scores = analyzer.polarity_scores(text)
    
    # Convert compound score to happiness scale (0-100)
    happiness_score = ((scores['compound'] + 1) / 2) * 100
    
    # Determine label
    if scores['compound'] >= 0.05:
        label = "positive"
    elif scores['compound'] <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "compound": scores['compound'],
        "happiness_score": happiness_score,
        "label": label,
        "breakdown": {
            "positive": scores['pos'],
            "neutral": scores['neu'],
            "negative": scores['neg']
        }
    }

def update_happiness_index(sentiment_score: float, source: str, post_data: dict = None):
    """Update the global happiness index"""
    global current_happiness, total_posts_analyzed, recent_posts
    
    happiness_scores.append(sentiment_score)
    source_breakdown[source] += 1
    total_posts_analyzed += 1
    
    # Add to recent posts
    if post_data:
        recent_posts.insert(0, post_data)
        recent_posts = recent_posts[:20]  # Keep only last 20 posts
    
    # Calculate rolling average
    if happiness_scores:
        current_happiness = statistics.mean(happiness_scores)

class RedditStreamer:
    def __init__(self):
        # Mock Reddit data - no praw dependency
        self.mock_posts = [
            "Today I learned something amazing that made me smile!",
            "Just had the best day ever with my family.",
            "Found a $20 bill on the ground and returned it to the owner.",
            "My dog learned a new trick today and I'm so proud!",
            "Helped an elderly person cross the street today.",
            "Got a promotion at work after months of hard work!",
            "Made a new friend at the coffee shop today.",
            "Watched a beautiful sunset that took my breath away.",
            "My garden is finally blooming after weeks of care.",
            "Received an unexpected compliment that made my day."
        ]
        
    async def stream_subreddits(self, subreddits: List[str]):
        """Stream mock data from subreddits"""
        def reddit_stream():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Generate mock posts continuously
                while True:
                    for subreddit_name in subreddits:
                        try:
                            # Generate random mock post
                            mock_text = random.choice(self.mock_posts)
                            sentiment = analyze_sentiment(mock_text)
                            
                            # Create happiness data
                            happiness_data = HappinessData(
                                source="reddit",
                                text=mock_text,
                                sentiment_score=sentiment["happiness_score"],
                                sentiment_label=sentiment["label"],
                                subreddit=subreddit_name
                            )
                            
                            # Create post data
                            post_data = {
                                "id": happiness_data.id,
                                "source": happiness_data.source,
                                "text": happiness_data.text,
                                "sentiment_score": happiness_data.sentiment_score,
                                "sentiment_label": happiness_data.sentiment_label,
                                "subreddit": happiness_data.subreddit,
                                "timestamp": happiness_data.timestamp.isoformat()
                            }
                            
                            # Update global happiness index
                            update_happiness_index(sentiment["happiness_score"], "reddit", post_data)
                            
                            # Create broadcast message
                            message = {
                                "type": "new_post",
                                "data": {
                                    "id": happiness_data.id,
                                    "source": happiness_data.source,
                                    "text": happiness_data.text,
                                    "sentiment_score": happiness_data.sentiment_score,
                                    "sentiment_label": happiness_data.sentiment_label,
                                    "subreddit": happiness_data.subreddit,
                                    "timestamp": happiness_data.timestamp.isoformat(),
                                    "current_happiness": current_happiness,
                                    "total_analyzed": total_posts_analyzed,
                                    "source_breakdown": source_breakdown.copy()
                                }
                            }
                            
                            # Use synchronous approach for thread safety
                            try:
                                # Just update the global variables, websockets will be handled differently
                                print(f"New post from r/{subreddit_name}: {sentiment['happiness_score']:.1f}% happiness")
                            except Exception as e:
                                print(f"Broadcast error: {e}")
                            
                            # Store in database - simplified approach
                            try:
                                # Skip database for now, focus on real-time updates
                                pass
                            except Exception as e:
                                print(f"Database error: {e}")
                            
                            time.sleep(3)  # Rate limiting
                            
                        except Exception as e:
                            print(f"Error with subreddit {subreddit_name}: {e}")
                            
                        time.sleep(2)  # Delay between subreddits
                        
            except Exception as e:
                print(f"Reddit streaming error: {e}")
        
        # Run in thread to avoid blocking
        thread = threading.Thread(target=reddit_stream, daemon=True)
        thread.start()

# Initialize Reddit streamer
reddit_streamer = RedditStreamer()

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
        "happiness_trend": list(happiness_scores)[-10:],  # Last 10 scores
        "last_updated": datetime.utcnow().isoformat()
    }

@api_router.get("/recent-posts")
async def get_recent_posts(limit: int = 20):
    """Get recent analyzed posts"""
    return recent_posts[:limit]

@api_router.post("/start-streaming")
async def start_streaming():
    """Start the Reddit streaming"""
    subreddits = ["wholesomememes", "UpliftingNews", "happy", "MadeMeSmile", "todayilearned", "AskReddit", "funny"]
    await reddit_streamer.stream_subreddits(subreddits)
    return {"message": "Streaming started", "subreddits": subreddits}

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
    # Start background tasks
    asyncio.create_task(periodic_broadcast())
    await asyncio.sleep(2)  # Give server time to start
    subreddits = ["wholesomememes", "UpliftingNews", "happy", "MadeMeSmile", "todayilearned", "AskReddit", "funny"]
    await reddit_streamer.stream_subreddits(subreddits)

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
                    "recent_posts": recent_posts[:5]  # Send last 5 posts
                }
            }
            await manager.broadcast(message)
        await asyncio.sleep(5)  # Broadcast every 5 seconds

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()