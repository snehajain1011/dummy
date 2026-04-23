#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import asyncio
import json
import os
import sys
import time
import jwt
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import motor.motor_asyncio
from anthropic import Anthropic
import threading

# Pipecat imports
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.services.livekit import LiveKitParams, LiveKitTransport
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.frames.frames import (
    BotInterruptionFrame,
    TextFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TTSSpeakFrame,
)
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService

# Load environment variables
load_dotenv(override=True)

# === Configuration Section ===
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME")
LIVEKIT_PARTICIPANT_NAME = os.getenv("LIVEKIT_PARTICIPANT_NAME", "InterviewBuddy")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "xx")
CLAUDE_DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "xx")
ELEVENLABS_VOICE = os.getenv("ELEVENLABS_VOICE", "en-US-Neural")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "xx")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "xx")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://dev:tetst@cluster0.ldalez8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
TOKEN_TTL_SECONDS = 7200

logger.remove()
logger.add(sys.stderr, level="DEBUG")

# === Fix for Windows ===
if sys.platform == "win32":
    def _setup_sigint_noop(self):
        pass
    PipelineRunner._setup_sigint = _setup_sigint_noop

# === Pydantic Models ===
class AppIntentItemDto(BaseModel):
    hash: str = Field(..., description="component hash")
    text: str = Field(..., description="Display text for the intent")
    componentType: str = Field(..., description="Component type")

class ProcessComponentsDto(BaseModel):
    components: List[AppIntentItemDto] = Field(..., description="List of components")
    userInput: str = Field(..., description="User input text")
    deviceId: Optional[str] = Field(None, description="Device ID")
    screen: Optional[str] = Field(None, description="Current screen")

class ComponentDto(BaseModel):
    _id: Optional[str] = None
    name: Optional[str] = None
    routeName: Optional[str] = None
    description: Optional[str] = None
    navigatorType: Optional[str] = None

class ComponentResponseFormatDto(BaseModel):
    intent: str
    routeName: Optional[str] = None
    text: str
    actionType: str = "navigate"
    confidence: float = 0.7
    timestamp: str
    component: Optional[ComponentDto] = None
    audioData: Optional[str] = None
    audioFormat: Optional[str] = None
    claudeError: Optional[bool] = None
    elevenLabsError: Optional[bool] = None
    systemError: Optional[bool] = None
    errorMessage: Optional[str] = None

# === MongoDB Connection ===
class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            # Try to get default database, if not available use a specific database name
            try:
                self.db = self.client.get_default_database()
            except Exception:
                # If no default database, use 'test' or extract from URI
                if 'mongodb+srv://' in MONGODB_URI and '/' in MONGODB_URI.split('/')[-1]:
                    db_name = MONGODB_URI.split('/')[-1].split('?')[0]
                    if db_name:
                        self.db = self.client[db_name]
                    else:
                        self.db = self.client['test']  # fallback database name
                else:
                    self.db = self.client['test']  # fallback database name
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB successfully (database: {self.db.name})")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise - allow server to start in mock mode
            self.client = None
            self.db = None
            logger.warning("Starting server in mock mode without MongoDB")
    
    async def get_app_by_api_key(self, app_id: str, api_key: str):
        try:
            if not self.db:
                # Mock mode - return valid response for testing
                logger.info(f"Mock mode: Validating API key for app {app_id}")
                return {"mock": True, "app": app_id, "keys": {"api": {"key": api_key}}}
            
            return await self.db.apikeys.find_one({
                "app": app_id,
                "keys.api.key": api_key
            })
        except Exception as e:
            logger.error(f"Error fetching app by API key: {e}")
            return {"mock": True, "app": app_id, "keys": {"api": {"key": api_key}}}
    
    async def get_components(self, app_id: str):
        try:
            if not self.db:
                # Mock mode - return sample components for testing
                logger.info(f"Mock mode: Returning sample components for app {app_id}")
                return [
                    {
                        "_id": "comp_1",
                        "name": "Home Screen",
                        "routeName": "home",
                        "description": "Main home screen",
                        "navigatorType": "screen",
                        "interactiveElements": []
                    },
                    {
                        "_id": "comp_2", 
                        "name": "Settings Screen",
                        "routeName": "settings",
                        "description": "Application settings",
                        "navigatorType": "screen",
                        "interactiveElements": []
                    }
                ]
            
            components = await self.db.components.find({
                "app": app_id
            }).to_list(length=None)
            return components
        except Exception as e:
            logger.error(f"Error fetching components: {e}")
            return []
    
    async def get_intents(self, app_id: str):
        try:
            if not self.db:
                # Mock mode - return sample intents for testing
                logger.info(f"Mock mode: Returning sample intents for app {app_id}")
                return [
                    {
                        "_id": "intent_1",
                        "schema": "navigation",
                        "text": "Navigate to different screens",
                        "app": app_id
                    },
                    {
                        "_id": "intent_2",
                        "schema": "action", 
                        "text": "Perform actions like delete, create, update",
                        "app": app_id
                    }
                ]
            
            intents = await self.db.intents.find({
                "app": app_id
            }).to_list(length=None)
            return intents
        except Exception as e:
            logger.error(f"Error fetching intents: {e}")
            return []

