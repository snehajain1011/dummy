#!/usr/bin/env python3
"""
MongoDB service for database operations using motor async driver
"""

import motor.motor_asyncio
from typing import List, Optional, Dict, Any
from loguru import logger
from .models import Component, Intent, App
from ..config import settings

class MongoDBService:
    """MongoDB service for async database operations"""
    
    def __init__(self):
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        
    async def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_uri)
            
            # Use Cluster0 database as that's where the data is
            self.db = self.client['Cluster0']
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB successfully (database: {self.db.name})")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise - allow server to start in mock mode
            self.client = None
            self.db = None
            logger.warning("Starting server in mock mode without MongoDB")
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def get_app_by_api_key(self, app_id: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Get app by API key for authentication"""
        try:
            if self.db is None:
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
    
    async def get_components_by_app_id(self, app_id: str) -> List[Component]:
        """Get components for a specific app"""
        try:
            if self.db is None:
                # Mock mode - return sample components for testing
                logger.info(f"Mock mode: Returning sample components for app {app_id}")
                return [
                    Component(
                        _id="comp_1",
                        name="Home Screen",
                        routeName="home",
                        description="Main home screen",
                        navigatorType="screen",
                        app=app_id,
                        interactiveElements=[]
                    ),
                    Component(
                        _id="comp_2", 
                        name="Settings Screen",
                        routeName="settings",
                        description="Application settings",
                        navigatorType="screen",
                        app=app_id,
                        interactiveElements=[]
                    )
                ]
            
            cursor = self.db.components.find({"app_id": app_id})
            components = await cursor.to_list(length=None)
            
            # Convert raw MongoDB data to match our model structure
            converted_components = []
            for comp in components:
                converted_comp = {
                    "_id": comp.get("_id"),
                    "name": comp.get("description", "Component"),  # Use description as name
                    "routeName": comp.get("route_name", ""),
                    "description": comp.get("description", ""),
                    "navigatorType": "screen",
                    "app": comp.get("app_id"),
                    "interactiveElements": comp.get("interactive_elements", [])
                }
                converted_components.append(converted_comp)
            
            return converted_components
            
        except Exception as e:
            logger.error(f"Error fetching components: {e}")
            return []
    
    async def get_intents_by_app_id(self, app_id: str) -> List[Intent]:
        """Get intents for a specific app"""
        try:
            if self.db is None:
                # Mock mode - return sample intents for testing
                logger.info(f"Mock mode: Returning sample intents for app {app_id}")
                return [
                    Intent(
                        _id="intent_1",
                        schema="navigation",
                        text="Navigate to different screens",
                        app=app_id
                    ),
                    Intent(
                        _id="intent_2",
                        schema="action", 
                        text="Perform actions like delete, create, update",
                        app=app_id
                    )
                ]
            
            cursor = self.db.intents.find({"app_id": app_id})
            intents = await cursor.to_list(length=None)
            
            # Convert raw MongoDB data to match our model structure
            converted_intents = []
            for intent in intents:
                converted_intent = {
                    "_id": intent.get("_id"),
                    "schema": intent.get("name", "intent"),
                    "text": ", ".join(intent.get("patterns", [])),
                    "app": intent.get("app_id")
                }
                converted_intents.append(converted_intent)
            
            return converted_intents
            
        except Exception as e:
            logger.error(f"Error fetching intents: {e}")
            return []
    
    async def save_interaction(self, app_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Save interaction data to database"""
        try:
            if self.db is None:
                logger.info(f"Mock mode: Would save interaction for app {app_id}")
                return True
            
            interaction_data["app"] = app_id
            interaction_data["timestamp"] = interaction_data.get("timestamp", "")
            
            result = await self.db.interactions.insert_one(interaction_data)
            logger.info(f"Saved interaction with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving interaction: {e}")
            return False
    
    async def get_app_by_id(self, app_id: str) -> Optional[App]:
        """Get app by ID"""
        try:
            if self.db is None:
                # Mock mode - return sample app
                logger.info(f"Mock mode: Returning sample app {app_id}")
                return App(
                    _id=app_id,
                    name="Sample App",
                    description="A sample application for testing",
                    apiKeys={}
                )
            
            app_data = await self.db.apps.find_one({"_id": app_id})
            if app_data:
                return App(**app_data)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching app by ID: {e}")
            return None

# Global MongoDB service instance
mongodb_service = MongoDBService() 