import React, { useEffect, useState, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Text, Float, MeshTransmissionMaterial } from "@react-three/drei";
import * as THREE from "three";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// 3D Wireframe Globe with Country Sentiment and Hover Tooltips
const WireframeGlobe = ({ happiness, countrySentiment }) => {
  const meshRef = useRef();
  const groupRef = useRef();
  const linesRef = useRef();
  
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1;
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.05) * 0.1;
    }
  });

  const getSentimentColor = (sentiment) => {
    if (sentiment >= 70) return '#00ff88'; // Very happy - bright green
    if (sentiment >= 60) return '#44ff66'; // Happy - green
    if (sentiment >= 50) return '#ffaa00'; // Neutral - orange
    if (sentiment >= 40) return '#ff6644'; // Sad - red-orange
    return '#ff4466'; // Very sad - red
  };

  const getSentimentText = (sentiment) => {
    if (sentiment >= 95) return 'ecstatic';
    if (sentiment >= 90) return 'euphoric';
    if (sentiment >= 85) return 'elated';
    if (sentiment >= 80) return 'jubilant';
    if (sentiment >= 75) return 'joyful';
    if (sentiment >= 70) return 'cheerful';
    if (sentiment >= 65) return 'upbeat';
    if (sentiment >= 60) return 'optimistic';
    if (sentiment >= 55) return 'content';
    if (sentiment >= 50) return 'neutral';
    if (sentiment >= 45) return 'subdued';
    if (sentiment >= 40) return 'melancholic';
    if (sentiment >= 35) return 'gloomy';
    if (sentiment >= 30) return 'somber';
    if (sentiment >= 25) return 'dejected';
    if (sentiment >= 20) return 'despairing';
    if (sentiment >= 15) return 'anguished';
    if (sentiment >= 10) return 'tormented';
    if (sentiment >= 5) return 'devastated';
    return 'despondent';
  };

  // Create wireframe sphere geometry
  const createWireframeSphere = () => {
    const geometry = new THREE.SphereGeometry(2, 24, 16);
    const edges = new THREE.EdgesGeometry(geometry);
    return edges;
  };

  // Major country positions with more countries
  const countryPositions = {
    'United States': [1.2, 0.8, 0.6],
    'United Kingdom': [0.1, 1.2, 0.8],
    'Germany': [0.3, 1.1, 0.9],
    'France': [0.0, 1.0, 1.0],
    'Japan': [-1.4, 0.6, 0.8],
    'Australia': [0.8, -1.2, 0.6],
    'Brazil': [0.6, -0.4, 1.2],
    'India': [-0.8, 0.4, 1.0],
    'China': [-1.0, 0.8, 0.8],
    'Canada': [1.0, 1.4, 0.4],
    'Russia': [-0.2, 1.6, 0.2],
    'South Africa': [0.2, -1.4, 0.8],
    'Mexico': [0.8, 0.4, 1.0],
    'Italy': [0.2, 0.9, 1.0],
    'Spain': [-0.1, 0.8, 1.0],
    'South Korea': [-1.3, 0.7, 0.7],
    'Sweden': [0.2, 1.5, 0.6],
    'Netherlands': [0.1, 1.1, 0.9],
    'Argentina': [0.4, -0.8, 1.0],
    'Nigeria': [0.1, 0.2, 1.2],
  };

  return (
    <group ref={groupRef}>
      <Float speed={0.5} rotationIntensity={0.02} floatIntensity={0.1}>
        {/* Main wireframe sphere */}
        <lineSegments ref={linesRef}>
          <primitive object={createWireframeSphere()} />
          <lineBasicMaterial color="#e3e3e3" opacity={0.3} transparent={true} />
        </lineSegments>

        {/* Additional grid lines for Joy Division effect */}
        {Array.from({ length: 12 }, (_, i) => (
          <mesh key={i} rotation={[0, 0, (i * Math.PI) / 6]}>
            <torusGeometry args={[2, 0.002, 2, 50, Math.PI]} />
            <meshBasicMaterial 
              color="#e3e3e3" 
              opacity={0.2} 
              transparent={true} 
            />
          </mesh>
        ))}

        {/* Latitude lines */}
        {Array.from({ length: 6 }, (_, i) => (
          <mesh key={`lat-${i}`} rotation={[Math.PI/2, 0, 0]} position={[0, -1 + (i * 0.4), 0]}>
            <torusGeometry args={[2 * Math.cos((i * Math.PI) / 6), 0.002, 2, 50]} />
            <meshBasicMaterial 
              color="#e3e3e3" 
              opacity={0.2} 
              transparent={true} 
            />
          </mesh>
        ))}

        {/* Country sentiment dots */}
        {Object.entries(countryPositions).map(([country, position]) => {
          const sentiment = countrySentiment[country] || happiness;
          return (
            <mesh 
              key={country}
              position={position}
              userData={{ country, sentiment }}
            >
              <sphereGeometry args={[0.06, 8, 8]} />
              <meshBasicMaterial 
                color={getSentimentColor(sentiment)} 
                transparent={true}
                opacity={0.9}
              />
            </mesh>
          );
        })}

        {/* Subtle glow effect */}
        <mesh>
          <sphereGeometry args={[2.1, 32, 32]} />
          <meshBasicMaterial 
            color={getSentimentColor(happiness)} 
            transparent={true} 
            opacity={0.05}
            side={THREE.BackSide}
          />
        </mesh>
      </Float>
    </group>
  );
};

