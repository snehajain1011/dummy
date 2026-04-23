#!/usr/bin/env python3
"""
Test Conversation Tracking
"""

import asyncio
import aiohttp
import json

async def test_conversation_events():
    """Test sending conversation events"""
    base_url = "http://localhost:8004"
    
    # Test user speech
    user_event = {
        "type": "user_speech_text",
        "timestamp": 1234567890,
        "data": {
            "text": "Hello, can you help me?",
            "duration": 2500,
            "confidence": 0.95
        }
    }
    
    # Test AI speech
    ai_event = {
        "type": "ai_speech_text", 
        "timestamp": 1234567891,
        "data": {
            "text": "Of course! I'm here to help.",
            "duration": 3000
        }
    }
    
    # Test AI intent
    intent_event = {
        "type": "ai_intent",
        "timestamp": 1234567892,
        "data": {
            "intent": "Dashboard-GoToDashboard-1.0",
            "actionType": "navigate",
            "text": "Taking you to the dashboard",
            "confidence": 0.92
        }
    }
    
    events = [user_event, ai_event, intent_event]
    
    for event in events:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/conversation/event", json=event) as response:
                    if response.status == 200:
                        print(f"✅ {event['type']} sent successfully")
                    else:
                        print(f"❌ {event['type']} failed: {response.status}")
        except Exception as e:
            print(f"❌ Error sending {event['type']}: {e}")

if __name__ == "__main__":
    asyncio.run(test_conversation_events())