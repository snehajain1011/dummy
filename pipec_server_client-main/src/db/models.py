#!/usr/bin/env python3
"""
Database models using Pydantic for data validation and structure definition
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class InteractiveElement(BaseModel):
    """Model for interactive elements within components"""
    type: str = Field(..., description="Element type (button, input, etc.)")
    testID: str = Field(..., description="Test ID for the element")
    textContent: Optional[str] = Field(None, description="Text content of the element")
    accessibilityLabel: Optional[str] = Field(None, description="Accessibility label")

class Component(BaseModel):
    """Model for application components"""
    id: Optional[str] = Field(None, alias="_id", description="Component ID")
    name: str = Field(..., description="Component name")
    routeName: str = Field(..., description="Route name for navigation")
    description: Optional[str] = Field(None, description="Component description")
    navigatorType: str = Field("screen", description="Type of navigator")
    app: Optional[str] = Field(None, description="Associated app ID")
    interactiveElements: List[InteractiveElement] = Field(default_factory=list, description="Interactive elements")

class Intent(BaseModel):
    """Model for application intents"""
    id: Optional[str] = Field(None, alias="_id", description="Intent ID")
    schema: str = Field(..., description="Intent schema")
    text: str = Field(..., description="Intent description")
    app: Optional[str] = Field(None, description="Associated app ID")

class App(BaseModel):
    """Model for applications"""
    id: Optional[str] = Field(None, alias="_id", description="App ID")
    name: str = Field(..., description="App name")
    description: Optional[str] = Field(None, description="App description")
    apiKeys: Dict[str, Any] = Field(default_factory=dict, description="API keys")

class AppIntentItem(BaseModel):
    """Model for app intent items from client"""
    hash: str = Field(..., description="Component hash")
    text: str = Field(..., description="Display text for the intent")
    componentType: str = Field(..., description="Component type")

class ProcessComponentsRequest(BaseModel):
    """Model for processing components request"""
    components: List[AppIntentItem] = Field(..., description="List of components")
    userInput: str = Field(..., description="User input text")
    deviceId: Optional[str] = Field(None, description="Device ID")
    screen: Optional[str] = Field(None, description="Current screen")

class ComponentResponse(BaseModel):
    """Model for component response"""
    intent: str = Field(..., description="Detected intent")
    routeName: Optional[str] = Field(None, description="Route name")
    text: str = Field(..., description="Response text")
    actionType: str = Field("navigate", description="Action type")
    confidence: float = Field(0.7, description="Confidence score")
    timestamp: str = Field(..., description="Timestamp")
    component: Optional[Component] = Field(None, description="Matched component")
    audioData: Optional[str] = Field(None, description="Audio data")
    audioFormat: Optional[str] = Field(None, description="Audio format")
    claudeError: Optional[bool] = Field(None, description="Claude API error flag")
    elevenLabsError: Optional[bool] = Field(None, description="ElevenLabs error flag")
    systemError: Optional[bool] = Field(None, description="System error flag")
    errorMessage: Optional[str] = Field(None, description="Error message")

class TokenRequest(BaseModel):
    """Model for token generation request"""
    user_identity: str = Field(..., description="User identity")
    room_name: Optional[str] = Field(None, description="Room name")
    ttl_seconds: Optional[int] = Field(7200, description="Token TTL in seconds")

class TokenResponse(BaseModel):
    """Model for token response"""
    token: str = Field(..., description="Generated JWT token")
    room_name: str = Field(..., description="Room name")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field("1.0.0", description="API version") 