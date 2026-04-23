import jwt
import time
from typing import Dict, Optional
from loguru import logger

class TokenService:
    @staticmethod
    def _mask_sensitive_data(data: str, show_chars: int = 4) -> str:
        """Mask sensitive data showing only first/last characters"""
        if not data or len(data) <= show_chars * 2:
            return "[MASKED]"
        return f"{data[:show_chars]}***{data[-show_chars:]}"
    
    @staticmethod
    def generate_livekit_token(user_identity: str, room_name: str, ttl: int = 1800) -> str:
        """Generate LiveKit JWT token"""
        try:
            from ..config import settings
            
            # LiveKit token payload
            payload = {
                "iss": settings.livekit_api_key,
                "sub": user_identity,
                "iat": int(time.time()),
                "exp": int(time.time()) + ttl,
                "video": {
                    "room": room_name,
                    "roomJoin": True,
                    "canPublish": True,
                    "canSubscribe": True,
                    "canPublishData": True
                }
            }
            
            token = jwt.encode(
                payload, 
                settings.livekit_api_secret, 
                algorithm="HS256"
            )
            
            logger.debug(f"🎫 Token generated: user=[{user_identity}] room=[{room_name}] ttl=[{ttl}s] api_key=[{TokenService._mask_sensitive_data(settings.livekit_api_key)}] token=[{TokenService._mask_sensitive_data(token)}]")
            return token
            
        except Exception as e:
            logger.error(f"❌ Token generation failed: {e}")
            raise
    
    @staticmethod
    def validate_livekit_token(token: str) -> Optional[Dict]:
        """Validate LiveKit token and return payload"""
        try:
            from ..config import settings
            
            payload = jwt.decode(
                token, 
                settings.livekit_api_secret, 
                algorithms=["HS256"]
            )
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                logger.warning("🎫 Token expired")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning(f"🎫 Token expired: token=[{TokenService._mask_sensitive_data(token)}]")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"🎫 Invalid token: token=[{TokenService._mask_sensitive_data(token)}] error=[{e}]")
            return None
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            return None
    
    @staticmethod
    def get_token_info(token: str) -> Optional[Dict]:
        """Get token information without validation"""
        try:
            # Decode without verification to get info
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "user_identity": payload.get("sub"),
                "room_name": payload.get("video", {}).get("room"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "expires_in": max(0, payload.get("exp", 0) - int(time.time()))
            }
            
        except Exception as e:
            logger.error(f"❌ Token info extraction failed: {e}")
            return None