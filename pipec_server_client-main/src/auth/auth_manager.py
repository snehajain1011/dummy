import sqlite3
import time
import uuid
from typing import Dict, Optional
from pathlib import Path
from loguru import logger

class AuthManager:
    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self.init_database()
        logger.info(f"🔐 Auth manager initialized: db=[{db_path}]")
    
    def _mask_sensitive_data(self, data: str, show_chars: int = 4) -> str:
        """Mask sensitive data showing only first/last characters"""
        if not data or len(data) <= show_chars * 2:
            return "[MASKED]"
        return f"{data[:show_chars]}***{data[-show_chars:]}"
    
    def init_database(self):
        """Create sessions table if not exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key TEXT UNIQUE NOT NULL,
                        user_identity TEXT NOT NULL,
                        app_id TEXT DEFAULT 'default',
                        room_name TEXT NOT NULL,
                        session_id TEXT UNIQUE NOT NULL,
                        livekit_token TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        expires_at INTEGER NOT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON sessions(api_key)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON sessions(expires_at)")
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Database init failed: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> bool:
        """Accept any non-empty API key for now"""
        is_valid = bool(api_key and len(api_key.strip()) > 0)
        if not is_valid:
            logger.warning("🔑 Invalid API key format")
        return is_valid
    
    def create_session(self, api_key: str, user_identity: str) -> Dict:
        """Create new session with 30-min expiry"""
        from .token_service import TokenService
        
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        room_name = f"room_{user_identity}_{int(time.time())}"
        created_at = int(time.time())
        expires_at = created_at + 1800  # 30 minutes
        
        # Generate LiveKit token
        livekit_token = TokenService.generate_livekit_token(user_identity, room_name)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (api_key, user_identity, app_id, room_name, session_id, 
                     livekit_token, created_at, expires_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (api_key, user_identity, "default", room_name, session_id,
                      livekit_token, created_at, expires_at, True))
                conn.commit()
                
            session_data = {
                "session_id": session_id,
                "api_key": api_key,
                "user_identity": user_identity,
                "app_id": "default",
                "room_name": room_name,
                "livekit_token": livekit_token,
                "created_at": created_at,
                "expires_at": expires_at,
                "expires_in": 1800
            }
            
            logger.info(f"✅ Session created: user=[{user_identity}] room=[{room_name}] session=[{session_id}] token=[{self._mask_sensitive_data(livekit_token)}]")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            raise
    
    def get_session_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get active session by API key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM sessions 
                    WHERE api_key = ? AND expires_at > ? AND is_active = 1
                """, (api_key, int(time.time())))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                session = dict(row)
                session["expires_in"] = session["expires_at"] - int(time.time())
                return session
                
        except Exception as e:
            logger.error(f"❌ Session lookup failed: {e}")
            return None
    
    def refresh_session(self, api_key: str) -> Optional[Dict]:
        """Refresh session with new token and extended expiry"""
        session = self.get_session_by_api_key(api_key)
        if not session:
            return None
        
        from .token_service import TokenService
        
        new_expires_at = int(time.time()) + 1800
        new_token = TokenService.generate_livekit_token(
            session["user_identity"], 
            session["room_name"]
        )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE sessions 
                    SET livekit_token = ?, expires_at = ?
                    WHERE api_key = ?
                """, (new_token, new_expires_at, api_key))
                conn.commit()
                
            session["livekit_token"] = new_token
            session["expires_at"] = new_expires_at
            session["expires_in"] = 1800
            
            logger.info(f"🔄 Session refreshed: user=[{session['user_identity']}] room=[{session['room_name']}] new_token=[{self._mask_sensitive_data(new_token)}]")
            return session
            
        except Exception as e:
            logger.error(f"❌ Session refresh failed: {e}")
            return None
    
    def delete_session(self, api_key: str) -> bool:
        """Delete session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE sessions SET is_active = 0 
                    WHERE api_key = ?
                """, (api_key,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"🗑️ Session deleted: api_key=[{self._mask_sensitive_data(api_key)}]")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Session deletion failed: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE expires_at < ?
                """, (int(time.time()),))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"🧹 Cleaned {cursor.rowcount} expired sessions")
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return 0
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM sessions 
                    WHERE expires_at > ? AND is_active = 1
                """, (int(time.time()),))
                return cursor.fetchone()[0]
        except:
            return 0