# === Claude Intent Service ===
class ClaudeIntentService:
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY != "xx" else None
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text.split()) * 1.3
    
    def get_action_hints(self, user_input: str) -> Dict[str, str]:
        """Analyze user input to suggest action type"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['click', 'tap', 'press', 'select']):
            return {"suggested": "click", "reason": "action_verb"}
        elif any(word in user_lower for word in ['go to', 'navigate', 'open', 'show me']):
            return {"suggested": "navigate", "reason": "navigation_intent"}
        elif any(word in user_lower for word in ['what', 'how', 'why', 'tell me', 'explain']):
            return {"suggested": "audio_only", "reason": "information_request"}
        else:
            return {"suggested": "navigate", "reason": "default"}
    
    async def detect_intent(
        self, 
        components: List[Dict], 
        user_input: str, 
        app_id: str,
        app_intents: List[Dict] = None,
        dom_data: List[AppIntentItemDto] = None,
        current_screen: str = "home"
    ) -> Dict[str, Any]:
        """Detect user intent using Claude API"""
        try:
            if not self.client:
                raise Exception("Claude API not configured")
            
            app_intents = app_intents or []
            dom_data = dom_data or []
            
            # Prepare components info
            components_info = []
            for component in components:
                comp_info = {
                    "name": component.get("name", ""),
                    "routeName": component.get("routeName", ""),
                    "description": component.get("description", ""),
                    "elements": ""
                }
                
                # Process interactive elements if available
                interactive_elements = component.get("interactiveElements", [])
                if interactive_elements:
                    elements = []
                    for el in interactive_elements:
                        if el.get("type", "").lower() != el.get("testID", "").lower():
                            element_str = f"{el.get('type', '')}:{el.get('testID', '')}"
                            if el.get("textContent"):
                                element_str += f":{el.get('textContent')}"
                            elements.append(element_str)
                    comp_info["elements"] = "|".join(elements)
                
                components_info.append(comp_info)
            
            # Prepare DOM info
            dom_info = ""
            if dom_data:
                dom_info = "\n".join([f"{d.hash}|{d.text}|{d.componentType}" for d in dom_data])
            
            # Prepare intents info
            intents_info = ""
            if app_intents:
                intents_info = "\n".join([f"{intent.get('schema', '')}: {intent.get('text', '')}" for intent in app_intents])
            
            # Get action hints
            action_hints = self.get_action_hints(user_input)
            
            # Create optimized prompt
            suggested_action = action_hints['suggested']
            dom_elements_section = f"DOM_ELEMENTS:\n{dom_info}" if dom_info else ""
            faq_intents_section = f"FAQ_INTENTS:\n{intents_info}" if intents_info else ""
            
            prompt = f"""Analyze user intent and respond with JSON only.

USER: "{user_input}"
CURRENT_SCREEN: {current_screen}
ACTION_HINTS: {action_hints}

AVAILABLE_SCREENS: {json.dumps(components_info)}
{dom_elements_section}
{faq_intents_section}

LOGIC:
1. If DOM match found → use hash as intent, routeName={current_screen} for clicks
2. If screen navigation needed → use matching routeName from screens
3. If info query → use audio_only with FAQ content

