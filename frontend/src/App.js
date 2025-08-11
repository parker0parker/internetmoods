import React, { useEffect, useState, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Text, Float, MeshTransmissionMaterial } from "@react-three/drei";
import * as THREE from "three";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// 3D Glass Emoji Face Component
const GlassEmojiFace = ({ happiness }) => {
  const meshRef = useRef();
  const groupRef = useRef();

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
    }
  });

  // Determine emoji shape based on happiness level
  const getEmojiGeometry = () => {
    if (happiness >= 70) return 'happy';
    if (happiness >= 45) return 'neutral';
    return 'sad';
  };

  const emojiType = getEmojiGeometry();

  return (
    <group ref={groupRef}>
      <Float speed={2} rotationIntensity={0.1} floatIntensity={0.5}>
        {/* Main face sphere */}
        <mesh ref={meshRef} scale={[2, 2, 2]}>
          <sphereGeometry args={[1, 32, 32]} />
          <MeshTransmissionMaterial
            transmission={0.9}
            thickness={0.2}
            roughness={0.1}
            chromaticAberration={0.1}
            anisotropy={0.1}
            envMapIntensity={0.5}
            color="#ffffff"
          />
        </mesh>

        {/* Eyes */}
        <mesh position={[-0.3, 0.2, 0.8]}>
          <sphereGeometry args={[0.1, 16, 16]} />
          <meshBasicMaterial color="#000000" />
        </mesh>
        <mesh position={[0.3, 0.2, 0.8]}>
          <sphereGeometry args={[0.1, 16, 16]} />
          <meshBasicMaterial color="#000000" />
        </mesh>

        {/* Mouth based on sentiment */}
        {emojiType === 'happy' && (
          <mesh position={[0, -0.3, 0.8]} rotation={[0, 0, 0]}>
            <torusGeometry args={[0.3, 0.05, 8, 16, Math.PI]} />
            <meshBasicMaterial color="#000000" />
          </mesh>
        )}
        
        {emojiType === 'neutral' && (
          <mesh position={[0, -0.3, 0.8]}>
            <boxGeometry args={[0.4, 0.05, 0.05]} />
            <meshBasicMaterial color="#000000" />
          </mesh>
        )}
        
        {emojiType === 'sad' && (
          <mesh position={[0, -0.3, 0.8]} rotation={[0, 0, Math.PI]}>
            <torusGeometry args={[0.3, 0.05, 8, 16, Math.PI]} />
            <meshBasicMaterial color="#000000" />
          </mesh>
        )}
      </Float>
    </group>
  );
};

// Joy Division inspired trend visualization
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

    // Joy Division style waves
    const waves = 12;
    const waveHeight = height / 2 / waves;
    
    ctx.strokeStyle = '#e3e3e3';
    ctx.lineWidth = 1;

    for (let i = 0; i < waves; i++) {
      ctx.beginPath();
      const baseY = (i + 1) * waveHeight;
      
      for (let x = 0; x < width/2; x += 4) {
        const dataIndex = Math.floor((x / (width/2)) * scores.length);
        const score = scores[dataIndex] || 50;
        
        // Create wave distortion based on happiness data
        const amplitude = Math.abs(score - 50) * 0.8;
        const frequency = 0.02 + (i * 0.005);
        const wave = Math.sin(x * frequency) * amplitude * 0.3;
        const dataWave = (score - 50) * 0.1;
        
        const y = baseY - wave - dataWave;
        
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }
  }, [scores]);

  return (
    <div className="joy-chart">
      <div className="chart-title">{title}</div>
      <canvas ref={canvasRef} className="joy-canvas" />
    </div>
  );
};

// Minimal stat component
const MinimalStat = ({ label, value, sublabel }) => (
  <div className="minimal-stat">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
    {sublabel && <div className="stat-sublabel">{sublabel}</div>}
  </div>
);

// Minimal post card
const PostCard = ({ post }) => {
  const getSentimentIndicator = (label) => {
    switch(label) {
      case 'positive': return '+';
      case 'negative': return '−';
      default: return '○';
    }
  };

  const getSourceIcon = (source) => {
    switch(source) {
      case 'reddit': return 'R';
      case 'mastodon': return 'M';
      case 'google_trends': return 'T';
      default: return '•';
    }
  };

  return (
    <div className="post-card">
      <div className="post-header">
        <span className="post-source">{getSourceIcon(post.source)}</span>
        <span className="post-sentiment">
          {getSentimentIndicator(post.sentiment_label)} {post.sentiment_score.toFixed(0)}
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

function App() {
  const [happinessData, setHappinessData] = useState({
    current_happiness: 50,
    total_posts_analyzed: 0,
    source_breakdown: { reddit: 0, mastodon: 0, google_trends: 0 },
    happiness_trend: []
  });
  const [recentPosts, setRecentPosts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

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
          happiness_trend: [...prev.happiness_trend.slice(-20), message.data.current_happiness]
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
    if (happiness >= 70) return 'euphoric';
    if (happiness >= 60) return 'joyful';
    if (happiness >= 50) return 'content';
    if (happiness >= 40) return 'melancholic';
    if (happiness >= 30) return 'somber';
    return 'despondent';
  };

  return (
    <div className="app">
      <div className="header">
        <h1 className="main-title">How is the Internet Feeling?</h1>
        <div className="connection-indicator">
          <span className={`status-dot ${isConnected ? 'live' : 'offline'}`}></span>
          {isConnected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>

      <div className="main-display">
        <div className="emoji-container">
          <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1} />
            <GlassEmojiFace happiness={happinessData.current_happiness} />
          </Canvas>
        </div>
        
        <div className="sentiment-readout">
          <div className="happiness-percentage">
            {happinessData.current_happiness.toFixed(1)}%
          </div>
          <div className="sentiment-word">
            {getSentimentText(happinessData.current_happiness)}
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

      {happinessData.happiness_trend.length > 0 && (
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
            <div>MONITORING FREQUENCIES...</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;