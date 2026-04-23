#!/usr/bin/env python3
"""
Tool 2: Smart Action Executor
Maps user natural language requests to specific UI actions
Generates intent JSON and sends via SSE (no actual execution)
"""

import re
import time
import aiohttp
from typing import Dict, List, Optional, Any
from loguru import logger


class SmartActionExecutor:
    """Intelligently maps user requests to UI actions and generates intent JSON"""
    
    def __init__(self, server_url: str = "http://localhost:8004"):
        self.server_url = server_url
        self.action_patterns = self._load_action_patterns()
        self.element_mappings = self._load_element_mappings()
        self.intent_log = []
    
    def _load_action_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that map user language to action types"""
        return {
            "click": [
                r"click.*button", r"press.*button", r"tap.*button",
                r"hit.*button", r"select.*button", r"choose.*button"
            ],
            "toggle": [
                r"toggle.*", r"switch.*", r"turn on.*", r"turn off.*",
                r"enable.*", r"disable.*", r"activate.*", r"deactivate.*"
            ],
            "navigate": [
                r"go to.*", r"navigate.*", r"open.*", r"show me.*",
                r"take me to.*", r"switch to.*", r"move to.*"
            ],
            "input": [
                r"type.*", r"enter.*", r"fill.*", r"input.*",
                r"write.*", r"set.*value", r"change.*text"
            ],
            "check": [
                r"check.*", r"what.*status", r"show.*status", r"display.*status",
                r"current.*status", r"status.*now"
            ],
            "test": [
                r"test.*", r"try.*", r"experiment.*", r"demo.*"
            ]
        }
    
    def _load_element_mappings(self) -> Dict[str, List[str]]:
        """Load mappings from user language to element identifiers"""
        return {
            "go-to-dashboard-btn": [
                "go to dashboard", "dashboard", "navigate to dashboard", "dashboard button",
                "go dashboard", "open dashboard", "show dashboard"
            ],
            "save-profile-btn": [
                "save profile", "save", "save changes", "profile save",
                "save button", "save profile button", "apply changes"
            ],
            "send-screen-status-btn": [
                "send screen status", "screen status", "send status", "status button",
                "send screen", "screen status button", "report status"
            ],
            "test-command-input": [
                "test command", "command input", "test input", "command field",
                "enter command", "type command", "command box"
            ],
            "ai-navigation-toggle": [
                "ai navigation mode", "ai mode", "navigation mode", "ai toggle",
                "toggle ai", "ai navigation", "enable ai", "disable ai"
            ],
            "live-status-box": [
                "live status", "status box", "current status", "status display",
                "live status box", "status indicator", "current state"
            ]
        }
    
    def analyze_user_request(self, user_input: str, current_page: str, 
                           available_elements: List[str]) -> Dict[str, Any]:
        """
        Analyze user request and determine the intended action
        
        Args:
            user_input: What the user said
            current_page: Current page route
            available_elements: Elements visible on current page
            
        Returns:
            Action analysis with type, target, and confidence
        """
        user_lower = user_input.lower().strip()
        
        # Determine action type
        action_type = self._detect_action_type(user_lower)
        
        # Find target element
        target_element = self._find_target_element(user_lower, available_elements)
        
        # Calculate confidence
        confidence = self._calculate_confidence(user_lower, action_type, target_element)
        
        # Generate response
        response_text = self._generate_response_text(action_type, target_element, current_page)
        
        return {
            "action_type": action_type,
            "target_element": target_element,
            "confidence": confidence,
            "response_text": response_text,
            "current_page": current_page,
            "user_input": user_input
        }
    
    def _detect_action_type(self, user_input: str) -> str:
        """Detect what type of action user wants to perform"""
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return action_type
        
        # Default action type based on common words
        if any(word in user_input for word in ["this", "that", "it"]):
            return "click"  # Generic interaction
        
        return "navigate"  # Default fallback
    
    def _find_target_element(self, user_input: str, available_elements: List[str]) -> Optional[str]:
        """Find which element the user is referring to"""
        best_match = None
        best_score = 0
        
        for element_id in available_elements:
            if element_id in self.element_mappings:
                for keyword in self.element_mappings[element_id]:
                    if keyword.lower() in user_input:
                        # Score based on keyword length (longer = more specific)
                        score = len(keyword)
                        if score > best_score:
                            best_score = score
                            best_match = element_id
        
        return best_match
    
    def _calculate_confidence(self, user_input: str, action_type: str, 
                            target_element: Optional[str]) -> float:
        """Calculate confidence score for the action analysis"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we found a specific element
        if target_element:
            confidence += 0.3
        
        # Boost confidence if action type was clearly detected
        if action_type != "navigate":  # navigate is default fallback
            confidence += 0.2
        
        # Boost confidence for specific action words
        specific_words = ["click", "toggle", "save", "refresh", "export"]
        if any(word in user_input for word in specific_words):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_response_text(self, action_type: str, target_element: Optional[str], 
                              current_page: str) -> str:
        """Generate appropriate response text for the action"""
        if target_element:
            element_name = target_element.replace("-", " ").replace("btn", "button")
            
            if action_type == "click":
                return f"I'll click the {element_name} for you."
            elif action_type == "toggle":
                return f"I'll toggle the {element_name}."
            elif action_type == "input":
                return f"I'll help you enter text in the {element_name}."
            elif action_type == "check":
                return f"I'll check the {element_name} for you."
            elif action_type == "test":
                return f"I'll test the {element_name} for you."
            else:
                return f"I'll {action_type} the {element_name}."
        else:
            if action_type == "navigate":
                return f"I'll help you navigate from the {current_page} page."
            else:
                return f"I'll perform the {action_type} action for you."
    
    def create_action_command(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create the hash-based intent JSON command to send to client"""
        # Map target element to hash value
        element_hash = self._get_element_hash(analysis["target_element"])
        
        return {
            "type": "ai_intent",
            "timestamp": time.time(),
            "data": {
                "intent": element_hash,
                "actionType": analysis["action_type"],
                "text": analysis["response_text"],
                "confidence": analysis["confidence"],
                "routeName": analysis["current_page"],
                "user_request": analysis["user_input"]
            }
        }
    
    def _get_element_hash(self, element_id: str) -> str:
        """Map element ID to hash value"""
        # Hash mapping based on your specification
        hash_mapping = {
            "go-to-dashboard-btn": "Dashboard-GoToDashboard-1.0",
            "save-profile-btn": "Profile-SaveProfile-1.1", 
            "send-screen-status-btn": "Status-SendScreenStatus-1.2",
            "test-command-input": "Input-TestCommand-2.0",
            "ai-navigation-toggle": "Toggle-AINavigation-2.1",
            "live-status-box": "Status-LiveStatus-2.2",
            # Add more mappings as needed
        }
        
        return hash_mapping.get(element_id, f"Unknown-{element_id}-0.0")
    
    async def generate_and_send_intent(self, user_input: str, current_page: str, 
                                     available_elements: List[str]) -> Dict[str, Any]:
        """
        Generate intent JSON and send via SSE (no actual execution)
        
        Args:
            user_input: What the user said
            current_page: Current page route
            available_elements: Elements visible on current page
            
        Returns:
            Generated intent data
        """
        try:
            # Analyze user request
            analysis = self.analyze_user_request(user_input, current_page, available_elements)
            
            # Generate hash-based intent
            intent_hash = self._generate_intent_hash(analysis)
            
            # Create intent data
            intent_data = {
                "intent": intent_hash,
                "actionType": analysis["action_type"],
                "text": analysis["response_text"],
                "confidence": analysis["confidence"],
                "timestamp": time.time(),
                "target_element": analysis["target_element"],
                "current_page": analysis["current_page"],
                "user_input": user_input
            }
            
            # Add to log
            self.intent_log.append(intent_data)
            
            # Keep only last 50 intents
            if len(self.intent_log) > 50:
                self.intent_log = self.intent_log[-50:]
            
            # Send via SSE using the correct endpoint
            event = {
                "type": "ai_intent",
                "timestamp": time.time(),
                "data": intent_data
            }
            
            await self._send_sse_event(event)
            logger.info(f"🎯 Generated intent: {intent_data['text']} (confidence: {intent_data['confidence']:.2f})")
            
            return intent_data
            
        except Exception as e:
            logger.error(f"❌ Error generating intent: {e}")
            return None
    
    def _generate_intent_hash(self, analysis: Dict[str, Any]) -> str:
        """Generate a hash-based intent identifier"""
        import hashlib
        
        # Create a unique string from the analysis
        intent_string = f"{analysis['action_type']}-{analysis['target_element']}-{analysis['current_page']}-{analysis['user_input']}"
        
        # Generate hash
        hash_object = hashlib.md5(intent_string.encode())
        hash_hex = hash_object.hexdigest()[:8]  # Use first 8 characters
        
        # Create readable intent ID
        timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of timestamp
        intent_id = f"Intent-{analysis['action_type'].upper()}-{hash_hex}-{timestamp}"
        
        return intent_id
    
    async def _send_sse_event(self, event: Dict[str, Any]):
        """Send event via SSE using the correct navigation command endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/navigation/command",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ Failed to send SSE event: {response.status}")
                    else:
                        logger.info(f"✅ Intent sent via SSE: {event['data']['intent']}")
                        
        except Exception as e:
            logger.error(f"❌ Error sending SSE event: {e}")
    
    def get_intent_log(self) -> list:
        """Get intent log"""
        return self.intent_log.copy()
    
    def clear_intent_log(self):
        """Clear intent log"""
        self.intent_log = []
        logger.info("🧹 Intent log cleared")


# Global instance
smart_action_executor = SmartActionExecutor()