REQUIRED_JSON_FORMAT:
{{
    "intent": "string",
    "routeName": "valid_route_from_screens", 
    "responseText": "user_friendly_response",
    "actionType": "{suggested_action}",
    "confidence": 0.9,
    "actionMetadata": {{"elementId": "if_click_action"}}
}}"""
            
            logger.debug(f"Prompt length: {len(prompt)}")
            
            # Make Claude API call
            response = self.client.messages.create(
                model=CLAUDE_DEFAULT_MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text
            logger.debug(f"Claude response: {response_text}")
            
            # Extract JSON from response
            try:
                # Find JSON in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                
                # Validate and set defaults
                result.setdefault("intent", "Unknown")
                result.setdefault("routeName", current_screen)
                result.setdefault("responseText", "I understand your request.")
                result.setdefault("actionType", action_hints["suggested"])
                result.setdefault("confidence", 0.7)
                result.setdefault("actionMetadata", {})
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse Claude response: {e}")
                # Return fallback response
                return {
                    "intent": "ParseError",
                    "routeName": current_screen,
                    "responseText": "I understand your request, but had trouble processing it fully.",
                    "actionType": action_hints["suggested"],
                    "confidence": 0.5,
                    "actionMetadata": {}
                }
                
        except Exception as e:
            logger.error(f"Error in detect_intent: {e}")
            raise

# === FastAPI App ===
app = FastAPI(title="Enhanced LiveKit Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
mongodb_service = MongoDBService()
claude_service = ClaudeIntentService()
livekit_task = None

@app.on_event("startup")
async def startup_event():
    await mongodb_service.connect()

def generate_livekit_token(api_key: str, api_secret: str, room: str, participant_name: str = "ai_assistant", ttl_seconds: int = TOKEN_TTL_SECONDS):
    now = int(time.time())
    payload = {
        'iss': api_key,
        'sub': participant_name,
        'nbf': now,
        'exp': now + ttl_seconds,
        'name': participant_name,
        'video': {
            'roomJoin': True,
            'room': room,
            'canPublish': True,
            'canSubscribe': True,
            'canPublishData': True,
            'hidden': False
        }
    }
    return jwt.encode(payload, api_secret, algorithm='HS256')

async def fallback_pattern_matching(components: List[AppIntentItemDto], user_input: str, app_id: str, screen: str = "home") -> ComponentResponseFormatDto:
    """Fallback pattern matching when Claude fails"""
    user_lower = user_input.lower()
    
    # Simple keyword matching
    for component in components:
        if any(word in user_lower for word in component.text.lower().split()):
            return ComponentResponseFormatDto(
                intent=component.hash,
                routeName=screen,
                text=f"I found a match for '{component.text}'. Let me help you with that.",
                actionType="click",
                confidence=0.6,
                timestamp=datetime.now().isoformat(),
                component=ComponentDto(
                    _id=component.hash,
                    name=component.text,
                    routeName=screen,
                    description=component.text,
                    navigatorType=component.componentType
                )
            )
    
    # Default fallback
    return ComponentResponseFormatDto(
        intent="Unknown",
        routeName=screen,
        text="I understand you're looking for something. Could you please be more specific?",
        actionType="audio_only",
        confidence=0.3,
        timestamp=datetime.now().isoformat()
    )

@app.post("/app/{app_id}/app-intents")
async def process_app_intents(
    app_id: str,
    process_components_dto: ProcessComponentsDto,
    x_api_key: str = Header(..., alias="X-API-Key")
) -> ComponentResponseFormatDto:
    """Process DOM components data with Claude intent service"""
    start_time = time.time()
    logger.info(f"Starting processAppIntents for app {app_id}")
    
    try:
        # Verify API key
        api_key_doc = await mongodb_service.get_app_by_api_key(app_id, x_api_key)
        if not api_key_doc:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get components and intents from MongoDB
        components_with_interactive_elements, developer_intents = await asyncio.gather(
            mongodb_service.get_components(app_id),
            mongodb_service.get_intents(app_id)
        )
        
        components = process_components_dto.components
        user_input = process_components_dto.userInput
        device_id = process_components_dto.deviceId
        screen = process_components_dto.screen or "home"
        
        logger.info(f"Processing request for app {app_id}, screen: {screen}")
        
        # If no components provided, fetch from app data
        if not components:
            logger.info(f"No components provided, fetching from app {app_id}")
            app_components = components_with_interactive_elements
            components = [
                AppIntentItemDto(
                    hash=str(comp.get("_id", "")),
                    text=comp.get("description", comp.get("routeName", "")),
                    componentType=comp.get("navigatorType", "screen")
                )
                for comp in app_components
            ]
            logger.info(f"Fetched {len(components)} components")
        
        if not components:
            raise HTTPException(status_code=400, detail="No components available for intent processing")
        
        logger.info(f"Found {len(developer_intents)} developer-managed intents")
        
        # Use Claude to detect intent
        claude_response = None
        claude_error = None
        
        try:
            logger.info("Calling Claude intent service...")
            claude_start_time = time.time()
            
            claude_response = await claude_service.detect_intent(
                components_with_interactive_elements,
                user_input,
                app_id,
                developer_intents,
                components,
                screen
            )
            
            claude_time = time.time() - claude_start_time
            logger.info(f"Claude processing completed in {claude_time:.2f}s")
            
        except Exception as error:
            claude_error = error
            logger.error(f"Claude API failed: {error}")
            
            # Return fallback response
            fallback_response = await fallback_pattern_matching(components, user_input, app_id, screen)
            fallback_response.text = f"I'm having trouble with my AI processing right now. {fallback_response.text}"
            fallback_response.claudeError = True
            fallback_response.errorMessage = "Claude AI service is temporarily unavailable"
            return fallback_response
        
        # Find matched component
        route_name = claude_response.get("routeName", screen)
        matched_component = None
        
        for comp in components:
            if (comp.hash == claude_response.get("intent") or 
                claude_response.get("intent", "").lower() in comp.text.lower()):
                matched_component = comp
                break
        
        if not matched_component:
            logger.warn(f"No component found for route: {route_name}")
        
        action_type = claude_response.get("actionType", "navigate")
        
        # TODO: Add audio generation with ElevenLabs if needed
        audio_response = {"audioData": "", "audioFormat": ""}
        
        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time:.2f}s")
        
        # Return structured response
        response = ComponentResponseFormatDto(
            intent=claude_response.get("intent", "Unknown"),
            routeName=route_name,
            text=claude_response.get("responseText", "I understand your request."),
            actionType=action_type,
            confidence=claude_response.get("confidence", 0.7),
            timestamp=datetime.now().isoformat(),
            component=ComponentDto(
                _id=matched_component.hash if matched_component else None,
                name=matched_component.text if matched_component else None,
                routeName=route_name,
                description=matched_component.text if matched_component else None,
                navigatorType=matched_component.componentType if matched_component else None
            ) if matched_component else None,
            audioData=audio_response.get("audioData"),
            audioFormat=audio_response.get("audioFormat")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as error:
        total_time = time.time() - start_time
        logger.error(f"Error processing intent request ({total_time:.2f}s): {error}")
        
        # Final fallback
        try:
            fallback_response = await fallback_pattern_matching(
                process_components_dto.components or [], 
                process_components_dto.userInput, 
                app_id,
                process_components_dto.screen or "home"
            )
            
            fallback_response.text = f"I encountered a technical issue but found a response: {fallback_response.text}"
            fallback_response.systemError = True
            fallback_response.errorMessage = "Primary processing failed, using fallback"
            return fallback_response
            
        except Exception as fallback_error:
            logger.error(f"Error in fallback pattern matching: {fallback_error}")
            
            return ComponentResponseFormatDto(
                intent="SystemError",
                routeName=process_components_dto.screen or "home",
                text="I'm experiencing technical difficulties. Please try again in a moment.",
                actionType="audio_only",
                confidence=0,
                timestamp=datetime.now().isoformat(),
                systemError=True,
                claudeError=True,
                errorMessage="All processing methods failed - system temporarily unavailable"
            )

async def setup_livekit_connection():
    token = generate_livekit_token(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
        room=LIVEKIT_ROOM_NAME,
        participant_name=LIVEKIT_PARTICIPANT_NAME,
        ttl_seconds=TOKEN_TTL_SECONDS
    )

    logger.info(f"Generated token for AI assistant in room: {LIVEKIT_ROOM_NAME}")
    logger.info(f"Participant name: {LIVEKIT_PARTICIPANT_NAME}")

    return LIVEKIT_URL, token, LIVEKIT_ROOM_NAME

async def start_livekit_bot():
    """Start the LiveKit bot in background"""
    global livekit_task
    
    try:
        url, token, room_name = await setup_livekit_connection()

        transport = LiveKitTransport(
            url=url,
            token=token,
            room_name=room_name,
            params=LiveKitParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        )

        stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY)
        llm = AnthropicLLMService(
            api_key=CLAUDE_API_KEY,
            model=CLAUDE_DEFAULT_MODEL,
        )

        tts = ElevenLabsTTSService(
            api_key=ELEVENLABS_API_KEY,
            voice=ELEVENLABS_VOICE,
            voice_id=ELEVENLABS_VOICE_ID,
            streaming_mode=True,
            chunk_size=25,
            exaggeration=0.8,
            temperature=0.6,
            cfg_weight=0.2,
            context_window=20,
            fade_duration=0.02,
            reconnect_on_interrupt=False,
        )

        messages = [
            {
                "role": "system",
                "content": """
                You are InterviewBuddy — a warm, friendly, and encouraging AI assistant dedicated to helping users prepare for job interviews. You always communicate in **English**.

                **Your role:**
                - Engage users in conversations about their upcoming interviews, career goals, and preparation strategies.
                - Ask thoughtful questions about the roles they're applying for, their strengths, weaknesses, and recent preparation.
                - Offer support, encouragement, and actionable tips to improve their interview performance.
                - Help users practice common interview questions, discuss their experiences, and boost their confidence.

                **Guidelines for all responses:**
                - Respond only in English.
                - Use a conversational, simple, and motivating tone.
                - Keep answers and questions short — 2-3 sentences per turn.
                - Always prompt the user to share more about their interview prep, recent experiences, or concerns.
                - If the user goes off-topic, gently guide the conversation back to interview preparation and professional growth.
                - When someone first speaks to you, greet them warmly and introduce yourself as InterviewBuddy.

                **Examples:**
                - Hi there! I'm InterviewBuddy, your AI interview assistant. What role are you preparing for right now?
                - What's your biggest strength, and how do you usually showcase it in interviews?
                - Can you tell me about a recent interview experience you had?
                - Great progress! Would you like to practice some common interview questions together?

                Be supportive, practical, and always eager to help the user succeed in their job search journey!
                """
            },
        ]

        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        runner = PipelineRunner()

        task = PipelineTask(
            Pipeline(
                [
                    transport.input(),
                    stt,
                    context_aggregator.user(),
                    llm,
                    tts,
                    transport.output(),
                    context_aggregator.assistant(),
                ]
            ),
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant_id):
            await asyncio.sleep(1)
            greeting_text = "Hello! I'm your AI assistant, ready to help with your interview preparation!"
            await task.queue_frames([
                LLMFullResponseStartFrame(),
                TextFrame(text=greeting_text),
                LLMFullResponseEndFrame()
            ])
            context.add_message({
                "role": "assistant",
                "content": greeting_text
            })

        @transport.event_handler("on_data_received")
        async def on_data_received(transport, data, participant_id):
            logger.info(f"Received data from participant {participant_id}: {data}")
            try:
                json_data = json.loads(data)
                await task.queue_frames([
                    BotInterruptionFrame(),
                    UserStartedSpeakingFrame(),
                    TranscriptionFrame(
                        user_id=participant_id,
                        timestamp=json_data.get("timestamp", int(time.time() * 1000)),
                        text=json_data.get("message", ""),
                    ),
                    UserStoppedSpeakingFrame(),
                ])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {e}")
            except Exception as e:
                logger.error(f"Error processing data: {e}")

        logger.info(f"🚀 Starting Enhanced LiveKit AI assistant")
        logger.info(f"📍 Room: {room_name}")
        logger.info(f"🔗 LiveKit URL: {url}")
        logger.info(f"🤖 Ready to assist with interview preparation!")

        await runner.run(task)
        
    except Exception as e:
        logger.error(f"Error starting LiveKit bot: {e}")

@app.get("/")
async def root():
    return {"message": "Enhanced LiveKit Server is running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/start-livekit")
async def start_livekit():
    """Endpoint to start LiveKit bot"""
    global livekit_task
    
    if livekit_task and not livekit_task.done():
        return {"message": "LiveKit bot is already running"}
    
    # Start LiveKit bot in background
    livekit_task = asyncio.create_task(start_livekit_bot())
    return {"message": "LiveKit bot started successfully"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🌟 Starting Enhanced LiveKit Server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