// Improved Joy Division chart with actual data representation
const JoyDivisionChart = ({ scores, title }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!scores.length || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth * 2;
    const height = canvas.height = canvas.offsetHeight * 2;
    
    ctx.scale(2, 2);
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, width/2, height/2);

    // Create meaningful waves based on happiness data
    const waves = Math.min(15, scores.length);
    const waveHeight = height / 2 / (waves + 1);
    
    ctx.lineWidth = 1.5;

    for (let i = 0; i < waves; i++) {
      ctx.beginPath();
      const dataPoint = scores[Math.floor((i / waves) * scores.length)] || 50;
      const intensity = Math.abs(dataPoint - 50) / 50; // 0 to 1
      
      // Color based on sentiment with pops of color
      if (dataPoint >= 60) {
        ctx.strokeStyle = '#00ff88'; // Happy - green
      } else if (dataPoint <= 40) {
        ctx.strokeStyle = '#ff4466'; // Sad - red
      } else {
        ctx.strokeStyle = '#ffaa00'; // Neutral - orange
      }
      
      // Adjust opacity based on intensity
      ctx.globalAlpha = 0.3 + (intensity * 0.7);
      
      const baseY = (i + 1) * waveHeight + 20;
      const points = 120;
      
      for (let x = 0; x < points; x++) {
        const xPos = (x / points) * (width / 2);
        
        // Create wave based on actual data trends
        let wave = 0;
        
        if (x < scores.length) {
          const currentScore = scores[x] || 50;
          const normalizedScore = (currentScore - 50) / 50; // -1 to 1
          wave = normalizedScore * intensity * 30;
        }
        
        // Add some organic wave pattern
        const organicWave = Math.sin(x * 0.1 + i * 0.5) * intensity * 8;
        const finalY = baseY - wave - organicWave;
        
        if (x === 0) {
          ctx.moveTo(xPos, finalY);
        } else {
          ctx.lineTo(xPos, finalY);
        }
      }
      ctx.stroke();
    }
    
    ctx.globalAlpha = 1;
  }, [scores]);

  return (
    <div className="joy-chart">
      <div className="chart-title">{title}</div>
      <div className="chart-legend">
        <span className="legend-item happy">■ positive sentiment</span>
        <span className="legend-item neutral">■ neutral sentiment</span>
        <span className="legend-item sad">■ negative sentiment</span>
      </div>
      <canvas ref={canvasRef} className="joy-canvas" />
    </div>
  );
};

