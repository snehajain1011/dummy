#!/usr/bin/env python3
"""
Quick Test - Basic functionality check
"""

import asyncio
import aiohttp
import json

async def quick_test():
    """Quick test of basic functionality"""
    base_url = "http://localhost:8004"
    
    print("🚀 Quick Test Starting...")
    
    # Test 1: Health check
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health") as response:
                data = await response.json()
                print(f"✅ Health: {response.status} - {data.get('status')}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
    
    # Test 2: SSE connection
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/navigation/stream") as response:
                print(f"✅ SSE: {response.status} - {response.content_type}")
                # Read one event
                async for line in response.content:
                    if line.startswith(b'data: '):
                        event = json.loads(line[6:].decode())
                        print(f"📡 First SSE event: {event.get('type')}")
                        break
    except Exception as e:
        print(f"❌ SSE failed: {e}")
    
    # Test 3: Send test event
    try:
        test_event = {
            "type": "test_event",
            "timestamp": 1234567890,
            "data": {"message": "Quick test event"}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/navigation/command", json=test_event) as response:
                data = await response.json()
                print(f"✅ Event send: {response.status} - {data.get('status')}")
    except Exception as e:
        print(f"❌ Event send failed: {e}")
    
    print("🎉 Quick test completed!")

if __name__ == "__main__":
    asyncio.run(quick_test())