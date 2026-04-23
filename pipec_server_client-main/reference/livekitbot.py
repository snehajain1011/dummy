import asyncio
import os
import sys
import time
import jwt
from dotenv import load_dotenv

from telemetry import Telemetry, logger  # logger comes from telemetry

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

load_dotenv(override=True)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME")
LIVEKIT_PARTICIPANT_NAME = os.getenv("LIVEKIT_PARTICIPANT_NAME", "InterviewBuddy")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
TOKEN_TTL_SECONDS = 7200

# Telemetry instance
telemetry = Telemetry(output_filename="performance_log.csv", level="DEBUG")

if sys.platform == "win32":
    def _setup_sigint_noop(self):
        pass
    PipelineRunner._setup_sigint = _setup_sigint_noop

def generate_livekit_token(api_key, api_secret, room, participant_name="ai_assistant", ttl_seconds=TOKEN_TTL_SECONDS):
    now = int(time.time())
    payload = {
        'iss': api_key, 'sub': participant_name, 'nbf': now, 'exp': now + ttl_seconds,
        'name': participant_name,
        'video': {'roomJoin': True, 'room': room, 'canPublish': True, 'canSubscribe': True, 'canPublishData': True}
    }
    return jwt.encode(payload, api_secret, algorithm='HS256')

async def setup_livekit_connection():
    if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL, LIVEKIT_ROOM_NAME]):
        logger.error("LiveKit credentials not found. Check your .env.")
        sys.exit(1)

    token = generate_livekit_token(
        LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_ROOM_NAME,
        participant_name=LIVEKIT_PARTICIPANT_NAME, ttl_seconds=TOKEN_TTL_SECONDS
    )
    logger.info(f"Generated token for AI assistant in room: {LIVEKIT_ROOM_NAME}")
    return LIVEKIT_URL, token, LIVEKIT_ROOM_NAME

async def main():
    url, token, room_name = await setup_livekit_connection()

    transport = LiveKitTransport(
        url=url, token=token, room_name=room_name,
        params=LiveKitParams(audio_in_enabled=True, audio_out_enabled=True, vad_analyzer=SileroVADAnalyzer())
    )

    stt = DeepgramSTTService(api_key=DEEPGRAM_API_KEY)
    llm = AnthropicLLMService(api_key=CLAUDE_API_KEY, model=CLAUDE_DEFAULT_MODEL)
    tts = ElevenLabsTTSService(api_key=ELEVENLABS_API_KEY, voice_id=ELEVENLABS_VOICE_ID)

    context = OpenAILLMContext([{"role": "system", "content": "You are InterviewBuddy — a warm, friendly, and encouraging AI assistant..."}])
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline([
        transport.input(), stt, context_aggregator.user(), llm, tts,
        transport.output(), context_aggregator.assistant()
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True, idle_timeout_sec=0)
    )

    telemetry.attach_to(task=task, pipeline=pipeline)

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant_id):
        await asyncio.sleep(1)
        greeting_text = "Hello! I’m InterviewBuddy, your AI interview assistant. What role are you preparing for?"
        await task.queue_frames([LLMFullResponseStartFrame(), TextFrame(text=greeting_text), LLMFullResponseEndFrame()])
        context.add_message({"role": "assistant", "content": greeting_text})

    @transport.event_handler("on_data_received")
    async def on_data_received(transport, data, participant_id):
        logger.info(f"Received data from participant {participant_id}: {data}")

    logger.info(f"🚀 Starting InterviewBuddy AI assistant")
    logger.info(f"📍 Room: {room_name}")
    logger.info(f"🔗 LiveKit URL: {url}")
    logger.info(f"🤖 Ready to assist!")

    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