// Tooltip component outside Canvas
const GlobeTooltip = ({ country, sentiment, position, visible }) => {
  if (!visible || !country) return null;
  
  const getSentimentColor = (sentiment) => {
    if (sentiment >= 70) return '#00ff88';
    if (sentiment >= 60) return '#44ff66';
    if (sentiment >= 50) return '#ffaa00';
    if (sentiment >= 40) return '#ff6644';
    return '#ff4466';
  };

  const getSentimentText = (sentiment) => {
    if (sentiment >= 95) return 'ecstatic';
    if (sentiment >= 90) return 'euphoric';
    if (sentiment >= 85) return 'elated';
    if (sentiment >= 80) return 'jubilant';
    if (sentiment >= 75) return 'joyful';
    if (sentiment >= 70) return 'cheerful';
    if (sentiment >= 65) return 'upbeat';
    if (sentiment >= 60) return 'optimistic';
    if (sentiment >= 55) return 'content';
    if (sentiment >= 50) return 'neutral';
    if (sentiment >= 45) return 'subdued';
    if (sentiment >= 40) return 'melancholic';
    if (sentiment >= 35) return 'gloomy';
    if (sentiment >= 30) return 'somber';
    if (sentiment >= 25) return 'dejected';
    if (sentiment >= 20) return 'despairing';
    if (sentiment >= 15) return 'anguished';
    if (sentiment >= 10) return 'tormented';
    if (sentiment >= 5) return 'devastated';
    return 'despondent';
  };

  return (
    <div 
      className="globe-tooltip"
      style={{
        position: 'fixed',
        left: position.x + 15,
        top: position.y - 10,
        zIndex: 1000,
        pointerEvents: 'none'
      }}
    >
      <div className="tooltip-country">{country}</div>
      <div className="tooltip-sentiment">
        <span 
          className="tooltip-percentage"
          style={{ color: getSentimentColor(sentiment) }}
        >
          {sentiment.toFixed(1)}%
        </span>
        <span className="tooltip-mood">
          {getSentimentText(sentiment)}
        </span>
      </div>
    </div>
  );
};
const MinimalStat = ({ label, value, sublabel }) => (
  <div className="minimal-stat">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
    {sublabel && <div className="stat-sublabel">{sublabel}</div>}
  </div>
);

// Minimal post card with color accents
const PostCard = ({ post }) => {
  const getSentimentProps = (label, score) => {
    if (label === 'positive') {
      return { symbol: '+', color: '#00ff88', bgColor: 'rgba(0, 255, 136, 0.05)' };
    } else if (label === 'negative') {
      return { symbol: '−', color: '#ff4466', bgColor: 'rgba(255, 68, 102, 0.05)' };
    } else {
      return { symbol: '○', color: '#ffaa00', bgColor: 'rgba(255, 170, 0, 0.05)' };
    }
  };

  const getSourceProps = (source) => {
    switch(source) {
      case 'reddit': return { icon: 'R', color: '#00ff88' };
      case 'mastodon': return { icon: 'M', color: '#ff4466' };
      case 'google_trends': return { icon: 'T', color: '#ffaa00' };
      default: return { icon: '•', color: '#e3e3e3' };
    }
  };

  const sentimentProps = getSentimentProps(post.sentiment_label, post.sentiment_score);
  const sourceProps = getSourceProps(post.source);

  return (
    <div className="post-card" style={{ backgroundColor: sentimentProps.bgColor }}>
      <div className="post-header">
        <span 
          className="post-source" 
          style={{ borderColor: sourceProps.color, color: sourceProps.color }}
        >
          {sourceProps.icon}
        </span>
        <span 
          className="post-sentiment" 
          style={{ color: sentimentProps.color }}
        >
          {sentimentProps.symbol} {post.sentiment_score.toFixed(0)}
        </span>
      </div>
      <div className="post-text">{post.text}</div>
      <div className="post-meta">
        {new Date(post.timestamp).toLocaleTimeString('en-US', { 
          hour12: false, 
          hour: '2-digit', 
          minute: '2-digit' 
        })}
      </div>
    </div>
  );
};

