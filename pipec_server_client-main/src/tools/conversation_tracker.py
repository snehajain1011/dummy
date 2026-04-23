#!/usr/bin/env python3
"""
Tool: Conversation Tracker
Monitors real-time conversation text from LiveKit STT/TTS
Sends actual spoken text via SSE immediately when speaking stops
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from loguru import logger
import aiohttp


class ConversationTracker:
    """Tracks real-time conversation text from STT/TTS events"""
    
    def __init__(self, server_url: str = "http://localhost:8004"):
        self.server_url = server_url
        self.conversation_log = []
        self.is_active = False
        self.last_user_speech = None
        self.last_ai_speech = None
        
    async def start_tracking(self):
        """Start conversation tracking"""
        self.is_active = True
        logger.info("💬 Conversation tracker started")
        
    async def stop_tracking(self):
        """Stop conversation tracking"""
        self.is_active = False
        logger.info("💬 Conversation tracker stopped")
        
    async def process_user_speech(self, text: str, duration: Optional[float] = None, confidence: Optional[float] = None):
        """
        Process user speech text from STT
        
        Args:
            text: Transcribed text from user
            duration: Duration of speech in milliseconds
            confidence: STT confidence score
        """
        if not self.is_active or not text.strip():
            return
            
        try:
            # Create conversation entry
            entry = {
                "timestamp": time.time(),
                "speaker": "user",
                "text": text.strip(),
                "duration": duration,
                "confidence": confidence
            }
            
            self.conversation_log.append(entry)
            self.last_user_speech = entry
            
            # Keep only last 100 entries
            if len(self.conversation_log) > 100:
                self.conversation_log = self.conversation_log[-100:]
            
            # Send via SSE
            event = {
                "type": "user_speech_text",
                "timestamp": time.time(),
                "data": {
                    "text": text.strip(),
                    "duration": duration,
                    "confidence": confidence
                }
            }
            
            await self._send_sse_event(event)
            logger.info(f"👤 User said: {text.strip()}")
            
        except Exception as e:
            logger.error(f"❌ Error processing user speech: {e}")
    
    async def process_ai_speech(self, text: str, duration: Optional[float] = None, intent: Optional[str] = None):
        """
        Process AI speech text from TTS
        
        Args:
            text: Text that AI spoke
            duration: Duration of speech in milliseconds
            intent: Associated intent if any
        """
        if not self.is_active or not text.strip():
            return
            
        try:
            # Create conversation entry
            entry = {
                "timestamp": time.time(),
                "speaker": "ai",
                "text": text.strip(),
                "duration": duration,
                "intent": intent
            }
            
            self.conversation_log.append(entry)
            self.last_ai_speech = entry
            
            # Keep only last 100 entries
            if len(self.conversation_log) > 100:
                self.conversation_log = self.conversation_log[-100:]
            
            # Send via SSE
            event = {
                "type": "ai_speech_text",
                "timestamp": time.time(),
                "data": {
                    "text": text.strip(),
                    "duration": duration,
                    "intent": intent
                }
            }
            
            await self._send_sse_event(event)
            logger.info(f"🤖 AI said: {text.strip()}")
            
        except Exception as e:
            logger.error(f"❌ Error processing AI speech: {e}")
    
    async def _send_sse_event(self, event: Dict[str, Any]):
        """Send event via SSE"""
        try:
            logger.info(f"📡 SENDING SSE EVENT: {event['type']} - {event}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/conversation/event",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ Failed to send SSE event: {response.status}")
                    else:
                        logger.info(f"✅ SSE EVENT SENT SUCCESSFULLY: {event['type']}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending SSE event: {e}")
    
    def get_conversation_log(self) -> list:
        """Get conversation log"""
        return self.conversation_log.copy()
    
    def get_last_user_speech(self) -> Optional[Dict]:
        """Get last user speech entry"""
        return self.last_user_speech
    
    def get_last_ai_speech(self) -> Optional[Dict]:
        """Get last AI speech entry"""
        return self.last_ai_speech
    
    def clear_log(self):
        """Clear conversation log"""
        self.conversation_log = []
        self.last_user_speech = None
        self.last_ai_speech = None
        logger.info("🧹 Conversation log cleared")


# Global instance
conversation_tracker = ConversationTracker() 