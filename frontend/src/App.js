import { useEffect, useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

const HappinessGauge = ({ happiness }) => {
  const getColor = (score) => {
    if (score >= 75) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    if (score >= 45) return "text-orange-400";
    return "text-red-400";
  };

  const getMood = (score) => {
    if (score >= 80) return "😊 Very Happy";
    if (score >= 65) return "🙂 Happy";
    if (score >= 55) return "😐 Neutral";
    if (score >= 40) return "😕 Sad";
    return "😞 Very Sad";
  };

  return (
    <div className="happiness-gauge">
      <div className="gauge-container">
        <div className="gauge-background">
          <div 
            className="gauge-fill"
            style={{ width: `${happiness}%` }}
          ></div>
        </div>
        <div className={`happiness-score ${getColor(happiness)}`}>
          {happiness.toFixed(1)}%
        </div>
      </div>
      <div className="mood-indicator">
        {getMood(happiness)}
      </div>
    </div>
  );
};

const PostCard = ({ post }) => {
  const getSentimentColor = (label) => {
    switch(label) {
      case 'positive': return 'border-green-400 bg-green-50';
      case 'negative': return 'border-red-400 bg-red-50';  
      default: return 'border-gray-400 bg-gray-50';
    }
  };

  const getSentimentEmoji = (label) => {
    switch(label) {
      case 'positive': return '😊';
      case 'negative': return '😢';
      default: return '😐';
    }
  };

  const getSourceIcon = (source) => {
    switch(source) {
      case 'reddit': return '🤖';
      case 'mastodon': return '🐘'; 
      case 'google_trends': return '📊';
      default: return '🌐';
    }
  };

  const getSourceLabel = (post) => {
    if (post.source === 'reddit' && post.subreddit) {
      return `r/${post.subreddit}`;
    } else if (post.source === 'mastodon' && post.instance) {
      return `${post.instance}`;
    } else if (post.source === 'google_trends' && post.keyword) {
      return `Trends: ${post.keyword}`;
    }
    return post.source;
  };

  return (
    <div className={`post-card ${getSentimentColor(post.sentiment_label)}`}>
      <div className="post-header">
        <span className="post-source">
          {getSourceIcon(post.source)} {getSourceLabel(post)}
        </span>
        <div className="sentiment-info">
          <span className="sentiment-badge">
            {getSentimentEmoji(post.sentiment_label)} {post.sentiment_score.toFixed(1)}%
          </span>
          {post.confidence && (
            <span className="confidence-badge">
              {(post.confidence * 100).toFixed(0)}% confidence
            </span>
          )}
        </div>
      </div>
      <p className="post-text">{post.text}</p>
      <div className="post-footer">
        <div className="post-time">
          {new Date(post.timestamp).toLocaleTimeString()}
        </div>
        {post.methods && (
          <div className="analysis-methods">
            <span title={`VADER: ${post.methods.vader}%, TextBlob: ${post.methods.textblob}%`}>
              📊 Multi-method analysis
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, subtitle, icon }) => (
  <div className="stat-card">
    <div className="stat-icon">{icon}</div>
    <div className="stat-content">
      <h3 className="stat-title">{title}</h3>
      <p className="stat-value">{value}</p>
      <p className="stat-subtitle">{subtitle}</p>
    </div>
  </div>
);

const SourceBreakdown = ({ sourceData }) => {
  const total = Object.values(sourceData).reduce((sum, count) => sum + count, 0);
  
  if (total === 0) return null;

  return (
    <div className="source-breakdown">
      <h3 className="breakdown-title">Data Sources</h3>
      <div className="breakdown-items">
        {Object.entries(sourceData).map(([source, count]) => (
          <div key={source} className="breakdown-item">
            <div className="source-info">
              <span className="source-icon">
                {source === 'reddit' ? '🤖' : source === 'mastodon' ? '🐘' : '📊'}
              </span>
              <span className="source-name">
                {source.charAt(0).toUpperCase() + source.slice(1).replace('_', ' ')}
              </span>
            </div>
            <div className="source-stats">
              <span className="count">{count.toLocaleString()}</span>
              <span className="percentage">
                ({((count / total) * 100).toFixed(1)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SentimentDistribution = ({ posts }) => {
  const distribution = posts.reduce((acc, post) => {
    acc[post.sentiment_label] = (acc[post.sentiment_label] || 0) + 1;
    return acc;
  }, {});

  const total = posts.length;
  if (total === 0) return null;

  return (
    <div className="sentiment-distribution">
      <h3 className="distribution-title">Sentiment Distribution</h3>
      <div className="distribution-bars">
        {['positive', 'neutral', 'negative'].map(sentiment => {
          const count = distribution[sentiment] || 0;
          const percentage = (count / total) * 100;
          const color = sentiment === 'positive' ? '#22c55e' : 
                       sentiment === 'negative' ? '#ef4444' : '#9ca3af';
          
          return (
            <div key={sentiment} className="distribution-bar">
              <div className="bar-label">
                <span>{sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}</span>
                <span>{count} ({percentage.toFixed(1)}%)</span>
              </div>
              <div className="bar-container">
                <div 
                  className="bar-fill"
                  style={{ width: `${percentage}%`, backgroundColor: color }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const RealTimeStats = ({ data }) => {
  const [timeElapsed, setTimeElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  return (
    <div className="realtime-stats">
      <div className="stats-row">
        <div className="stat-item">
          <span className="stat-label">Uptime</span>
          <span className="stat-value">{formatTime(timeElapsed)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Rate</span>
          <span className="stat-value">~{(data.total_posts_analyzed / Math.max(timeElapsed / 60, 1)).toFixed(1)}/min</span>
        </div>
      </div>
    </div>
  );
};

const TrendChart = ({ scores }) => {
  const max = Math.max(...scores, 50);
  const min = Math.min(...scores, 50);
  const range = max - min || 1;

  return (
    <div className="trend-chart">
      <h3 className="trend-title">Happiness Trend</h3>
      <div className="chart-container">
        <svg viewBox="0 0 300 100" className="trend-svg">
          <polyline
            points={scores.map((score, index) => 
              `${(index / (scores.length - 1)) * 280 + 10},${90 - ((score - min) / range) * 80}`
            ).join(' ')}
            className="trend-line"
          />
          {scores.map((score, index) => (
            <circle
              key={index}
              cx={(index / (scores.length - 1)) * 280 + 10}
              cy={90 - ((score - min) / range) * 80}
              r="2"
              className="trend-point"
            />
          ))}
        </svg>
      </div>
    </div>
  );
};

function App() {
  const [happinessData, setHappinessData] = useState({
    current_happiness: 50,
    total_posts_analyzed: 0,
    source_breakdown: { reddit: 0, mastodon: 0 },
    happiness_trend: []
  });
  const [recentPosts, setRecentPosts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    // Fetch initial data
    const fetchInitialData = async () => {
      try {
        const response = await axios.get(`${API}/happiness`);
        setHappinessData(response.data);
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };

    fetchInitialData();

    // Setup WebSocket connection
    const websocket = new WebSocket(`${WS_URL}/api/ws`);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'new_post') {
        // Update happiness data
        setHappinessData(prev => ({
          ...prev,
          current_happiness: message.data.current_happiness,
          total_posts_analyzed: message.data.total_analyzed,
          source_breakdown: message.data.source_breakdown,
          happiness_trend: prev.happiness_trend.slice(-9).concat([message.data.current_happiness])
        }));
        
        // Add new post to recent posts
        setRecentPosts(prev => [message.data, ...prev.slice(0, 19)]);
      } else if (message.type === 'happiness_update') {
        // Update happiness data from periodic broadcast
        setHappinessData(prev => ({
          ...prev,
          current_happiness: message.data.current_happiness,
          total_posts_analyzed: message.data.total_analyzed,
          source_breakdown: message.data.source_breakdown,
          happiness_trend: prev.happiness_trend.slice(-9).concat([message.data.current_happiness])
        }));
        
        // Update recent posts if provided
        if (message.data.recent_posts) {
          setRecentPosts(message.data.recent_posts);
        }
      } else if (message.type === 'initial_status') {
        setHappinessData(prev => ({
          ...prev,
          current_happiness: message.data.current_happiness,
          total_posts_analyzed: message.data.total_analyzed,
          source_breakdown: message.data.source_breakdown
        }));
      }
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      websocket.close();
    };
  }, []);

  const startStreaming = async () => {
    try {
      await axios.post(`${API}/start-streaming`);
    } catch (error) {
      console.error('Error starting streaming:', error);
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1 className="main-title">🌐 Internet Happiness Index</h1>
        <p className="subtitle">Real-time sentiment analysis of social media and news</p>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Live' : '🔴 Disconnected'}
        </div>
      </div>

      <div className="dashboard">
        <div className="main-gauge-section">
          <HappinessGauge happiness={happinessData.current_happiness} />
        </div>

        <div className="stats-grid">
          <StatCard 
            title="Posts Analyzed"
            value={happinessData.total_posts_analyzed.toLocaleString()}
            subtitle="Total processed"
            icon="📊"
          />
          <StatCard 
            title="Reddit Posts"
            value={happinessData.source_breakdown.reddit.toLocaleString()}
            subtitle="From subreddits"
            icon="🤖"
          />
          <StatCard 
            title="Mastodon Posts"
            value={happinessData.source_breakdown.mastodon.toLocaleString()}
            subtitle="From instances"
            icon="🐘"
          />
          <StatCard 
            title="Trends Data"
            value={happinessData.source_breakdown.google_trends.toLocaleString()}
            subtitle="From Google Trends"
            icon="📈"
          />
        </div>

        <div className="analytics-section">
          <SourceBreakdown sourceData={happinessData.source_breakdown} />
          <SentimentDistribution posts={recentPosts} />
        </div>

        <RealTimeStats data={happinessData} />

        {happinessData.happiness_trend.length > 0 && (
          <div className="trend-section">
            <TrendChart scores={happinessData.happiness_trend} />
          </div>
        )}

        <div className="posts-section">
          <div className="section-header">
            <h2>Recent Posts</h2>
            <button onClick={startStreaming} className="refresh-btn">
              🔄 Refresh Stream
            </button>
          </div>
          
          <div className="posts-grid">
            {recentPosts.map((post, index) => (
              <PostCard key={`${post.id}-${index}`} post={post} />
            ))}
          </div>
          
          {recentPosts.length === 0 && (
            <div className="empty-state">
              <p>🔍 Waiting for new posts...</p>
              <button onClick={startStreaming} className="start-btn">
                Start Analyzing Posts
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;