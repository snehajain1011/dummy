#!/usr/bin/env python3
"""
API Router for authentication and token endpoints
"""

import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from loguru import logger

from ..auth.token_service import TokenService
from ..db.models import TokenRequest, TokenResponse, HealthResponse
from ..config import settings

router = APIRouter(prefix="/api/v1", tags=["Authentication"])

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key and return it if valid"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is required")
    return x_api_key

@router.post("/token", response_model=TokenResponse)
async def generate_token(
    request: TokenRequest,
    api_key: str = Depends(verify_api_key)
) -> TokenResponse:
    """
    Generate a LiveKit JWT token for user authentication
    
    Args:
        request: Token request with user identity and optional parameters
        api_key: API key for authentication
        
    Returns:
        TokenResponse with JWT token and metadata
    """
    try:
        logger.info(f"Generating token for user: {request.user_identity}")
        
        # Generate token
        ttl = request.ttl_seconds or settings.token_ttl_seconds
        token = TokenService.generate_livekit_token(
            user_identity=request.user_identity,
            room_name=request.room_name or settings.livekit_room_name,
            ttl=ttl
        )
        
        # Get room name for response
        room_name = request.room_name or settings.livekit_room_name
        
        logger.info(f"Token generated successfully for user {request.user_identity} in room {room_name}")
        
        return TokenResponse(
            token=token,
            room_name=room_name,
            expires_in=ttl
        )
        
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    
    Returns:
        HealthResponse with server status
    """
    try:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/token/validate")
async def validate_token(
    token: str,
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Validate a JWT token
    
    Args:
        token: JWT token to validate
        api_key: API key for authentication
        
    Returns:
        Token validation result
    """
    try:
        payload = TokenService.validate_livekit_token(token)
        
        if payload:
            return {
                "valid": True,
                "user": payload.get("name"),
                "room": payload.get("video", {}).get("room"),
                "expires_at": payload.get("exp")
            }
        else:
            return {
                "valid": False,
                "error": "Invalid or expired token"
            }
            
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate token: {str(e)}")

@router.get("/token/info")
async def get_token_info(
    token: str,
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Get token information without validation (for debugging)
    
    Args:
        token: JWT token to decode
        api_key: API key for authentication
        
    Returns:
        Token information
    """
    try:
        payload = TokenService.get_token_info(token)
        
        if payload:
            return {
                "valid_format": True,
                "user": payload.get("name"),
                "room": payload.get("video", {}).get("room"),
                "expires_at": payload.get("exp"),
                "issued_at": payload.get("nbf")
            }
        else:
            return {
                "valid_format": False,
                "error": "Invalid token format"
            }
            
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get token info: {str(e)}")

@router.get("/config")
async def get_config(
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Get server configuration (non-sensitive)
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Server configuration
    """
    try:
        return {
            "livekit_url": settings.livekit_url,
            "room_name": settings.livekit_room_name,
            "participant_name": settings.livekit_participant_name,
            "token_ttl_seconds": settings.token_ttl_seconds,
            "server_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

@router.get("/apps")
async def get_available_apps(
    api_key: str = Depends(verify_api_key)
) -> list:
    """
    Get available app IDs from database
    
    Args:
        api_key: API key for authentication
        
    Returns:
        List of available apps with basic info
    """
    try:
        from ..db.mongodb_service import mongodb_service
        
        # Always include custom app "0" first
        apps_info = [
            {
                "app_id": "0",
                "name": "Custom Demo App",
                "component_count": 3,
                "intent_count": 5,
                "has_interactive_elements": True,
                "source": "hardcoded"
            }
        ]
        
        # Get unique app IDs from components collection
        if mongodb_service.db is None:
            # Return fallback apps along with custom app
            apps_info.extend([
                {
                    "app_id": "standalone-test-36a75d3c-f9df-4d0e-9384-14d3f420370a",
                    "name": "Test App 1",
                    "component_count": 1,
                    "intent_count": 1,
                    "has_interactive_elements": True,
                    "source": "mongodb"
                },
                {
                    "app_id": "standalone-test-2ceb89db-9d76-4172-aa1b-cc6938fe903f", 
                    "name": "Test App 2",
                    "component_count": 1,
                    "intent_count": 1,
                    "has_interactive_elements": True,
                    "source": "mongodb"
                }
            ])
            return apps_info
        
        # Get app IDs from components
        components_pipeline = [{"$group": {"_id": "$app_id"}}]
        components_cursor = mongodb_service.db["components"].aggregate(components_pipeline)
        app_ids = [doc["_id"] async for doc in components_cursor if doc["_id"]]
        
        # Get stats for each app from MongoDB
        for app_id in app_ids:
            components = await mongodb_service.get_components_by_app_id(app_id)
            intents = await mongodb_service.get_intents_by_app_id(app_id)
            
            apps_info.append({
                "app_id": app_id,
                "name": f"App {app_id[:8]}...",
                "component_count": len(components),
                "intent_count": len(intents),
                "has_interactive_elements": any(
                    comp.get("interactive_elements", []) for comp in components
                ),
                "source": "mongodb"
            })
        
        # Sort by component count (custom app "0" will stay first)
        mongodb_apps = [app for app in apps_info if app["app_id"] != "0"]
        mongodb_apps.sort(key=lambda x: x["component_count"], reverse=True)
        
        # Rebuild list with custom app first
        final_apps = [app for app in apps_info if app["app_id"] == "0"]
        final_apps.extend(mongodb_apps)
        
        return final_apps
        
    except Exception as e:
        logger.error(f"Error getting apps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get apps: {str(e)}") 