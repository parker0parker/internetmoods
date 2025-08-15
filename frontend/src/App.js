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
const WireframeGlobe = ({ happiness, countrySentiment, onCountryHover }) => {
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

  // Create wireframe sphere geometry
  const createWireframeSphere = () => {
    const geometry = new THREE.SphereGeometry(2, 24, 16);
    const edges = new THREE.EdgesGeometry(geometry);
    return edges;
  };

  // Create interactive country dot
  const CountryDot = ({ position, sentiment, name }) => {
    const [hovered, setHovered] = useState(false);
    
    return (
      <mesh 
        position={position}
        onPointerOver={(event) => {
          event.stopPropagation();
          setHovered(true);
          onCountryHover({ name, sentiment });
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={(event) => {
          event.stopPropagation();
          setHovered(false);
          onCountryHover(null);
          document.body.style.cursor = 'default';
        }}
      >
        <sphereGeometry args={[hovered ? 0.08 : 0.06, 8, 8]} />
        <meshBasicMaterial 
          color={getSentimentColor(sentiment)} 
          transparent={true}
          opacity={hovered ? 1.0 : 0.9}
        />
        
        {/* Glow effect on hover */}
        {hovered && (
          <mesh>
            <sphereGeometry args={[0.12, 8, 8]} />
            <meshBasicMaterial 
              color={getSentimentColor(sentiment)} 
              transparent={true}
              opacity={0.3}
            />
          </mesh>
        )}
      </mesh>
    );
  };

  // Convert latitude and longitude to 3D coordinates
  const latLongTo3D = (lat, lng, radius = 2) => {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lng + 180) * (Math.PI / 180);
    
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    
    return [x, y, z];
  };

  // Accurate country positions with latitude and longitude
  const countryCoordinates = {
    // North America
    'United States': [39.8283, -98.5795],
    'Canada': [56.1304, -106.3468],
    'Mexico': [23.6345, -102.5528],
    
    // South America
    'Brazil': [-14.2350, -51.9253],
    'Argentina': [-38.4161, -63.6167],
    'Chile': [-35.6751, -71.5430],
    'Colombia': [4.5709, -74.2973],
    'Peru': [-9.1900, -75.0152],
    'Venezuela': [6.4238, -66.5897],
    'Uruguay': [-32.5228, -55.7658],
    'Ecuador': [-1.8312, -78.1834],
    
    // Europe
    'United Kingdom': [55.3781, -3.4360],
    'Germany': [51.1657, 10.4515],
    'France': [46.6034, 2.2137],
    'Italy': [41.8719, 12.5674],
    'Spain': [40.4637, -3.7492],
    'Netherlands': [52.1326, 5.2913],
    'Sweden': [60.1282, 18.6435],
    'Norway': [60.4720, 8.4689],
    'Finland': [61.9241, 25.7482],
    'Denmark': [56.2639, 9.5018],
    'Belgium': [50.5039, 4.4699],
    'Switzerland': [46.8182, 8.2275],
    'Austria': [47.5162, 14.5501],
    'Poland': [51.9194, 19.1451],
    'Czech Republic': [49.8175, 15.4730],
    'Portugal': [39.3999, -8.2245],
    'Greece': [39.0742, 21.8243],
    'Russia': [61.5240, 105.3188],
    'Ukraine': [48.3794, 31.1656],
    'Turkey': [38.9637, 35.2433],
    
    // Asia
    'China': [35.8617, 104.1954],
    'Japan': [36.2048, 138.2529],
    'India': [20.5937, 78.9629],
    'South Korea': [35.9078, 127.7669],
    'Thailand': [15.8700, 100.9925],
    'Vietnam': [14.0583, 108.2772],
    'Indonesia': [-0.7893, 113.9213],
    'Philippines': [12.8797, 121.7740],
    'Malaysia': [4.2105, 101.9758],
    'Singapore': [1.3521, 103.8198],
    'Taiwan': [23.6978, 120.9605],
    'Bangladesh': [23.6850, 90.3563],
    'Pakistan': [30.3753, 69.3451],
    'Iran': [32.4279, 53.6880],
    'Saudi Arabia': [23.8859, 45.0792],
    'Israel': [31.0461, 34.8516],
    'UAE': [23.4241, 53.8478],
    'Mongolia': [46.8625, 103.8467],
    'Kazakhstan': [48.0196, 66.9237],
    
    // Africa
    'South Africa': [-30.5595, 22.9375],
    'Nigeria': [9.0820, 8.6753],
    'Egypt': [26.0975, 30.0444],
    'Kenya': [-0.0236, 37.9062],
    'Morocco': [31.7917, -7.0926],
    'Ghana': [7.9465, -1.0232],
    'Ethiopia': [9.1450, 40.4897],
    'Tanzania': [-6.3690, 34.8888],
    'Algeria': [28.0339, 1.6596],
    'Libya': [26.3351, 17.2283],
    'Tunisia': [33.8869, 9.5375],
    'Cameroon': [7.3697, 12.3547],
    'Uganda': [1.3733, 32.2903],
    'Zimbabwe': [-19.0154, 29.1549],
    
    // Oceania
    'Australia': [-25.2744, 133.7751],
    'New Zealand': [-40.9006, 174.8860],
    'Papua New Guinea': [-6.3149, 143.9555],
    'Fiji': [-16.5781, 179.4144],
    
    // Middle East
    'Iraq': [33.2232, 43.6793],
    'Afghanistan': [33.9391, 67.7100],
    'Syria': [34.8021, 38.9968],
    'Jordan': [30.5852, 36.2384],
    'Lebanon': [33.8547, 35.8623]
  };

  // Convert all coordinates to 3D positions
  const countryPositions = {};
  Object.entries(countryCoordinates).forEach(([country, [lat, lng]]) => {
    countryPositions[country] = latLongTo3D(lat, lng);
  });

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
            <CountryDot
              key={country}
              position={position}
              sentiment={sentiment}
              name={country}
            />
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

// Multi-Country Happiness Timeline Chart - Robust Version
const CountryHappinessChart = ({ countryTimelines = [], title }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    // Early returns with comprehensive safety checks
    if (!Array.isArray(countryTimelines) || countryTimelines.length === 0 || !canvasRef.current) {
      return;
    }

    // Filter and validate countries with proper error handling
    const validCountries = countryTimelines.filter(country => {
      return (
        country &&
        typeof country === 'object' &&
        country.name &&
        Array.isArray(country.timeline) &&
        country.timeline.length >= 5
      );
    });

    if (validCountries.length === 0) {
      return;
    }

    try {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const width = canvas.width = canvas.offsetWidth * 2;
      const height = canvas.height = (canvas.offsetHeight) * 2; // Account for reserved legend space
      
      ctx.scale(2, 2);
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, width/2, height/2);

      // Chart dimensions - leave more space at bottom for legend
      const padding = 50;
      const bottomPadding = 100; // Extra space for legend at bottom
      const chartWidth = width/2 - padding * 2;
      const chartHeight = height/2 - padding - bottomPadding;
      
      // Country colors (space theme palette)
      const countryColors = [
        '#00ff88', '#ffaa00', '#ff4466', '#44ff66', 
        '#ff6644', '#ffffff', '#66aaff'
      ];
      
      // Draw grid
      ctx.strokeStyle = '#333333';
      ctx.lineWidth = 0.5;
      ctx.globalAlpha = 0.3;
      
      // Horizontal grid lines
      for (let i = 0; i <= 10; i++) {
        const y = padding + (i / 10) * chartHeight;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(padding + chartWidth, y);
        ctx.stroke();
      }
      
      // Find max timeline length safely
      const timelineLengths = validCountries.map(c => c.timeline.length);
      const maxLength = Math.max(...timelineLengths);
      
      // Vertical grid lines
      const timeIntervals = Math.min(10, maxLength);
      for (let i = 0; i <= timeIntervals; i++) {
        const x = padding + (i / timeIntervals) * chartWidth;
        ctx.beginPath();
        ctx.moveTo(x, padding);
        ctx.lineTo(x, padding + chartHeight);
        ctx.stroke();
      }
      
      ctx.globalAlpha = 1;
      
      // Draw country lines
      validCountries.forEach((country, countryIndex) => {
        const color = countryColors[countryIndex % countryColors.length];
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        let hasStarted = false;
        country.timeline.forEach((happiness, index) => {
          // Ensure happiness is a valid number
          const happinessValue = typeof happiness === 'number' && isFinite(happiness) ? happiness : 50;
          
          const x = padding + (index / (maxLength - 1)) * chartWidth;
          const normalizedHappiness = Math.max(0, Math.min(1, (happinessValue - 10) / 80));
          const y = padding + chartHeight - (normalizedHappiness * chartHeight);
          
          if (!hasStarted) {
            ctx.moveTo(x, y);
            hasStarted = true;
          } else {
            ctx.lineTo(x, y);
          }
        });
        
        ctx.stroke();
        
        // Add glow effect
        ctx.shadowColor = color;
        ctx.shadowBlur = 2;
        ctx.stroke();
        ctx.shadowBlur = 0;
        
        // Draw data points
        ctx.fillStyle = color;
        country.timeline.forEach((happiness, index) => {
          const happinessValue = typeof happiness === 'number' && isFinite(happiness) ? happiness : 50;
          
          const x = padding + (index / (maxLength - 1)) * chartWidth;
          const normalizedHappiness = Math.max(0, Math.min(1, (happinessValue - 10) / 80));
          const y = padding + chartHeight - (normalizedHappiness * chartHeight);
          
          ctx.beginPath();
          ctx.arc(x, y, 1.5, 0, Math.PI * 2);
          ctx.fill();
        });
      });
      
      // Draw Y-axis labels
      ctx.fillStyle = '#666666';
      ctx.font = '10px "Noto Sans Mono"';
      ctx.textAlign = 'right';
      
      for (let i = 0; i <= 10; i++) {
        const y = padding + (i / 10) * chartHeight;
        const value = Math.round(90 - (i * 8));
        ctx.fillText(`${value}%`, padding - 10, y + 3);
      }
      
      // Draw time labels
      ctx.textAlign = 'center';
      ctx.font = '9px "Noto Sans Mono"';
      const now = new Date();
      
      for (let i = 0; i <= 5; i++) {
        const x = padding + (i / 5) * chartWidth;
        const minutesAgo = Math.round((maxLength - 1) * (1 - i / 5) * 1.5);
        const labelTime = new Date(now.getTime() - minutesAgo * 60000);
        const timeLabel = labelTime.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        });
        ctx.fillText(timeLabel, x, padding + chartHeight + 20);
      }
      
    } catch (error) {
      console.warn('Chart rendering error:', error);
    }
    
  }, [countryTimelines]);

  // Safely get valid countries for legend
  const validCountriesForLegend = Array.isArray(countryTimelines) ? 
    countryTimelines.filter(c => 
      c && 
      typeof c === 'object' && 
      c.name && 
      Array.isArray(c.timeline) && 
      c.timeline.length >= 5
    ).slice(0, 7) : [];

  return (
    <div className="country-happiness-chart">
      <div className="chart-title">{title}</div>
      <div className="chart-legend country-legend">
        {validCountriesForLegend.map((country, index) => {
          const colors = ['#00ff88', '#ffaa00', '#ff4466', '#44ff66', '#ff6644', '#ffffff', '#66aaff'];
          const totalPosts = country.total_posts || 0;
          
          return (
            <span key={`${country.name}-${index}`} className="legend-item" style={{ color: colors[index] }}>
              ■ {country.name.toLowerCase()} ({totalPosts})
            </span>
          );
        })}
      </div>
      <canvas ref={canvasRef} className="happiness-canvas" />
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

// Minimal post card with color accents and clickable links
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
      case 'youtube': return { icon: 'Y', color: '#44ff66' };
      case 'news': return { icon: 'N', color: '#ff6644' };
      case 'twitter': return { icon: 'X', color: '#6644ff' };
      case 'forums': return { icon: 'F', color: '#ff44aa' };
      default: return { icon: '•', color: '#e3e3e3' };
    }
  };

  const sentimentProps = getSentimentProps(post.sentiment_label, post.sentiment_score);
  const sourceProps = getSourceProps(post.source);
  
  // Handle click to open source URL
  const handleClick = () => {
    if (post.url && post.url !== '' && post.url !== 'undefined') {
      window.open(post.url, '_blank', 'noopener,noreferrer');
    }
  };

  const isClickable = post.url && post.url !== '' && post.url !== 'undefined';

  return (
    <div 
      className={`post-card ${isClickable ? 'post-card-clickable' : ''}`}
      style={{ backgroundColor: sentimentProps.bgColor }}
      onClick={handleClick}
      title={isClickable ? `Open ${post.source} source` : ''}
    >
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
        {isClickable && (
          <span className="post-link-indicator">↗</span>
        )}
      </div>
      <div className="post-text">{post.text}</div>
      <div className="post-meta">
        {new Date(post.timestamp).toLocaleTimeString('en-US', { 
          hour12: false, 
          hour: '2-digit', 
          minute: '2-digit' 
        })}
        {post.subreddit && (
          <span className="post-subreddit"> • r/{post.subreddit}</span>
        )}
        {post.instance && (
          <span className="post-instance"> • {post.instance}</span>
        )}
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
            The system continuously collects posts from seven major data sources: Reddit, Mastodon, 
            Google Trends, YouTube, News headlines, Twitter/X, and public forums. Each piece of 
            content is processed through advanced sentiment analysis algorithms including VADER, 
            TextBlob, and contextual analysis to determine emotional tone.
          </p>
          <p>
            The global happiness index is calculated as a weighted average of all analyzed content, 
            updated in real-time every 5 seconds. Country-specific sentiment is tracked individually, 
            creating detailed happiness timelines for regions with sufficient data (minimum 5 posts).
          </p>
          <p>
            The space observatory interface provides an immersive experience, displaying Earth's 
            emotional pulse as viewed from orbit with realistic star movement and atmospheric effects.
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
            <div className="source-item">
              <span className="source-icon" style={{ color: '#44ff66' }}>Y</span>
              <div>
                <strong>YouTube</strong>
                <span>Comments from trending videos</span>
              </div>
            </div>
            <div className="source-item">
              <span className="source-icon" style={{ color: '#ff6644' }}>N</span>
              <div>
                <strong>News</strong>
                <span>Headlines and articles from global news sources</span>
              </div>
            </div>
            <div className="source-item">
              <span className="source-icon" style={{ color: '#6644ff' }}>X</span>
              <div>
                <strong>Twitter/X</strong>
                <span>Public tweets and social discussions</span>
              </div>
            </div>
            <div className="source-item">
              <span className="source-icon" style={{ color: '#ff44aa' }}>F</span>
              <div>
                <strong>Forums</strong>
                <span>Public discussion boards and communities</span>
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
            The interface features a space observatory theme with multiple visualization layers:
          </p>
          <ul>
            <li><strong>3D Wireframe Globe</strong> - Real-time country sentiment mapping with color-coded emotional states</li>
            <li><strong>Sentiment Emoji</strong> - Dynamic emotional expression that changes with global happiness levels</li>
            <li><strong>Country Timeline Charts</strong> - Multi-line graphs showing happiness trends for top countries over time</li>
            <li><strong>Real-time Statistics</strong> - Live data feeds showing posts analyzed from all seven sources</li>
          </ul>
          <p>
            The globe displays individual countries as colored dots: green for happy regions, 
            orange for neutral, and red for sad areas. Country-specific happiness trends are 
            tracked and displayed in detailed timeline charts.
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
    source_breakdown: { reddit: 0, mastodon: 0, google_trends: 0, youtube: 0, news: 0, twitter: 0, forums: 0 },
    happiness_trend: [],
    country_sentiment: {},
    country_timelines: [],
    uptime: "00:00"
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
          happiness_trend: message.data.happiness_trend || prev.happiness_trend || [],
          country_sentiment: message.data.country_sentiment || prev.country_sentiment,
          country_timelines: message.data.country_timelines || prev.country_timelines,
          uptime: message.data.uptime || prev.uptime
        }));
        
        if (message.data.recent_posts && Array.isArray(message.data.recent_posts)) {
          setRecentPosts(message.data.recent_posts.slice(0, 8));
        }
      }
    };

    websocket.onclose = () => setIsConnected(false);
    websocket.onerror = () => setIsConnected(false);

    return () => websocket.close();
  }, []);

  // Add smooth scroll-based parallax effect - stars move up when scrolling down
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const starfield = document.body;
      if (starfield) {
        // Stars move up when scrolling down (negative value)
        starfield.style.setProperty('--scroll-y', `${-scrollY * 0.2}px`);
      }
    };

    // Use RAF for smoother animation
    let ticking = false;
    const smoothScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', smoothScroll, { passive: true });
    return () => window.removeEventListener('scroll', smoothScroll);
  }, []);

  const getSentimentEmoji = (happiness) => {
    if (happiness >= 95) return '🤩'; // ecstatic
    if (happiness >= 90) return '😍'; // euphoric
    if (happiness >= 85) return '🥳'; // elated
    if (happiness >= 80) return '😄'; // jubilant
    if (happiness >= 75) return '😊'; // joyful
    if (happiness >= 70) return '😌'; // cheerful
    if (happiness >= 65) return '🙂'; // upbeat
    if (happiness >= 60) return '😐'; // optimistic
    if (happiness >= 55) return '😶'; // content
    if (happiness >= 50) return '😑'; // neutral
    if (happiness >= 45) return '🙁'; // subdued
    if (happiness >= 40) return '☹️'; // melancholic
    if (happiness >= 35) return '😞'; // gloomy
    if (happiness >= 30) return '😔'; // somber
    if (happiness >= 25) return '😟'; // dejected
    if (happiness >= 20) return '😨'; // despairing
    if (happiness >= 15) return '😰'; // anguished
    if (happiness >= 10) return '😱'; // tormented
    if (happiness >= 5) return '😭'; // devastated
    return '💀'; // despondent
  };

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

  // Helper functions to get happiest and saddest countries
  const getHappiestCountry = (countrySentiment) => {
    if (!countrySentiment || Object.keys(countrySentiment).length === 0) {
      return 'n/a';
    }
    
    let happiestCountry = 'n/a';
    let highestSentiment = 0;
    
    Object.entries(countrySentiment).forEach(([country, sentiment]) => {
      if (sentiment > highestSentiment) {
        highestSentiment = sentiment;
        happiestCountry = country.toLowerCase();
      }
    });
    
    return happiestCountry;
  };

  const getSaddestCountry = (countrySentiment) => {
    if (!countrySentiment || Object.keys(countrySentiment).length === 0) {
      return 'n/a';
    }
    
    let saddestCountry = 'n/a';
    let lowestSentiment = 100;
    
    Object.entries(countrySentiment).forEach(([country, sentiment]) => {
      if (sentiment < lowestSentiment) {
        lowestSentiment = sentiment;
        saddestCountry = country.toLowerCase();
      }
    });
    
    return saddestCountry;
  };

  return (
    <div className="app">
      <div className="header">
        <h1 className="main-title">
          How Is<br />
          The Internet<br />
          Feeling?
        </h1>
        <div className="header-controls">
          <div className="connection-indicator">
            <span className={`status-dot ${isConnected ? 'live' : 'offline'}`}></span>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          <div className="uptime-indicator">
            <span>UPTIME: {happinessData.uptime}</span>
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
          <div className="sentiment-emoji">
            {getSentimentEmoji(happinessData.current_happiness)}
          </div>
          <div 
            className="happiness-percentage"
            style={{ color: getSentimentColor(happinessData.current_happiness) }}
          >
            {happinessData.current_happiness.toFixed(1)}%
          </div>
          <div className="globe-legend">
            <div className="legend-title">global sentiment</div>
            <div className="legend-colors">
              <span className="legend-color happy">■ euphoric/joyful</span>
              <span className="legend-color neutral">■ content/neutral</span>
              <span className="legend-color sad">■ melancholic/somber</span>
            </div>
          </div>
          
          <div className="country-extremes">
            <div className="extreme-title">current extremes</div>
            <div className="extreme-countries">
              <div className="extreme-item">
                <span className="extreme-label">happiest:</span>
                <span className="extreme-country happy">
                  {getHappiestCountry(happinessData.country_sentiment)}
                </span>
              </div>
              <div className="extreme-item">
                <span className="extreme-label">saddest:</span>
                <span className="extreme-country sad">
                  {getSaddestCountry(happinessData.country_sentiment)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="stats-section">
        <div className="total-stat-centered">
          <MinimalStat 
            label="TOTAL ANALYZED"
            value={happinessData.total_posts_analyzed.toLocaleString()}
          />
        </div>
        
        <div className="source-stats-grid">
          <MinimalStat 
            label="REDDIT"
            value={happinessData.source_breakdown.reddit?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="MASTODON"
            value={happinessData.source_breakdown.mastodon?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="TRENDS"
            value={happinessData.source_breakdown.google_trends?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="YOUTUBE"
            value={happinessData.source_breakdown.youtube?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="NEWS"
            value={happinessData.source_breakdown.news?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="TWITTER"
            value={happinessData.source_breakdown.twitter?.toLocaleString() || '0'}
          />
          <MinimalStat 
            label="FORUMS"
            value={happinessData.source_breakdown.forums?.toLocaleString() || '0'}
          />
        </div>
      </div>

      {happinessData.country_timelines && happinessData.country_timelines.length > 0 && (
        <div className="chart-section">
          <CountryHappinessChart 
            countryTimelines={happinessData.country_timelines || []} 
            title="COUNTRY HAPPINESS TIMELINE"
          />
        </div>
      )}

      <div className="posts-section">
        <div className="section-title">RECENT TRANSMISSIONS</div>
        <div className="posts-grid">
          {(recentPosts || []).map((post, index) => (
            <PostCard key={`${post.id}-${index}`} post={post} />
          ))}
        </div>
        
        {(recentPosts || []).length === 0 && (
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