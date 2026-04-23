#!/usr/bin/env python3
"""
Complete SSE Test Suite
Tests all SSE endpoints and features with raw JSON output
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, Any, List
from loguru import logger

# Configure logging
logger.remove()
logger.add("test/sse_test.log", level="DEBUG")
logger.add(lambda msg: print(msg, end=""), level="INFO")

class SSETestSuite:
    """Complete SSE test suite"""
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
        self.received_events = []
        self.connection_active = False
        
    def print_json(self, title: str, data: Any):
        """Print formatted JSON with title"""
        print(f"\n{'='*60}")
        print(f"📡 {title}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2, default=str))
        print(f"{'='*60}\n")
    
    async def test_sse_connection(self):
        """Test basic SSE connection"""
        print(f"\n🔌 TESTING SSE CONNECTION")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/navigation/stream",
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache"
                    }
                ) as response:
                    
                    self.print_json("SSE CONNECTION RESPONSE", {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "content_type": response.content_type
                    })
                    
                    if response.status == 200:
                        print("✅ SSE connection established")
                        
                        # Read first few events
                        event_count = 0
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            
                            if line.startswith('data: '):
                                event_data = line[6:]  # Remove 'data: ' prefix
                                try:
                                    event = json.loads(event_data)
                                    self.received_events.append(event)
                                    
                                    self.print_json(f"SSE EVENT #{event_count + 1}", event)
                                    
                                    event_count += 1
                                    if event_count >= 3:  # Stop after 3 events
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    print(f"⚠️ Invalid JSON in SSE event: {event_data}")
                        
                        print(f"✅ SSE connection test PASSED - received {event_count} events")
                    else:
                        print(f"❌ SSE connection test FAILED: {response.status}")
                        
        except Exception as e:
            print(f"❌ SSE connection test FAILED: {e}")
    
    async def test_navigation_command_endpoint(self):
        """Test navigation command endpoint"""
        print(f"\n🧭 TESTING NAVIGATION COMMAND ENDPOINT")
        
        test_commands = [
            {
                "type": "navigation_command",
                "timestamp": time.time(),
                "data": {
                    "action": "navigate",
                    "target": "/dashboard",
                    "instruction": "Navigate to dashboard page"
                }
            },
            {
                "type": "ui_action",
                "timestamp": time.time(),
                "data": {
                    "action_type": "click",
                    "target_element": "save-button",
                    "instruction": "Click the save button"
                }
            }
        ]
        
        for i, command in enumerate(test_commands):
            print(f"\n📤 Sending navigation command {i+1}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    self.print_json(f"NAVIGATION COMMAND REQUEST #{i+1}", command)
                    
                    async with session.post(
                        f"{self.base_url}/navigation/command",
                        json=command
                    ) as response:
                        status = response.status
                        
                        try:
                            data = await response.json()
                        except:
                            data = {"text": await response.text()}
                        
                        self.print_json(f"NAVIGATION COMMAND RESPONSE #{i+1}", {
                            "status_code": status,
                            "response": data
                        })
                        
                        if status == 200:
                            print(f"✅ Navigation command {i+1} PASSED")
                        else:
                            print(f"❌ Navigation command {i+1} FAILED: {status}")
                            
            except Exception as e:
                print(f"❌ Navigation command {i+1} FAILED: {e}")
    
    async def test_conversation_event_endpoint(self):
        """Test conversation event endpoint"""
        print(f"\n💬 TESTING CONVERSATION EVENT ENDPOINT")
        
        test_events = [
            {
                "type": "user_speech_text",
                "timestamp": time.time(),
                "data": {
                    "text": "Hello, can you help me navigate?",
                    "duration": 2500,
                    "confidence": 0.95
                }
            },
            {
                "type": "ai_speech_text",
                "timestamp": time.time(),
                "data": {
                    "text": "Of course! I can help you navigate the website.",
                    "duration": 3000,
                    "intent": None
                }
            },
            {
                "type": "ai_intent",
                "timestamp": time.time(),
                "data": {
                    "intent": "Dashboard-GoToDashboard-1.0",
                    "actionType": "navigate",
                    "text": "Taking you to the dashboard",
                    "confidence": 0.92,
                    "routeName": "/dashboard"
                }
            }
        ]
        
        for i, event in enumerate(test_events):
            print(f"\n📤 Sending conversation event {i+1}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    self.print_json(f"CONVERSATION EVENT REQUEST #{i+1}", event)
                    
                    async with session.post(
                        f"{self.base_url}/conversation/event",
                        json=event
                    ) as response:
                        status = response.status
                        
                        try:
                            data = await response.json()
                        except:
                            data = {"text": await response.text()}
                        
                        self.print_json(f"CONVERSATION EVENT RESPONSE #{i+1}", {
                            "status_code": status,
                            "response": data
                        })
                        
                        if status == 200:
                            print(f"✅ Conversation event {i+1} PASSED")
                        else:
                            print(f"❌ Conversation event {i+1} FAILED: {status}")
                            
            except Exception as e:
                print(f"❌ Conversation event {i+1} FAILED: {e}")
    
    async def test_ai_data_endpoint(self):
        """Test AI data endpoint"""
        print(f"\n🤖 TESTING AI DATA ENDPOINT")
        
        test_data = [
            {
                "type": "dashboard_data",
                "app_id": "test_dashboard",
                "data": {
                    "name": "Test Dashboard",
                    "routeName": "/test-dashboard",
                    "description": "Test dashboard for SSE testing",
                    "interactiveElements": [
                        {
                            "type": "button",
                            "testID": "test-button-1",
                            "textContent": "Test Button 1",
                            "accessibilityLabel": "Click test button 1"
                        },
                        {
                            "type": "input",
                            "testID": "test-input-1",
                            "textContent": "",
                            "accessibilityLabel": "Test input field"
                        }
                    ],
                    "intents": [
                        {
                            "schema": "action.test_button",
                            "text": "Click the test button"
                        }
                    ]
                }
            },
            {
                "type": "screen_status",
                "data": {
                    "current_page": "Test Dashboard",
                    "route": "/test-dashboard",
                    "elements_visible": ["test-button-1", "test-input-1"],
                    "user_action": "page_active"
                }
            },
            {
                "type": "user_command",
                "data": {
                    "command": "click the test button",
                    "timestamp": time.time()
                }
            }
        ]
        
        for i, data in enumerate(test_data):
            print(f"\n📤 Sending AI data {i+1}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    self.print_json(f"AI DATA REQUEST #{i+1}", data)
                    
                    async with session.post(
                        f"{self.base_url}/ai/data",
                        json=data
                    ) as response:
                        status = response.status
                        
                        try:
                            response_data = await response.json()
                        except:
                            response_data = {"text": await response.text()}
                        
                        self.print_json(f"AI DATA RESPONSE #{i+1}", {
                            "status_code": status,
                            "response": response_data
                        })
                        
                        if status == 200:
                            print(f"✅ AI data {i+1} PASSED")
                        else:
                            print(f"❌ AI data {i+1} FAILED: {status}")
                            
            except Exception as e:
                print(f"❌ AI data {i+1} FAILED: {e}")
    
    async def test_concurrent_sse_connections(self):
        """Test multiple concurrent SSE connections"""
        print(f"\n👥 TESTING CONCURRENT SSE CONNECTIONS")
        
        async def sse_listener(connection_id: int):
            """Listen to SSE events for a specific connection"""
            events_received = []
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/navigation/stream",
                        headers={"Accept": "text/event-stream"}
                    ) as response:
                        
                        if response.status == 200:
                            print(f"🔌 Connection {connection_id} established")
                            
                            # Listen for 10 seconds
                            start_time = time.time()
                            async for line in response.content:
                                if time.time() - start_time > 10:  # 10 second timeout
                                    break
                                    
                                line = line.decode('utf-8').strip()
                                if line.startswith('data: '):
                                    event_data = line[6:]
                                    try:
                                        event = json.loads(event_data)
                                        events_received.append(event)
                                        print(f"📡 Connection {connection_id} received: {event.get('type', 'unknown')}")
                                    except:
                                        pass
                        
                        return {
                            "connection_id": connection_id,
                            "status": response.status,
                            "events_count": len(events_received),
                            "events": events_received[:3]  # First 3 events only
                        }
                        
            except Exception as e:
                return {
                    "connection_id": connection_id,
                    "status": "error",
                    "error": str(e),
                    "events_count": 0
                }
        
        # Start multiple concurrent connections
        num_connections = 3
        tasks = [sse_listener(i) for i in range(num_connections)]
        
        # Also send some events while connections are active
        async def send_test_events():
            await asyncio.sleep(2)  # Wait for connections to establish
            
            for i in range(5):
                test_event = {
                    "type": "test_event",
                    "timestamp": time.time(),
                    "data": {
                        "message": f"Concurrent test event {i+1}",
                        "event_id": i+1
                    }
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.post(f"{self.base_url}/navigation/command", json=test_event)
                        print(f"📤 Sent test event {i+1}")
                        await asyncio.sleep(1)
                except:
                    pass
        
        # Run listeners and event sender concurrently
        event_sender_task = asyncio.create_task(send_test_events())
        results = await asyncio.gather(*tasks, return_exceptions=True)
        await event_sender_task
        
        self.print_json("CONCURRENT SSE TEST RESULTS", results)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == 200)
        print(f"✅ Concurrent SSE test: {successful}/{num_connections} connections successful")
    
    async def test_sse_event_types(self):
        """Test all different SSE event types"""
        print(f"\n🎭 TESTING ALL SSE EVENT TYPES")
        
        # Start SSE listener
        async def event_collector():
            collected_events = []
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/navigation/stream",
                        headers={"Accept": "text/event-stream"}
                    ) as response:
                        
                        start_time = time.time()
                        async for line in response.content:
                            if time.time() - start_time > 15:  # 15 second timeout
                                break
                                
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                event_data = line[6:]
                                try:
                                    event = json.loads(event_data)
                                    collected_events.append(event)
                                    print(f"📡 Collected event: {event.get('type', 'unknown')}")
                                except:
                                    pass
                        
                        return collected_events
                        
            except Exception as e:
                print(f"❌ Event collector failed: {e}")
                return []
        
        # Start event collector
        collector_task = asyncio.create_task(event_collector())
        
        # Wait a moment for connection
        await asyncio.sleep(2)
        
        # Send different types of events
        event_types = [
            {
                "type": "static_data_ready",
                "timestamp": time.time(),
                "data": {"app_id": "test", "message": "Static data loaded"}
            },
            {
                "type": "user_speech_text",
                "timestamp": time.time(),
                "data": {"text": "Test user speech", "confidence": 0.9}
            },
            {
                "type": "ai_speech_text",
                "timestamp": time.time(),
                "data": {"text": "Test AI response"}
            },
            {
                "type": "ai_intent",
                "timestamp": time.time(),
                "data": {"intent": "Test-Intent-1.0", "actionType": "click"}
            },
            {
                "type": "navigation_command",
                "timestamp": time.time(),
                "data": {"action": "navigate", "target": "/test"}
            },
            {
                "type": "tool_log",
                "timestamp": time.time(),
                "data": {"tool": "test_tool", "action": "test_action"}
            }
        ]
        
        for event in event_types:
            try:
                async with aiohttp.ClientSession() as session:
                    # Try both endpoints
                    if event["type"] in ["user_speech_text", "ai_speech_text", "ai_intent"]:
                        endpoint = "/conversation/event"
                    else:
                        endpoint = "/navigation/command"
                    
                    await session.post(f"{self.base_url}{endpoint}", json=event)
                    print(f"📤 Sent {event['type']} event")
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Failed to send {event['type']}: {e}")
        
        # Wait for events to be collected
        await asyncio.sleep(3)
        
        # Get collected events
        collected_events = await collector_task
        
        self.print_json("ALL COLLECTED SSE EVENTS", collected_events)
        
        # Analyze event types received
        event_type_counts = {}
        for event in collected_events:
            event_type = event.get('type', 'unknown')
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        self.print_json("EVENT TYPE SUMMARY", event_type_counts)
        
        print(f"✅ Event types test completed - {len(collected_events)} total events")
    
    async def run_all_tests(self):
        """Run complete SSE test suite"""
        print(f"\n🚀 STARTING COMPLETE SSE TEST SUITE")
        print(f"🎯 Target server: {self.base_url}")
        
        start_time = time.time()
        
        try:
            await self.test_sse_connection()
            await self.test_navigation_command_endpoint()
            await self.test_conversation_event_endpoint()
            await self.test_ai_data_endpoint()
            await self.test_concurrent_sse_connections()
            await self.test_sse_event_types()
            
            duration = time.time() - start_time
            
            print(f"\n🎉 ALL SSE TESTS COMPLETED")
            print(f"⏱️ Total duration: {duration:.2f} seconds")
            print(f"📡 Total events received: {len(self.received_events)}")
            
            # Final summary
            self.print_json("FINAL SSE TEST SUMMARY", {
                "duration_seconds": duration,
                "total_events_received": len(self.received_events),
                "test_timestamp": time.time(),
                "endpoints_tested": [
                    "/navigation/stream",
                    "/navigation/command", 
                    "/conversation/event",
                    "/ai/data"
                ]
            })
            
        except Exception as e:
            print(f"❌ SSE TEST SUITE FAILED: {e}")
            raise

async def main():
    """Main test runner"""
    test_suite = SSETestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())