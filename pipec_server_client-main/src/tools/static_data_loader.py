#!/usr/bin/env python3
"""
Tool 3: Static Data Loader
Loads and manages static knowledge about pages, elements, and capabilities on-demand
"""

from typing import Dict, List, Any, Optional
from loguru import logger
import aiohttp
import asyncio
import time
import time


class StaticDataLoader:
    """Manages static knowledge about website structure and capabilities"""
    
    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.pages_data = {}
        self.elements_data = {}
        self.navigation_map = {}
        self.loaded_apps = {}  # Cache loaded app data
        self.current_app_id = None
    
    async def load_app_data(self, app_id: str) -> bool:
        """
        Load static data for an app from backend on-demand
        
        Args:
            app_id: Application identifier
            
        Returns:
            True if loaded successfully
        """
        try:
            # Check if already loaded
            if app_id in self.loaded_apps:
                logger.debug(f"App {app_id} already loaded, using cached data")
                self._set_current_app_data(app_id)
                return True
            
            logger.info(f"Loading static data for app: {app_id}")
            
            # Fetch data from backend
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/bot/website-data?app_id={app_id}") as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch app data: {response.status}")
                        return False
                    
                    data = await response.json()
                    components = data.get("components", [])
                    intents = data.get("intents", [])
            
            # Process and cache the data
            app_data = {
                "pages_data": self._process_components(components),
                "elements_data": self._process_elements(components),
                "navigation_map": self._build_navigation_map(components, intents),
                "raw_components": components,
                "raw_intents": intents
            }
            
            self.loaded_apps[app_id] = app_data
            self._set_current_app_data(app_id)
            
            logger.info(f"Static data loaded for app {app_id}: {len(self.pages_data)} pages, {len(self.elements_data)} elements")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load static data for app {app_id}: {e}")
            return False
    
    def _set_current_app_data(self, app_id: str):
        """Set current app data from cache"""
        if app_id in self.loaded_apps:
            app_data = self.loaded_apps[app_id]
            self.pages_data = app_data["pages_data"]
            self.elements_data = app_data["elements_data"]
            self.navigation_map = app_data["navigation_map"]
            self.current_app_id = app_id
    
    def load_app_data_sync(self, app_id: str, components: List[Dict], intents: List[Dict]) -> bool:
        """
        Load static data for an app (synchronous version for backward compatibility)
        
        Args:
            app_id: Application identifier
            components: List of page components
            intents: List of available intents
            
        Returns:
            True if loaded successfully
        """
        try:
            logger.info(f"Loading static data for app: {app_id}")
            
            # Process and cache the data
            app_data = {
                "pages_data": self._process_components(components),
                "elements_data": self._process_elements(components),
                "navigation_map": self._build_navigation_map(components, intents),
                "raw_components": components,
                "raw_intents": intents
            }
            
            self.loaded_apps[app_id] = app_data
            self._set_current_app_data(app_id)
            
            logger.info(f"Static data loaded for app {app_id}: {len(self.pages_data)} pages, {len(self.elements_data)} elements")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load static data for app {app_id}: {e}")
            return False
    
    def _process_components(self, components: List[Dict]) -> Dict[str, Dict]:
        """Process components into structured pages data"""
        pages = {}
        
        for comp in components:
            route = comp.get("routeName", "/")
            pages[route] = {
                "name": comp.get("name", "Unknown Page"),
                "description": comp.get("description", ""),
                "purpose": self._determine_page_purpose(comp),
                "elements": [elem.get("testID") for elem in comp.get("interactiveElements", [])],
                "capabilities": self._extract_capabilities(comp),
                "navigation_type": comp.get("navigatorType", "screen")
            }
        
        return pages
    
    def _process_elements(self, components: List[Dict]) -> Dict[str, Dict]:
        """Process interactive elements into structured data"""
        elements = {}
        
        for comp in components:
            route = comp.get("routeName", "/")
            
            for elem in comp.get("interactiveElements", []):
                element_id = elem.get("testID")
                if element_id:
                    elements[element_id] = {
                        "type": elem.get("type", "unknown"),
                        "text": elem.get("textContent", ""),
                        "label": elem.get("accessibilityLabel", ""),
                        "page": route,
                        "purpose": self._determine_element_purpose(elem),
                        "action_type": self._determine_action_type(elem)
                    }
        
        return elements
    
    def _build_navigation_map(self, components: List[Dict], intents: List[Dict]) -> Dict[str, Any]:
        """Build navigation relationships and intent mappings"""
        nav_map = {
            "routes": [comp.get("routeName") for comp in components],
            "intents": {},
            "relationships": self._build_page_relationships(components)
        }
        
        # Process intents
        for intent in intents:
            schema = intent.get("schema", "")
            text = intent.get("text", "")
            
            if schema.startswith("navigation."):
                page_name = schema.split("navigation.")[1]
                nav_map["intents"][page_name] = text
            elif schema.startswith("action."):
                action_name = schema.split("action.")[1]
                nav_map["intents"][action_name] = text
        
        return nav_map
    
    def _determine_page_purpose(self, component: Dict) -> str:
        """Determine the main purpose of a page"""
        name = component.get("name", "").lower()
        description = component.get("description", "").lower()
        
        if "dashboard" in name or "analytics" in description:
            return "data_visualization"
        elif "profile" in name or "settings" in description:
            return "user_management"
        elif "analytics" in name or "report" in description:
            return "reporting"
        else:
            return "general"
    
    def _extract_capabilities(self, component: Dict) -> List[str]:
        """Extract what actions are possible on this page"""
        capabilities = []
        
        for elem in component.get("interactiveElements", []):
            elem_type = elem.get("type", "").lower()
            test_id = elem.get("testID", "").lower()
            
            if "refresh" in test_id:
                capabilities.append("refresh_data")
            elif "export" in test_id:
                capabilities.append("export_data")
            elif "save" in test_id:
                capabilities.append("save_changes")
            elif "generate" in test_id:
                capabilities.append("generate_report")
            elif elem_type == "input":
                capabilities.append("input_data")
            elif elem_type == "select":
                capabilities.append("select_option")
        
        return list(set(capabilities))  # Remove duplicates
    
    def _determine_element_purpose(self, element: Dict) -> str:
        """Determine what an element is used for"""
        test_id = element.get("testID", "").lower()
        text = element.get("textContent", "").lower()
        elem_type = element.get("type", "").lower()
        
        if "refresh" in test_id or "refresh" in text:
            return "refresh_data"
        elif "export" in test_id or "export" in text:
            return "export_data"
        elif "save" in test_id or "save" in text:
            return "save_changes"
        elif "password" in test_id or "password" in text:
            return "security_action"
        elif elem_type == "input":
            return "data_input"
        else:
            return "general_action"
    
    def _determine_action_type(self, element: Dict) -> str:
        """Determine what type of action this element performs"""
        elem_type = element.get("type", "").lower()
        
        if elem_type == "button":
            return "click"
        elif elem_type == "input":
            return "input"
        elif elem_type == "select":
            return "select"
        elif "toggle" in element.get("testID", "").lower():
            return "toggle"
        else:
            return "click"
    
    def _build_page_relationships(self, components: List[Dict]) -> Dict[str, List[str]]:
        """Build relationships between pages"""
        relationships = {}
        routes = [comp.get("routeName") for comp in components]
        
        # Simple relationship mapping (can be enhanced)
        for route in routes:
            relationships[route] = [r for r in routes if r != route]
        
        return relationships
    
    def get_page_info(self, route: str) -> Optional[Dict]:
        """Get information about a specific page"""
        return self.pages_data.get(route)
    
    def get_element_info(self, element_id: str) -> Optional[Dict]:
        """Get information about a specific element"""
        return self.elements_data.get(element_id)
    
    def get_available_elements(self, route: str) -> List[str]:
        """Get list of elements available on a page"""
        page_info = self.get_page_info(route)
        return page_info.get("elements", []) if page_info else []
    
    def get_page_capabilities(self, route: str) -> List[str]:
        """Get list of capabilities for a page"""
        page_info = self.get_page_info(route)
        return page_info.get("capabilities", []) if page_info else []
    
    def find_element_by_purpose(self, purpose: str, route: str = None) -> Optional[str]:
        """Find element ID by its purpose, optionally filtered by page"""
        for element_id, element_info in self.elements_data.items():
            if element_info["purpose"] == purpose:
                if route is None or element_info["page"] == route:
                    return element_id
        return None
    
    def get_navigation_options(self, current_route: str) -> List[str]:
        """Get available navigation options from current page"""
        return self.navigation_map.get("relationships", {}).get(current_route, [])
    
    def get_all_routes(self) -> List[str]:
        """Get all available routes"""
        return self.navigation_map.get("routes", [])
    
    def is_loaded(self, app_id: str = None) -> bool:
        """Check if static data has been loaded"""
        if app_id:
            return app_id in self.loaded_apps
        return self.current_app_id is not None
    
    async def ensure_app_loaded(self, app_id: str) -> bool:
        """Ensure app data is loaded, load if not"""
        if not self.is_loaded(app_id):
            return await self.load_app_data(app_id)
        return True
    
    def get_loaded_apps(self) -> List[str]:
        """Get list of loaded app IDs"""
        return list(self.loaded_apps.keys())
    
    def switch_app(self, app_id: str) -> bool:
        """Switch to a different loaded app"""
        if app_id in self.loaded_apps:
            self._set_current_app_data(app_id)
            logger.info(f"Switched to app: {app_id}")
            return True
        else:
            logger.warning(f"App {app_id} not loaded")
            return False
    
    async def send_static_data_via_sse(self, app_id: str = None) -> bool:
        """
        Send static data via SSE instead of HTTP
        
        Args:
            app_id: Application identifier (uses current if not specified)
            
        Returns:
            True if sent successfully
        """
        try:
            target_app_id = app_id or self.current_app_id
            if not target_app_id or target_app_id not in self.loaded_apps:
                logger.error(f"No data loaded for app: {target_app_id}")
                return False
            
            app_data = self.loaded_apps[target_app_id]
            
            # Create SSE event
            event = {
                "type": "static_data_ready",
                "timestamp": time.time(),
                "data": {
                    "app_id": target_app_id,
                    "components": app_data["raw_components"],
                    "intents": app_data["raw_intents"],
                    "pages_count": len(app_data["pages_data"]),
                    "elements_count": len(app_data["elements_data"])
                }
            }
            
            # Send via SSE
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/navigation/command",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Static data sent via SSE for app: {target_app_id}")
                        return True
                    else:
                        logger.error(f"❌ Failed to send static data via SSE: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending static data via SSE: {e}")
            return False
    
    def check_participants_ready(self, room) -> bool:
        """Check if both user and AI are in the room"""
        if not room:
            return False
            
        total_participants = 1 + room.remoteParticipants.size  # local + remote
        has_ai = any(
            p.identity.includes('bot') or p.identity.includes('ai') 
            for p in room.remoteParticipants.values()
        )
        
        return total_participants >= 2 and has_ai


# Global instance
static_data_loader = StaticDataLoader()