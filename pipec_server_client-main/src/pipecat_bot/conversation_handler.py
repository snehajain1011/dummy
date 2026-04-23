#!/usr/bin/env python3
"""
Conversation Handler for Pipecat Integration
Processes STT/TTS events and extracts actual spoken text
"""

import asyncio
import time
from typing import Optional, Dict, Any
from loguru import logger

from ..tools.conversation_tracker import conversation_tracker


class ConversationHandler:
    """Handles conversation events from Pipecat STT/TTS"""
    
    def __init__(self):
        self.is_active = False
        self.current_user_speech = None
        self.current_ai_speech = None
        self.speech_start_time = None
        
    async def start_handling(self):
        """Start conversation handling"""
        self.is_active = True
        await conversation_tracker.start_tracking()
        logger.info("💬 Conversation handler started")
        logger.info("💬 Conversation tracker status: active")
        
    async def stop_handling(self):
        """Stop conversation handling"""
        self.is_active = False
        await conversation_tracker.stop_tracking()
        logger.info("💬 Conversation handler stopped")
        
    async def handle_user_started_speaking(self, frame: Any):
        """Handle user started speaking event"""
        if not self.is_active:
            return
            
        try:
            self.speech_start_time = time.time()
            logger.debug("👤 User started speaking")
            
        except Exception as e:
            logger.error(f"❌ Error handling user started speaking: {e}")
    
    async def handle_user_stopped_speaking(self, frame: Any):
        """Handle user stopped speaking event"""
        if not self.is_active:
            return
            
        try:
            # Calculate speech duration
            duration = None
            if self.speech_start_time:
                duration = (time.time() - self.speech_start_time) * 1000  # Convert to milliseconds
                self.speech_start_time = None
            
            logger.debug(f"👤 User stopped speaking (duration: {duration:.0f}ms)")
            
        except Exception as e:
            logger.error(f"❌ Error handling user stopped speaking: {e}")
    
    async def handle_transcription(self, frame: Any):
        """Handle transcription event from STT"""
        if not self.is_active:
            return
            
        try:
            # Extract text from transcription frame
            text = getattr(frame, 'text', None)
            if not text or not text.strip():
                return
                
            # Extract confidence if available
            confidence = getattr(frame, 'confidence', None)
            
            # Calculate duration
            duration = None
            if self.speech_start_time:
                duration = (time.time() - self.speech_start_time) * 1000
                self.speech_start_time = None
            
            logger.info(f"🎤 TRANSCRIPTION RECEIVED: '{text.strip()}' (confidence: {confidence})")
            
            # Process user speech
            await conversation_tracker.process_user_speech(
                text=text.strip(),
                duration=duration,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Error handling transcription: {e}")
    
    async def handle_llm_response_start(self, frame: Any):
        """Handle LLM response start event"""
        if not self.is_active:
            return
            
        try:
            logger.debug("🤖 AI started responding")
            
        except Exception as e:
            logger.error(f"❌ Error handling LLM response start: {e}")
    
    async def handle_llm_response_end(self, frame: Any):
        """Handle LLM response end event"""
        if not self.is_active:
            return
            
        try:
            # Extract text from LLM response
            text = getattr(frame, 'text', None)
            if not text or not text.strip():
                return
                
            # Process AI speech
            await conversation_tracker.process_ai_speech(
                text=text.strip(),
                duration=None,  # LLM doesn't provide duration
                intent=None  # Will be set by intent handler if needed
            )
            
        except Exception as e:
            logger.error(f"❌ Error handling LLM response end: {e}")
    
    async def handle_tts_speak(self, frame: Any):
        """Handle TTS speak event"""
        if not self.is_active:
            return
            
        try:
            # Extract text from TTS frame
            text = getattr(frame, 'text', None)
            if not text or not text.strip():
                return
                
            logger.info(f"🤖 TTS SPEAK RECEIVED: '{text.strip()}'")
            
            # Process AI speech (this is what actually gets spoken)
            await conversation_tracker.process_ai_speech(
                text=text.strip(),
                duration=None,
                intent=None
            )
            
        except Exception as e:
            logger.error(f"❌ Error handling TTS speak: {e}")
    
    async def handle_bot_interruption(self, frame: Any):
        """Handle bot interruption event"""
        if not self.is_active:
            return
            
        try:
            logger.info("🔄 Bot was interrupted by user")
            
        except Exception as e:
            logger.error(f"❌ Error handling bot interruption: {e}")
    
    def get_conversation_log(self) -> list:
        """Get conversation log from tracker"""
        return conversation_tracker.get_conversation_log()
    
    def clear_conversation_log(self):
        """Clear conversation log"""
        conversation_tracker.clear_log()


# Global instance
conversation_handler = ConversationHandler() 