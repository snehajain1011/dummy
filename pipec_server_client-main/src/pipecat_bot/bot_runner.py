#!/usr/bin/env python3
"""
Bot Runner for initializing and running the Pipecat pipeline
(Simplified and Corrected Version with Full Prompt)
"""

import asyncio
import json
import sys
import time
from typing import Optional, Dict, Any
from loguru import logger

# Pipecat imports
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.services.livekit import LiveKitParams, LiveKitTransport
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.frames.frames import (
    TextFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
)
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService

from ..config import settings
from ..auth.token_service import TokenService
from ..tools import smart_action_executor, static_data_loader

# Fix for Windows
if sys.platform == "win32":
    def _setup_sigint_noop(self):
        pass
    PipelineRunner._setup_sigint = _setup_sigint_noop

class BotRunner:
    """Manages the Pipecat bot pipeline and LiveKit connection."""
    
    def __init__(self):
        self.runners: Dict[str, PipelineRunner] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        
        # Attach tools to the instance
        self.smart_action_executor = smart_action_executor
        self.static_data_loader = static_data_loader
        
    def _mask_sensitive_data(self, data: str, show_chars: int = 4) -> str:
        if not data or len(data) <= show_chars * 2:
            return "[MASKED]"
        return f"{data[:show_chars]}***{data[-show_chars:]}"
    
    async def start_bot(self, room_name: str, user_identity: str) -> bool:
        """Starts a pipeline for a specific room if one isn't already running."""
        if room_name in self.tasks and not self.tasks[room_name].done():
            logger.info(f"Bot already running for room [{room_name}]")
            return True

        logger.info(f"🚀 Starting bot for room [{room_name}]")
        
        # Create a background task to run the pipeline for this room
        task = asyncio.create_task(self._run_pipeline_for_room(room_name, user_identity))
        self.tasks[room_name] = task
        return True

    async def stop_bot(self, room_name: str) -> bool:
        """Stops the pipeline for a specific room."""
        if room_name not in self.tasks or self.tasks[room_name].done():
            logger.warning(f"Bot not running or already stopped for room [{room_name}]")
            return True

        logger.info(f"🛑 Stopping bot for room [{room_name}]")
        
        runner = self.runners.get(room_name)
        if runner:
            await runner.stop()

        task = self.tasks.get(room_name)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Bot task for room [{room_name}] cancelled successfully.")
        
        # Clean up references
        if room_name in self.runners:
            del self.runners[room_name]
        if room_name in self.tasks:
            del self.tasks[room_name]
            
        return True

    async def _run_pipeline_for_room(self, room_name: str, user_identity: str):
        """The main pipeline logic for a single room connection."""
        try:
            # 1. SETUP CONNECTION
            token = TokenService.generate_livekit_token(
                user_identity=settings.livekit_participant_name,
                room_name=room_name
            )
            logger.info(f"🤖 Generated LiveKit token for bot in room [{room_name}]")

            transport = LiveKitTransport(
                url=settings.livekit_url,
                token=token,
                room_name=room_name,
                params=LiveKitParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    vad_analyzer=SileroVADAnalyzer(),
                ),
            )

            # 2. SETUP SERVICES
            context = OpenAILLMContext()
            
            stt = DeepgramSTTService(api_key=settings.deepgram_api_key)
            
            llm = AnthropicLLMService(
                api_key=settings.claude_api_key,
                model=settings.claude_default_model,
            )
            llm._enable_metrics = False
            llm._enable_usage_metrics = False

            # Defensive wrapper for the LLM token counting TypeError
            original_process_context = llm._process_context
            async def logged_process_context(context):
                try:
                    return await original_process_context(context)
                except TypeError as e:
                    logger.error(f"❌ LLM_ERROR (TypeError): {e}. Suppressing traceback.")
                    return "I'm sorry, I encountered a technical issue. Could you please repeat that?"
                except Exception as e:
                    logger.error(f"❌ LLM_ERROR (General): {e}")
                    return "An unexpected error occurred. Please try again."
            llm._process_context = logged_process_context

            tts = ElevenLabsTTSService(
                api_key=settings.elevenlabs_api_key,
                voice_id=settings.elevenlabs_voice_id,
                streaming_mode=True,
            )

            # 3. SETUP PROMPT AND ACTION LOGIC
            # --- THIS IS THE FULL, CORRECTED SYSTEM PROMPT ---
            enhanced_system_prompt = """You are a helpful and friendly Website Assistant. Your goal is to help users by voice.

**CRITICAL INSTRUCTIONS:**
1.  **Be Conversational:** Always respond to the user in a natural, helpful, and friendly way.
2.  **Perform Actions:** When a user asks you to do something like "clear the logs" or "toggle monitoring", you must do two things:
    - First, say a confirmation message like "Okay, clearing the logs for you now!"
    - **Second, you MUST end your response with the special tag: <Execute>Action</Execute>**

**EXAMPLES:**

User: "Hey, can you clear the logs for me?"
Your Response: "Of course, I'll clear those logs for you right away! <Execute>Action</Execute>"

User: "I want to toggle the monitoring dashboard."
Your Response: "No problem, toggling the monitoring dashboard now. <Execute>Action</Execute>"

User: "What can you do?"
Your Response: "I can help you interact with this website. For example, I can clear the logs or toggle the monitoring dashboard for you."

**IMPORTANT:** The `<Execute>Action</Execute>` tag is your way of pressing the button. You must include it in your response whenever you are performing an action for the user.
"""
            context.add_message({"role": "user", "content": f"SYSTEM INSTRUCTIONS: {enhanced_system_prompt}"})

            accumulated_text = ""
            original_tts_process = tts.process_frame
            async def smart_tts_process(frame, direction):
                nonlocal accumulated_text
                if hasattr(frame, 'text') and frame.text:
                    accumulated_text += frame.text
                    if '<Execute>Action</Execute>' in accumulated_text:
                        logger.info(f"🎯 AI is requesting an action!")
                        
                        if 'clear' in accumulated_text.lower() and 'log' in accumulated_text.lower():
                            await self.smart_action_executor.generate_and_send_intent("clear logs", "/voice-chat", ["monitoring-toggle-btn", "clear-logs-btn"])
                        elif 'toggle' in accumulated_text.lower() and 'monitoring' in accumulated_text.lower():
                            await self.smart_action_executor.generate_and_send_intent("toggle monitoring", "/voice-chat", ["monitoring-toggle-btn", "clear-logs-btn"])
                        
                        accumulated_text = "" # Reset after execution
                    
                    if '<Execute>Action</Execute>' in frame.text:
                        frame.text = frame.text.replace('<Execute>Action</Execute>', '')
                return await original_tts_process(frame, direction)
            tts.process_frame = smart_tts_process

            # 4. BUILD AND RUN PIPELINE
            context_aggregator = llm.create_context_aggregator(context)
            pipeline = Pipeline([
                transport.input(),
                stt,
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ])

            runner = PipelineRunner()
            self.runners[room_name] = runner

            task = PipelineTask(pipeline, params=PipelineParams(enable_metrics=False))

            @transport.event_handler("on_first_participant_joined")
            async def on_first_participant_joined(transport, participant):
                logger.info(f"👋 First participant [{participant.identity}] joined room [{room_name}]")
                await asyncio.sleep(2)
                greeting = "Hello! I'm your Website Assistant. How can I help you today?"
                await task.queue_frames([LLMFullResponseStartFrame(), TextFrame(greeting), LLMFullResponseEndFrame()])

            await runner.run(task)

        except asyncio.CancelledError:
            logger.info(f"Pipeline task for room [{room_name}] was cancelled.")
        except Exception as e:
            logger.error(f"❌ Pipeline for room [{room_name}] failed: {e}")
        finally:
            logger.info(f"✅ Pipeline for room [{room_name}] has finished.")
            if room_name in self.runners:
                del self.runners[room_name]
            if room_name in self.tasks:
                del self.tasks[room_name]

    def get_status(self) -> Dict[str, Any]:
        """Get bot status"""
        return {
            "is_running": len(self.tasks) > 0,
            "active_rooms": list(self.tasks.keys()),
        }

# Global bot runner instance
bot_runner = BotRunner()