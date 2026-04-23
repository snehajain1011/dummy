#!/usr/bin/env python3
"""
Test client for the Enhanced LiveKit Server
This demonstrates how to call the app-intents endpoint
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any

# Test configuration
SERVER_URL = "http://localhost:8000"
TEST_APP_ID = "your_app_id_here"
TEST_API_KEY = "your_api_key_here"

# Sample test data
SAMPLE_COMPONENTS = [
    {
        "hash": "btn_delete_ticket_123",
        "text": "Delete Ticket",
        "componentType": "button"
    },
    {
        "hash": "nav_home_456",
        "text": "Go to Home",
        "componentType": "navigation"
    },
    {
        "hash": "btn_create_user_789",
        "text": "Create New User",
        "componentType": "button"
    },
    {
        "hash": "screen_settings_101",
        "text": "Settings Screen",
        "componentType": "screen"
    }
]

async def test_app_intents_endpoint(user_input: str, components: List[Dict] = None, screen: str = "home"):
    """Test the app-intents endpoint"""
    
    if components is None:
        components = SAMPLE_COMPONENTS
    
    # Prepare request data
    request_data = {
        "components": components,
        "userInput": user_input,
        "deviceId": "test_device_123",
        "screen": screen
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": TEST_API_KEY
    }
    
    url = f"{SERVER_URL}/app/{TEST_APP_ID}/app-intents"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"🚀 Testing endpoint: {url}")
            print(f"📝 User Input: '{user_input}'")
            print(f"📱 Screen: {screen}")
            print(f"🔧 Components: {len(components)} items")
            print("-" * 50)
            
            async with session.post(url, json=request_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ SUCCESS!")
                    print(f"Intent: {result.get('intent')}")
                    print(f"Route Name: {result.get('routeName')}")
                    print(f"Action Type: {result.get('actionType')}")
                    print(f"Confidence: {result.get('confidence')}")
                    print(f"Response Text: {result.get('text')}")
                    
                    if result.get('component'):
                        print(f"Matched Component: {result['component'].get('name')}")
                    
                    if result.get('claudeError'):
                        print("⚠️  Claude API had issues")
                    
                    if result.get('errorMessage'):
                        print(f"Error Message: {result.get('errorMessage')}")
                        
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ ERROR {response.status}: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return None

async def test_server_health():
    """Test if the server is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Server is healthy!")
                    print(f"Status: {result.get('status')}")
                    print(f"Timestamp: {result.get('timestamp')}")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

async def run_tests():
    """Run a series of tests"""
    print("=" * 60)
    print("🧪 ENHANCED LIVEKIT SERVER TEST SUITE")
    print("=" * 60)
    
    # Test server health
    print("\n1️⃣ Testing server health...")
    if not await test_server_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Test cases
    test_cases = [
        {
            "description": "Navigation request",
            "user_input": "I want to go to settings",
            "screen": "home"
        },
        {
            "description": "Button click request",
            "user_input": "Delete this ticket please",
            "screen": "tickets"
        },
        {
            "description": "Information request",
            "user_input": "What can I do here?",
            "screen": "dashboard"
        },
        {
            "description": "Create action request",
            "user_input": "I need to create a new user account",
            "screen": "admin"
        }
    ]
    
    print(f"\n2️⃣ Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        result = await test_app_intents_endpoint(
            user_input=test_case["user_input"],
            screen=test_case["screen"]
        )
        
        if result:
            print("✅ Test passed!")
        else:
            print("❌ Test failed!")
        
        print()
    
    print("🏁 Test suite completed!")

if __name__ == "__main__":
    print("Before running tests, make sure to:")
    print("1. Update TEST_APP_ID and TEST_API_KEY variables")
    print("2. Start the enhanced server: python enhanced_livekit_server.py")
    print("3. Ensure your .env file has the correct MongoDB and Claude API keys")
    print()
    
    # Run the tests
    asyncio.run(run_tests())