// About Section Component
const AboutSection = ({ isVisible, onClose }) => {
  if (!isVisible) return null;

  return (
    <div className="about-overlay" onClick={onClose}>
      <div className="about-content" onClick={(e) => e.stopPropagation()}>
        <button className="about-close" onClick={onClose}>×</button>
        
        <h2 className="about-title">How is the Internet Feeling?</h2>
        
        <div className="about-section">
          <h3>what this is</h3>
          <p>
            A real-time sentiment analysis system that monitors the collective emotional state 
            of the internet by analyzing posts from multiple social media platforms and search trends.
          </p>
        </div>

        <div className="about-section">
          <h3>how it works</h3>
          <p>
            The system continuously collects posts from Reddit, Mastodon, and Google Trends data. 
            Each piece of content is processed through advanced sentiment analysis algorithms 
            including VADER, TextBlob, and contextual analysis to determine emotional tone.
          </p>
          <p>
            The happiness index is calculated as a weighted average of all analyzed content, 
            updated in real-time every 10 seconds.
          </p>
        </div>

        <div className="about-section">
          <h3>data sources</h3>
          <div className="source-list">
            <div className="source-item">
              <span className="source-icon" style={{ color: '#00ff88' }}>R</span>
              <div>
                <strong>Reddit</strong>
                <span>Social discussions and community posts</span>
              </div>
            </div>
            <div className="source-item">
              <span className="source-icon" style={{ color: '#ff4466' }}>M</span>
              <div>
                <strong>Mastodon</strong>
                <span>Decentralized social media posts</span>
              </div>
            </div>
            <div className="source-item">
              <span className="source-icon" style={{ color: '#ffaa00' }}>T</span>
              <div>
                <strong>Google Trends</strong>
                <span>Search behavior patterns and interests</span>
              </div>
            </div>
          </div>
        </div>

        <div className="about-section">
          <h3>sentiment analysis</h3>
          <p>
            Multiple algorithms work together to analyze emotional content:
          </p>
          <ul>
            <li><strong>VADER</strong> - Lexicon and rule-based sentiment analysis</li>
            <li><strong>TextBlob</strong> - Pattern-based sentiment classification</li>
            <li><strong>Context Analysis</strong> - Detects emotional keywords, intensifiers, and negations</li>
            <li><strong>Emoji Analysis</strong> - Interprets emotional meaning of emojis and symbols</li>
          </ul>
        </div>

        <div className="about-section">
          <h3>visualization</h3>
          <p>
            The 3D glass emoji face reflects the current emotional state, rotating and changing 
            expression based on sentiment. The Joy Division-inspired wave visualization shows 
            sentiment patterns over time, with colors indicating emotional intensity.
          </p>
        </div>

        <div className="about-section">
          <h3>privacy & ethics</h3>
          <p>
            Only public posts and aggregated search data are analyzed. No personal information 
            is collected or stored. The system provides insights into collective mood patterns 
            while respecting individual privacy.
          </p>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [happinessData, setHappinessData] = useState({
    current_happiness: 50,
    total_posts_analyzed: 0,
    source_breakdown: { reddit: 0, mastodon: 0, google_trends: 0 },
    happiness_trend: [],
    country_sentiment: {}
  });
  const [recentPosts, setRecentPosts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Add mouse tracking for tooltips
  useEffect(() => {
    const handleMouseMove = (event) => {
      setMousePosition({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

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
      setIsConnected(true);
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'happiness_update') {
        setHappinessData(prev => ({
          ...prev,
          current_happiness: message.data.current_happiness,
          total_posts_analyzed: message.data.total_analyzed,
          source_breakdown: message.data.source_breakdown,
          happiness_trend: [...prev.happiness_trend.slice(-30), message.data.current_happiness],
          country_sentiment: message.data.country_sentiment || prev.country_sentiment
        }));
        
        if (message.data.recent_posts) {
          setRecentPosts(message.data.recent_posts.slice(0, 8));
        }
      }
    };

    websocket.onclose = () => setIsConnected(false);
    websocket.onerror = () => setIsConnected(false);

    return () => websocket.close();
  }, []);

  const getSentimentText = (happiness) => {
    if (happiness >= 95) return 'ecstatic';
    if (happiness >= 90) return 'euphoric';
    if (happiness >= 85) return 'elated';
    if (happiness >= 80) return 'jubilant';
    if (happiness >= 75) return 'joyful';
    if (happiness >= 70) return 'cheerful';
    if (happiness >= 65) return 'upbeat';
    if (happiness >= 60) return 'optimistic';
    if (happiness >= 55) return 'content';
    if (happiness >= 50) return 'neutral';
    if (happiness >= 45) return 'subdued';
    if (happiness >= 40) return 'melancholic';
    if (happiness >= 35) return 'gloomy';
    if (happiness >= 30) return 'somber';
    if (happiness >= 25) return 'dejected';
    if (happiness >= 20) return 'despairing';
    if (happiness >= 15) return 'anguished';
    if (happiness >= 10) return 'tormented';
    if (happiness >= 5) return 'devastated';
    return 'despondent';
  };

  const getSentimentColor = (happiness) => {
    if (happiness >= 70) return '#00ff88';
    if (happiness >= 60) return '#44ff66';
    if (happiness >= 50) return '#ffaa00';
    if (happiness >= 40) return '#ff6644';
    return '#ff4466';
  };

  return (
    <div className="app">
      <div className="header">
        <h1 className="main-title">How is the Internet Feeling?</h1>
        <div className="header-controls">
          <div className="connection-indicator">
            <span className={`status-dot ${isConnected ? 'live' : 'offline'}`}></span>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          <button 
            className="about-button"
            onClick={() => setShowAbout(true)}
          >
            ABOUT
          </button>
        </div>
      </div>

      <div className="main-display">
        <div 
          className="globe-container"
          onMouseEnter={() => setHoveredCountry(null)}
        >
          <Canvas 
            camera={{ position: [0, 0, 6], fov: 50 }}
            onPointerMissed={() => setHoveredCountry(null)}
          >
            <ambientLight intensity={0.4} />
            <pointLight position={[10, 10, 10]} intensity={0.8} />
            <pointLight position={[-10, -10, 10]} intensity={0.6} />
            <WireframeGlobe 
              happiness={happinessData.current_happiness} 
              countrySentiment={happinessData.country_sentiment || {}}
              onCountryHover={setHoveredCountry}
            />
          </Canvas>
        </div>
        
        <div className="sentiment-readout">
          <div 
            className="happiness-percentage"
            style={{ color: getSentimentColor(happinessData.current_happiness) }}
          >
            {happinessData.current_happiness.toFixed(1)}%
          </div>
          <div className="sentiment-word">
            {getSentimentText(happinessData.current_happiness)}
          </div>
          <div className="globe-legend">
            <div className="legend-title">global sentiment</div>
            <div className="legend-colors">
              <span className="legend-color happy">■ euphoric/joyful</span>
              <span className="legend-color neutral">■ content/neutral</span>
              <span className="legend-color sad">■ melancholic/somber</span>
            </div>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <MinimalStat 
          label="TOTAL ANALYZED"
          value={happinessData.total_posts_analyzed.toLocaleString()}
        />
        <MinimalStat 
          label="REDDIT"
          value={happinessData.source_breakdown.reddit.toLocaleString()}
        />
        <MinimalStat 
          label="MASTODON"
          value={happinessData.source_breakdown.mastodon.toLocaleString()}
        />
        <MinimalStat 
          label="TRENDS"
          value={happinessData.source_breakdown.google_trends.toLocaleString()}
        />
      </div>

      {happinessData.happiness_trend.length > 5 && (
        <div className="chart-section">
          <JoyDivisionChart 
            scores={happinessData.happiness_trend} 
            title="SENTIMENT WAVES"
          />
        </div>
      )}

      <div className="posts-section">
        <div className="section-title">RECENT TRANSMISSIONS</div>
        <div className="posts-grid">
          {recentPosts.map((post, index) => (
            <PostCard key={`${post.id}-${index}`} post={post} />
          ))}
        </div>
        
        {recentPosts.length === 0 && (
          <div className="empty-state">
            <div>MONITORING GLOBAL FREQUENCIES...</div>
          </div>
        )}
      </div>

      <GlobeTooltip
        country={hoveredCountry?.name}
        sentiment={hoveredCountry?.sentiment}
        position={mousePosition}
        visible={!!hoveredCountry}
      />

      <AboutSection 
        isVisible={showAbout} 
        onClose={() => setShowAbout(false)} 
      />
    </div>
  );
}

export default App;