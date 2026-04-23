from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import asyncio
from loguru import logger
from .auth_manager import AuthManager
from .token_service import TokenService

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_manager = AuthManager()

async def start_bot_for_user(room_name: str, user_identity: str):
    """Start bot for user in background"""
    try:
        from ..pipecat_bot.bot_runner import bot_runner
        logger.info(f"🤖 Starting bot for user: {user_identity} in room: {room_name}")
        await bot_runner.start_bot(
            room_name=room_name,
            user_identity=user_identity
        )
        logger.info(f"✅ Bot ready for user: {user_identity}")
    except Exception as e:
        logger.error(f"❌ Bot start failed for {user_identity}: {e}")

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class LoginRequest(BaseModel):
    user_identity: str

class LoginResponse(BaseModel):
    session_id: str
    room_name: str
    livekit_token: str
    livekit_url: str
    expires_in: int
    expires_at: str
    user_identity: str

class StatusResponse(BaseModel):
    is_active: bool
    user_identity: str
    room_name: str
    expires_in: int
    session_id: str

@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        logger.info(f"👤 Registration request: username=[{request.username}], email=[{request.email}]")
        
        # For testing purposes, we'll just return success
        # In a real implementation, you'd save to database
        return {
            "status": "success",
            "message": "User registered successfully",
            "username": request.username,
            "email": request.email
        }
        
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, x_api_key: str = Header(..., alias="X-API-Key")):
    """Login with API key and user identity"""
    try:
        logger.info(f"🔐 Auth login request: user=[{request.user_identity}], api_key=[{x_api_key[:12]}***{x_api_key[-4:]}]")
        
        # Validate API key
        if not auth_manager.validate_api_key(x_api_key):
            logger.warning(f"🔑 Auth failed - Invalid API key: [{x_api_key[:12]}***{x_api_key[-4:]}]")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Always create new session for now to avoid user identity conflicts
        # TODO: Implement proper session management later
        logger.info(f"🔐 Auth creating new session: user=[{request.user_identity}]")
        session = auth_manager.create_session(x_api_key, request.user_identity)
        
        # Import settings here to avoid circular import
        from ..config import settings
        
        response = LoginResponse(
            session_id=session["session_id"],
            room_name=session["room_name"],
            livekit_token=session["livekit_token"],
            livekit_url=settings.livekit_url,
            expires_in=session["expires_in"],
            expires_at=f"{session['expires_at']}",
            user_identity=session["user_identity"]
        )
        
        logger.info(f"✅ Auth login success: user=[{request.user_identity}] room=[{session['room_name']}] expires=[{session['expires_in']}s]")
        
        # Return response immediately, then start bot in background
        # This ensures fast response time for the client
        asyncio.create_task(start_bot_for_user(session["room_name"], session["user_identity"]))
        logger.info(f"🚀 Bot connection initiated in background for room=[{session['room_name']}]")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Auth login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/status", response_model=StatusResponse)
async def get_status(x_api_key: str = Header(..., alias="X-API-Key")):
    """Get session status"""
    try:
        logger.debug(f"🔐 Auth status request: key={x_api_key[:8]}...")
        session = auth_manager.get_session_by_api_key(x_api_key)
        if not session:
            logger.warning(f"🔑 Auth status failed - Invalid session: {x_api_key[:8]}...")
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return StatusResponse(
            is_active=True,
            user_identity=session["user_identity"],
            room_name=session["room_name"],
            expires_in=session["expires_in"],
            session_id=session["session_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")

@router.post("/refresh")
async def refresh_session(x_api_key: str = Header(..., alias="X-API-Key")):
    """Refresh session token"""
    try:
        session = auth_manager.refresh_session(x_api_key)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        from ..config import settings
        
        return {
            "livekit_token": session["livekit_token"],
            "expires_in": session["expires_in"],
            "expires_at": session["expires_at"],
            "livekit_url": settings.livekit_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Refresh failed")

@router.post("/logout")
async def logout(x_api_key: str = Header(..., alias="X-API-Key")):
    """Logout and cleanup session"""
    try:
        logger.info(f"🔐 Auth logout request: key={x_api_key[:8]}...")
        success = auth_manager.delete_session(x_api_key)
        if not success:
            logger.warning(f"🔑 Auth logout failed - Session not found: {x_api_key[:8]}...")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Auth logout success: {x_api_key[:8]}...")
        return {"status": "logged_out", "message": "Session terminated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/cleanup")
async def cleanup_expired():
    """Cleanup expired sessions (admin endpoint)"""
    try:
        count = auth_manager.cleanup_expired_sessions()
        active_count = auth_manager.get_active_sessions_count()
        
        return {
            "cleaned_sessions": count,
            "active_sessions": active_count,
            "status": "cleanup_complete"
        }
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")