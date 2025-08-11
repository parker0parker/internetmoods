"""
Advanced sentiment analysis combining multiple methods
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AdvancedSentimentAnalyzer:
    """Advanced sentiment analysis using multiple methods"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Enhanced keywords for context-aware analysis
        self.happiness_keywords = {
            'very_positive': ['amazing', 'fantastic', 'incredible', 'wonderful', 'perfect', 'excellent', 'outstanding', 'brilliant', 'spectacular', 'phenomenal'],
            'positive': ['good', 'great', 'nice', 'happy', 'pleased', 'satisfied', 'glad', 'thankful', 'grateful', 'excited', 'joy', 'love', 'like'],
            'negative': ['bad', 'terrible', 'awful', 'horrible', 'sad', 'angry', 'frustrated', 'disappointed', 'upset', 'annoyed', 'hate', 'dislike'],
            'very_negative': ['devastating', 'catastrophic', 'tragic', 'nightmare', 'disaster', 'horrific', 'disgusting', 'appalling', 'dreadful', 'abysmal']
        }
        
        # Context modifiers
        self.intensifiers = ['very', 'extremely', 'incredibly', 'absolutely', 'totally', 'completely', 'utterly', 'really', 'quite', 'so']
        self.negations = ['not', 'never', 'no', 'nothing', 'nobody', 'nowhere', 'neither', 'nor', "n't", 'hardly', 'scarcely', 'barely']
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags but keep the emotional context
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)  # Keep hashtag content
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze contextual clues in text"""
        text_lower = text.lower()
        
        # Count different types of sentiment words
        context_scores = {
            'very_positive': sum(1 for word in self.happiness_keywords['very_positive'] if word in text_lower),
            'positive': sum(1 for word in self.happiness_keywords['positive'] if word in text_lower),
            'negative': sum(1 for word in self.happiness_keywords['negative'] if word in text_lower),
            'very_negative': sum(1 for word in self.happiness_keywords['very_negative'] if word in text_lower)
        }
        
        # Check for intensifiers and negations
        has_intensifiers = sum(1 for word in self.intensifiers if word in text_lower)
        has_negations = sum(1 for word in self.negations if word in text_lower)
        
        return {
            'context_scores': context_scores,
            'intensifiers': has_intensifiers,
            'negations': has_negations
        }
    
    def analyze_emoji_sentiment(self, text: str) -> float:
        """Analyze emoji sentiment"""
        # Common positive and negative emojis
        positive_emojis = ['😊', '😄', '😃', '😁', '🙂', '😍', '🥰', '😘', '🤗', '🎉', '🎊', '👍', '❤️', '💕', '🌟', '✨']
        negative_emojis = ['😞', '😢', '😭', '😰', '😨', '😱', '😡', '😠', '💔', '😔', '😟', '😕', '👎', '😪', '😫', '😩']
        
        positive_count = sum(text.count(emoji) for emoji in positive_emojis)
        negative_count = sum(text.count(emoji) for emoji in negative_emojis)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def analyze_sentiment(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        """Comprehensive sentiment analysis"""
        if not text:
            return {
                "happiness_score": 50.0,
                "label": "neutral",
                "confidence": 0.0,
                "methods": {}
            }
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Method 1: VADER Analysis
        vader_scores = self.vader.polarity_scores(cleaned_text)
        vader_happiness = ((vader_scores['compound'] + 1) / 2) * 100
        
        # Method 2: TextBlob Analysis
        try:
            blob = TextBlob(cleaned_text)
            textblob_polarity = blob.sentiment.polarity  # -1 to 1
            textblob_happiness = ((textblob_polarity + 1) / 2) * 100
            textblob_subjectivity = blob.sentiment.subjectivity  # 0 to 1
        except:
            textblob_happiness = 50.0
            textblob_subjectivity = 0.5
        
        # Method 3: Context Analysis
        context_analysis = self.analyze_context(cleaned_text)
        context_scores = context_analysis['context_scores']
        
        # Calculate context-based happiness score
        context_score = (
            context_scores['very_positive'] * 2.0 +
            context_scores['positive'] * 1.0 -
            context_scores['negative'] * 1.0 -
            context_scores['very_negative'] * 2.0
        )
        
        # Adjust for negations
        if context_analysis['negations'] > 0:
            context_score *= -0.5
        
        # Adjust for intensifiers
        if context_analysis['intensifiers'] > 0:
            context_score *= 1.5
        
        # Normalize context score to 0-100 scale
        context_happiness = max(0, min(100, 50 + context_score * 10))
        
        # Method 4: Emoji Analysis
        emoji_sentiment = self.analyze_emoji_sentiment(text)
        emoji_happiness = 50 + emoji_sentiment * 50  # Scale to 0-100
        
        # Weighted combination of methods
        weights = {
            'vader': 0.4,
            'textblob': 0.3, 
            'context': 0.2,
            'emoji': 0.1
        }
        
        final_happiness = (
            weights['vader'] * vader_happiness +
            weights['textblob'] * textblob_happiness +
            weights['context'] * context_happiness +
            weights['emoji'] * emoji_happiness
        )
        
        # Determine label and confidence
        if final_happiness >= 65:
            label = "positive"
            confidence = min(1.0, (final_happiness - 50) / 50)
        elif final_happiness <= 35:
            label = "negative"
            confidence = min(1.0, (50 - final_happiness) / 50)
        else:
            label = "neutral"
            confidence = 1.0 - abs(final_happiness - 50) / 50
        
        return {
            "happiness_score": round(final_happiness, 1),
            "label": label,
            "confidence": round(confidence, 2),
            "methods": {
                "vader": round(vader_happiness, 1),
                "textblob": round(textblob_happiness, 1),
                "context": round(context_happiness, 1),
                "emoji": round(emoji_happiness, 1)
            },
            "breakdown": vader_scores,
            "subjectivity": round(textblob_subjectivity, 2),
            "text_features": {
                "length": len(text),
                "word_count": len(text.split()),
                "has_emojis": bool(emoji_sentiment != 0),
                "context_words": sum(context_scores.values())
            }
        }

# Initialize the advanced analyzer
advanced_analyzer = AdvancedSentimentAnalyzer()