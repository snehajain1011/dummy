#!/usr/bin/env python3
"""
Configuration management for the Qubekit Server
Loads and validates environment variables using Pydantic Settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict # <- Import SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv(override=True)

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # --- This is the corrected configuration ---
    # All model configuration is now in this single dictionary.
    model_config = SettingsConfigDict(
        env_file=".env",              # Load from a .env file
        env_file_encoding="utf-8",    # Specify encoding
        case_sensitive=False,         # Environment variables are not case-sensitive
        extra='ignore'                # Ignore extra variables like 'groq_api_key'
    )
    
    # LiveKit Configuration
    # Using `...` as the default value makes the field required.
    livekit_api_key: str = Field(..., alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(..., alias="LIVEKIT_API_SECRET")
    livekit_room_name: str = Field(..., alias="LIVEKIT_ROOM_NAME")
    livekit_participant_name: str = Field("WebsiteAssistant", alias="LIVEKIT_PARTICIPANT_NAME")
    livekit_url: str = Field(..., alias="LIVEKIT_URL")
    token_ttl_seconds: int = Field(7200, alias="TOKEN_TTL_SECONDS")
    
    # AI Services Configuration
    claude_api_key: str = Field(..., alias="CLAUDE_API_KEY")
    claude_default_model: str = Field("claude-3-5-sonnet-20240620", alias="CLAUDE_DEFAULT_MODEL")
    elevenlabs_api_key: str = Field(..., alias="ELEVENLABS_API_KEY")
    elevenlabs_voice: str = Field("en-US-Neural", alias="ELEVENLABS_VOICE")
    elevenlabs_voice_id: str = Field(..., alias="ELEVENLABS_VOICE_ID")
    deepgram_api_key: str = Field(..., alias="DEEPGRAM_API_KEY")
    
    # Database Configuration
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    
    # Server Configuration
    server_host: str = Field("0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(8002, alias="SERVER_PORT")
    debug: bool = Field(False, alias="DEBUG")
    
    # CORS Configuration
    cors_origins: List[str] = Field(["*"], alias="CORS_ORIGINS")
    cors_credentials: bool = Field(True, alias="CORS_CREDENTIALS")
    
    # Auth Configuration
    auth_db_path: str = Field("sessions.db", alias="AUTH_DB_PATH")
    session_duration: int = Field(1800, alias="SESSION_DURATION")  # 30 minutes
    max_sessions_per_user: int = Field(5, alias="MAX_SESSIONS_PER_USER")

# Create a single, global settings instance to be used across the application
try:
    settings = Settings()
    print("✅ Configuration loaded successfully.")
except Exception as e:
    # This provides a much cleaner error message if required variables are missing
    print(f"❌ CONFIGURATION ERROR: Failed to load settings. Please check your .env file.")
    print(f"   Details: {e}")
    exit(1) # Exit the application if configuration fails