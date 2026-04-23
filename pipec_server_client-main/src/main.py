#!/usr/bin/env python3
"""Main FastAPI application entry point"""

import asyncio
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
import json
from datetime import datetime
import os
import glob

# --- Core Application Imports ---
from .config import settings
from .db.mongodb_service import mongodb_service

# --- Routers ---
# This is the router for /api/v1/token, which can be used for API-based auth
from .api.auth_router import router as api_auth_router
# This is the main router for the client, providing /auth/login
from .auth.auth_router import router as client_auth_router

# --- Tools and Bot ---
# Import the bot_runner to get status, but it's primarily controlled via the auth router
from .pipecat_bot.bot_runner import bot_runner
# Import the static_data_loader to be used directly by the /ai/data endpoint
from .tools.static_data_loader import static_data_loader

# --- Logging Configuration ---
logger.remove()
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
existing_logs = glob.glob(f"{log_dir}/run_*.log")
run_numbers = [int(f.split("run_")[1].split("_")[0]) for f in existing_logs if "run_" in f]
next_run = max(run_numbers, default=0) + 1
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f"{log_dir}/run_{next_run:03d}_{timestamp}.log"

logger.add(log_filename, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", enqueue=True)
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <5} | {message}")

logger.info(f"Logging to: {log_filename}")

# --- Application Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Qubekit Server...")
    try:
        await mongodb_service.connect()
        logger.info("✅ Database connection established")
        logger.info("✅ Server ready. Bot will start after user authentication.")
        yield
    finally:
        logger.info("🛑 Shutting down Qubekit Server...")
        await mongodb_service.disconnect()
        logger.info("✅ Database connection closed")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Qubekit Server",
    description="A modular voice AI server with LiveKit integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# This provides the /auth/login endpoint for your reverted App.js
app.include_router(client_auth_router)
# This provides the /api/v1/token endpoint for other potential clients
app.include_router(api_auth_router)

# --- Core Endpoints ---
@app.get("/")
async def root():
    return {"message": "Qubekit Server is running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot_status": bot_runner.get_status()}

# --- Server-Sent Events (SSE) Queues and Endpoint ---
navigation_queue = asyncio.Queue()
# Add other queues as needed by your tools (e.g., from conversation_tracker)
# conversation_queue = asyncio.Queue() 

@app.get("/navigation/stream")
async def navigation_stream():
    """Streams events to the client via Server-Sent Events."""
    async def event_generator():
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        while True:
            try:
                # Listen for events from the navigation queue
                event = await asyncio.wait_for(navigation_queue.get(), timeout=25)
                logger.info(f"📡 SENDING SSE TO CLIENT: {event.get('type')}")
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Send a keepalive event to prevent the connection from closing
                yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': time.time()})}\n\n"
            except asyncio.CancelledError:
                logger.info("SSE stream task cancelled.")
                break
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                break
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/navigation/command")
async def receive_navigation_command(command: dict):
    """Receives commands from tools and puts them on the SSE queue."""
    await navigation_queue.put(command)
    return {"status": "queued"}

# --- Data Ingress Endpoint ---
@app.post("/ai/data")
async def ai_data_ingress(message: dict):
    """
    Receives static website data from the client and loads it directly
    into the static_data_loader tool.
    """
    try:
        if message.get("type") == "dashboard_data":
            app_id = message.get("app_id", "test_dashboard")
            data = message.get("data", {})
            
            components = [data] if data else []
            intents = data.get("intents", [])
            
            success = static_data_loader.load_app_data_sync(app_id, components, intents)
            
            if success:
                logger.info(f"📊 Stored website data for app [{app_id}]")
                await static_data_loader.send_static_data_via_sse(app_id)
                return {"status": "ok", "stored": True}
            else:
                logger.error(f"❌ Failed to load website data for app [{app_id}]")
                raise HTTPException(status_code=500, detail="Failed to process website data")

        logger.warning(f"Received unhandled message type in /ai/data: {message.get('type')}")
        return {"status": "ok", "stored": False}
        
    except Exception as e:
        logger.error(f"❌ Error in /ai/data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Client-Side Logging Endpoint ---
@app.post("/api/client-log")
async def receive_client_log(request: Request):
    """Receives logs from the client and prints them to the server console."""
    try:
        data = await request.json()
        log_message = data.get("message", "")
        session_id = data.get("sessionId", "unknown")
        logger.info(f"CLIENT LOG [{session_id}]: {log_message}")
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"❌ Error saving client log: {e}")
        return {"status": "error", "message": str(e)}

# --- Error Handlers ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "path": str(request.url.path)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."},
    )

# --- Main Execution ---
if __name__ == "__main__":
    import uvicorn
    logger.info(f"🌟 Starting Qubekit Server on http://{settings.server_host}:{settings.server_port}")
    uvicorn.run("main:app",
                host=settings.server_host,
                port=settings.server_port,
                reload=settings.debug)