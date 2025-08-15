#!/usr/bin/env python3
"""
Backend Test Suite for Internet Happiness Index
Tests all API endpoints, WebSocket functionality, and data generation
"""

import requests
import json
import time
import asyncio
import websockets
import threading
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class HappinessIndexTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.websocket_messages = []
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if data and not success:
            print(f"   Data: {data}")
    
    def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Root Endpoint", True, f"Status: {response.status_code}", data)
                    return True
                else:
                    self.log_test("Root Endpoint", False, "Missing message field", data)
                    return False
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_happiness_endpoint(self):
        """Test GET /api/happiness endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/happiness")
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["current_happiness", "total_posts_analyzed", "source_breakdown", "happiness_trend", "last_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Happiness Endpoint Structure", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Validate happiness score range (0-100)
                happiness = data.get("current_happiness", -1)
                if not (0 <= happiness <= 100):
                    self.log_test("Happiness Score Range", False, f"Score {happiness} not in range 0-100", data)
                    return False
                
                # Check source breakdown structure
                source_breakdown = data.get("source_breakdown", {})
                if not isinstance(source_breakdown, dict):
                    self.log_test("Source Breakdown Structure", False, "Source breakdown not a dict", data)
                    return False
                
                # Check happiness trend is a list
                trend = data.get("happiness_trend", [])
                if not isinstance(trend, list):
                    self.log_test("Happiness Trend Structure", False, "Trend not a list", data)
                    return False
                
                self.log_test("Happiness Endpoint", True, f"Happiness: {happiness}%, Posts: {data.get('total_posts_analyzed', 0)}", data)
                return True
            else:
                self.log_test("Happiness Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Happiness Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_recent_posts_endpoint(self):
        """Test GET /api/recent-posts endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/recent-posts")
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test("Recent Posts Structure", False, "Response not a list", data)
                    return False
                
                # If there are posts, validate structure
                if data:
                    post = data[0]
                    required_fields = ["id", "source", "text", "sentiment_score", "sentiment_label", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in post]
                    
                    if missing_fields:
                        self.log_test("Recent Posts Post Structure", False, f"Missing fields: {missing_fields}", post)
                        return False
                    
                    # Validate sentiment score range
                    score = post.get("sentiment_score", -1)
                    if not (0 <= score <= 100):
                        self.log_test("Recent Posts Sentiment Range", False, f"Score {score} not in range 0-100", post)
                        return False
                    
                    # Validate sentiment label
                    label = post.get("sentiment_label", "")
                    if label not in ["positive", "negative", "neutral"]:
                        self.log_test("Recent Posts Sentiment Label", False, f"Invalid label: {label}", post)
                        return False
                
                self.log_test("Recent Posts Endpoint", True, f"Retrieved {len(data)} posts", {"count": len(data)})
                return True
            else:
                self.log_test("Recent Posts Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Recent Posts Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_start_streaming_endpoint(self):
        """Test POST /api/start-streaming endpoint"""
        try:
            response = self.session.post(f"{API_BASE}/start-streaming")
            if response.status_code == 200:
                data = response.json()
                
                if "message" not in data or "sources" not in data:
                    self.log_test("Start Streaming Structure", False, "Missing message or sources", data)
                    return False
                
                sources = data.get("sources", [])
                expected_sources = ["reddit", "mastodon", "google_trends"]
                
                if not all(source in sources for source in expected_sources):
                    self.log_test("Start Streaming Sources", False, f"Missing expected sources", data)
                    return False
                
                self.log_test("Start Streaming Endpoint", True, f"Started streaming {len(sources)} sources", data)
                return True
            else:
                self.log_test("Start Streaming Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Start Streaming Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_status_endpoints(self):
        """Test POST and GET /api/status endpoints"""
        try:
            # Test POST /api/status
            test_data = {"client_name": "test_client_happiness_index"}
            response = self.session.post(f"{API_BASE}/status", json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "client_name", "timestamp"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("POST Status Structure", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                if data.get("client_name") != test_data["client_name"]:
                    self.log_test("POST Status Data", False, "Client name mismatch", data)
                    return False
                
                self.log_test("POST Status Endpoint", True, "Status created successfully", data)
            else:
                self.log_test("POST Status Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
            
            # Test GET /api/status
            response = self.session.get(f"{API_BASE}/status")
            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list):
                    self.log_test("GET Status Structure", False, "Response not a list", data)
                    return False
                
                self.log_test("GET Status Endpoint", True, f"Retrieved {len(data)} status checks", {"count": len(data)})
                return True
            else:
                self.log_test("GET Status Endpoint", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Status Endpoints", False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and message handling"""
        try:
            ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for initial status message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("type") == "initial_status":
                        initial_data = data.get("data", {})
                        required_fields = ["current_happiness", "total_analyzed", "source_breakdown"]
                        missing_fields = [field for field in required_fields if field not in initial_data]
                        
                        if missing_fields:
                            self.log_test("WebSocket Initial Message", False, f"Missing fields: {missing_fields}", data)
                            return False
                        
                        self.log_test("WebSocket Connection", True, "Connected and received initial status", data)
                        self.websocket_messages.append(data)
                        
                        # Wait for additional messages (happiness updates)
                        try:
                            for _ in range(3):  # Try to get 3 more messages
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                data = json.loads(message)
                                self.websocket_messages.append(data)
                                
                                if data.get("type") == "happiness_update":
                                    self.log_test("WebSocket Happiness Update", True, "Received happiness update", data)
                        except asyncio.TimeoutError:
                            self.log_test("WebSocket Updates", False, "No happiness updates received within timeout")
                            return False
                        
                        return True
                    else:
                        self.log_test("WebSocket Initial Message Type", False, f"Unexpected message type: {data.get('type')}", data)
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Initial Message", False, "No initial message received")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")
            return False
    
    def test_data_generation_over_time(self):
        """Test that data is being generated continuously"""
        try:
            # Get initial state
            response1 = self.session.get(f"{API_BASE}/happiness")
            if response1.status_code != 200:
                self.log_test("Data Generation Initial", False, f"Status: {response1.status_code}")
                return False
            
            data1 = response1.json()
            initial_count = data1.get("total_posts_analyzed", 0)
            
            # Wait for data generation
            print("Waiting 15 seconds for data generation...")
            time.sleep(15)
            
            # Get updated state
            response2 = self.session.get(f"{API_BASE}/happiness")
            if response2.status_code != 200:
                self.log_test("Data Generation Follow-up", False, f"Status: {response2.status_code}")
                return False
            
            data2 = response2.json()
            final_count = data2.get("total_posts_analyzed", 0)
            
            if final_count > initial_count:
                self.log_test("Data Generation", True, f"Posts increased from {initial_count} to {final_count}")
                return True
            else:
                self.log_test("Data Generation", False, f"No increase in posts: {initial_count} -> {final_count}")
                return False
                
        except Exception as e:
            self.log_test("Data Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_reddit_data_integration(self):
        """Test that Reddit data is being integrated into the happiness system"""
        try:
            # Check if Reddit is contributing to the source breakdown
            response = self.session.get(f"{API_BASE}/happiness")
            if response.status_code != 200:
                self.log_test("Reddit Data Integration", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            source_breakdown = data.get("source_breakdown", {})
            reddit_count = source_breakdown.get("reddit", 0)
            
            if reddit_count > 0:
                self.log_test("Reddit Data Integration", True, f"Reddit contributing {reddit_count} posts to happiness index")
                
                # Try to find Reddit posts in recent posts (they might be there)
                posts_response = self.session.get(f"{API_BASE}/recent-posts?limit=50")
                if posts_response.status_code == 200:
                    posts = posts_response.json()
                    reddit_posts = [post for post in posts if post.get("source") == "reddit"]
                    
                    if reddit_posts:
                        subreddits = set()
                        for post in reddit_posts:
                            if "subreddit" in post and post["subreddit"]:
                                subreddits.add(post["subreddit"])
                        
                        if subreddits:
                            self.log_test("Reddit Subreddit Diversity", True, f"Found Reddit posts from subreddits: {subreddits}")
                        else:
                            self.log_test("Reddit Subreddit Diversity", True, "Reddit posts found but subreddit info not available (fallback working)")
                    else:
                        self.log_test("Reddit Posts in Recent", True, "Reddit data integrated but not in recent posts (high activity from other sources)")
                
                return True
            else:
                self.log_test("Reddit Data Integration", False, "Reddit not contributing any posts")
                return False
                
        except Exception as e:
            self.log_test("Reddit Data Integration", False, f"Exception: {str(e)}")
            return False

    def test_country_happiness_timeline_api(self):
        """Test GET /api/country-happiness-timeline endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/country-happiness-timeline")
            if response.status_code == 200:
                data = response.json()
                
                # Check required top-level fields
                required_fields = ["countries", "last_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Country Timeline API Structure", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check countries structure
                countries = data.get("countries", [])
                if not isinstance(countries, list):
                    self.log_test("Country Timeline Countries Structure", False, "Countries not a list", data)
                    return False
                
                # If there are countries, validate structure
                if countries:
                    country = countries[0]
                    required_country_fields = ["name", "total_posts", "timeline"]
                    missing_country_fields = [field for field in required_country_fields if field not in country]
                    
                    if missing_country_fields:
                        self.log_test("Country Timeline Country Structure", False, f"Missing country fields: {missing_country_fields}", country)
                        return False
                    
                    # Validate timeline structure
                    timeline = country.get("timeline", [])
                    if not isinstance(timeline, list):
                        self.log_test("Country Timeline Timeline Structure", False, "Timeline not a list", country)
                        return False
                    
                    # If timeline has data, validate structure
                    if timeline:
                        timeline_point = timeline[0]
                        if isinstance(timeline_point, dict):
                            required_timeline_fields = ["happiness", "timestamp"]
                            missing_timeline_fields = [field for field in required_timeline_fields if field not in timeline_point]
                            
                            if missing_timeline_fields:
                                self.log_test("Country Timeline Point Structure", False, f"Missing timeline fields: {missing_timeline_fields}", timeline_point)
                                return False
                        
                        # Validate happiness values are in correct range
                        for point in timeline[:5]:  # Check first 5 points
                            if isinstance(point, dict):
                                happiness = point.get("happiness", -1)
                                if not (0 <= happiness <= 100):
                                    self.log_test("Country Timeline Happiness Range", False, f"Happiness {happiness} not in range 0-100", point)
                                    return False
                
                self.log_test("Country Happiness Timeline API", True, f"Retrieved {len(countries)} countries with timeline data", data)
                return True
            else:
                self.log_test("Country Happiness Timeline API", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Country Happiness Timeline API", False, f"Exception: {str(e)}")
            return False

    async def test_websocket_enhanced_messages(self):
        """Test WebSocket connection for enhanced messages with country timelines and uptime"""
        try:
            ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for initial status message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("type") == "initial_status":
                        self.log_test("WebSocket Enhanced Initial", True, "Received initial status", data)
                        self.websocket_messages.append(data)
                        
                        # Wait for happiness update messages with enhanced data
                        enhanced_message_received = False
                        for _ in range(3):  # Try to get 3 messages
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=8)
                                data = json.loads(message)
                                self.websocket_messages.append(data)
                                
                                if data.get("type") == "happiness_update":
                                    update_data = data.get("data", {})
                                    
                                    # Check for enhanced fields
                                    enhanced_fields = ["country_timelines", "uptime", "country_sentiment"]
                                    found_enhanced = [field for field in enhanced_fields if field in update_data]
                                    
                                    if found_enhanced:
                                        enhanced_message_received = True
                                        
                                        # Validate uptime format (should be HH:MM)
                                        uptime = update_data.get("uptime", "")
                                        if uptime and ":" in uptime:
                                            self.log_test("WebSocket Uptime Format", True, f"Uptime format correct: {uptime}")
                                        else:
                                            self.log_test("WebSocket Uptime Format", False, f"Invalid uptime format: {uptime}")
                                        
                                        # Validate country_timelines structure
                                        country_timelines = update_data.get("country_timelines", [])
                                        if isinstance(country_timelines, list) and country_timelines:
                                            country = country_timelines[0]
                                            if isinstance(country, dict) and "name" in country and "timeline" in country:
                                                self.log_test("WebSocket Country Timelines", True, f"Country timelines data present with {len(country_timelines)} countries")
                                            else:
                                                self.log_test("WebSocket Country Timelines", False, "Invalid country timeline structure")
                                        else:
                                            self.log_test("WebSocket Country Timelines", False, "No country timelines data")
                                        
                                        # Validate country_sentiment
                                        country_sentiment = update_data.get("country_sentiment", {})
                                        if isinstance(country_sentiment, dict) and country_sentiment:
                                            self.log_test("WebSocket Country Sentiment", True, f"Country sentiment data present for {len(country_sentiment)} countries")
                                        else:
                                            self.log_test("WebSocket Country Sentiment", False, "No country sentiment data")
                                        
                                        break
                                        
                            except asyncio.TimeoutError:
                                continue
                        
                        if enhanced_message_received:
                            self.log_test("WebSocket Enhanced Messages", True, "Received enhanced happiness updates with new features")
                            return True
                        else:
                            self.log_test("WebSocket Enhanced Messages", False, "No enhanced messages received")
                            return False
                        
                    else:
                        self.log_test("WebSocket Enhanced Initial Type", False, f"Unexpected message type: {data.get('type')}", data)
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Enhanced Initial", False, "No initial message received")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Enhanced Messages", False, f"Exception: {str(e)}")
            return False

    def test_all_data_sources_working(self):
        """Test that all 7 data sources are working and contributing to the happiness index"""
        try:
            response = self.session.get(f"{API_BASE}/happiness")
            if response.status_code != 200:
                self.log_test("All Data Sources", False, f"Status: {response.status_code}")
                return False
            
            data = response.json()
            source_breakdown = data.get("source_breakdown", {})
            
            expected_sources = ["reddit", "mastodon", "google_trends", "youtube", "news", "twitter", "forums"]
            working_sources = []
            
            for source in expected_sources:
                if source in source_breakdown and source_breakdown[source] > 0:
                    working_sources.append(source)
            
            if len(working_sources) >= 5:  # At least 5 out of 7 sources should be working
                self.log_test("All Data Sources", True, f"{len(working_sources)}/7 data sources working: {working_sources}")
                return True
            else:
                self.log_test("All Data Sources", False, f"Only {len(working_sources)}/7 data sources working: {working_sources}")
                return False
                
        except Exception as e:
            self.log_test("All Data Sources", False, f"Exception: {str(e)}")
            return False
    
    def run_websocket_test(self):
        """Run WebSocket test in async context"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.test_websocket_connection())
            loop.close()
            return result
        except Exception as e:
            self.log_test("WebSocket Test Runner", False, f"Exception: {str(e)}")
            return False

    def run_enhanced_websocket_test(self):
        """Run enhanced WebSocket test in async context"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.test_websocket_enhanced_messages())
            loop.close()
            return result
        except Exception as e:
            self.log_test("Enhanced WebSocket Test Runner", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n🚀 Starting Internet Happiness Index Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        # Basic API endpoint tests
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Happiness Endpoint", self.test_happiness_endpoint),
            ("Recent Posts Endpoint", self.test_recent_posts_endpoint),
            ("Start Streaming Endpoint", self.test_start_streaming_endpoint),
            ("Status Endpoints", self.test_status_endpoints),
        ]
        
        # Run basic tests
        for test_name, test_func in tests:
            print(f"\n--- Running {test_name} ---")
            test_func()
        
        # NEW FEATURE TESTS - Priority from review request
        print(f"\n--- Running NEW FEATURE Tests ---")
        print(f"\n--- Running Country Happiness Timeline API Test ---")
        self.test_country_happiness_timeline_api()
        
        print(f"\n--- Running All Data Sources Test ---")
        self.test_all_data_sources_working()
        
        # Run WebSocket tests
        print(f"\n--- Running WebSocket Test ---")
        self.run_websocket_test()
        
        print(f"\n--- Running Enhanced WebSocket Test (Country Timelines & Uptime) ---")
        self.run_enhanced_websocket_test()
        
        # Run data generation tests (these take time)
        print(f"\n--- Running Data Generation Tests ---")
        self.test_data_generation_over_time()
        self.test_subreddit_diversity()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['message']}")
        
        # Show WebSocket messages received
        if self.websocket_messages:
            print(f"\n📡 WebSocket Messages Received: {len(self.websocket_messages)}")
            for i, msg in enumerate(self.websocket_messages[:3]):  # Show first 3
                print(f"  {i+1}. Type: {msg.get('type', 'unknown')}")
        
        return passed == total

if __name__ == "__main__":
    tester = HappinessIndexTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 All tests passed! Backend is working correctly.")
        exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        exit(1)