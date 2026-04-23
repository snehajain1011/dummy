#!/usr/bin/env python3
"""
LLM Context Builder for preparing context-rich prompts
"""

import json
from typing import List, Dict, Any, Optional
from loguru import logger
from ..db.models import Component, Intent, AppIntentItem

class LLMContextBuilder:
    """Builds context-rich prompts for LLM processing"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are Website Assistant — a helpful AI assistant for the Voice Chat Interface. You always communicate in **English**.

**CURRENT WEBSITE CONTEXT:**
You are helping users with a Voice Chat Interface that has the following elements:

**AVAILABLE BUTTONS:**
1. "Connect" button - Connects to the voice chat room
2. "Disconnect" button - Disconnects from the voice chat room  
3. "Reconnect" button - Reconnects to the voice chat room

**AVAILABLE TOGGLE:**
1. "AI Navigation Mode" toggle - Enables/disables AI-powered navigation assistance

**CURRENT PAGE ELEMENTS:**
- User Identity input field (shows current user ID)
- Selected App ID input field (for website data)
- LiveKit Server URL field (auto-filled)
- JWT Token field (auto-generated)
- Connection Status display
- Participants list (shows who's in the voice chat)
- Test Command input (for sending navigation commands)
- Demo scenario buttons (Go to Dashboard, Save Profile, Send Screen Status)
- Connection logs area

**YOUR CAPABILITIES:**
- I can see the current connection status (connected/disconnected)
- I can help users understand what each button and toggle does
- I can guide users through connecting to voice chat
- I can explain the AI Navigation Mode feature
- I can help with test commands and demo scenarios
- I have access to website component data for the selected app ID

**RESPONSE GUIDELINES:**
- Keep responses conversational and helpful (2-3 sentences)
- Always respond in English
- Focus on voice chat interface assistance
- When users ask "what data do you have", explain the website components and interactive elements available
- Help users understand how to use the voice chat features

**EXAMPLE RESPONSES:**
- "Hi! I'm your Website Assistant. I can see you're on the voice chat interface. Would you like help connecting or understanding any of the features?"
- "I can see the Connect, Disconnect, and Reconnect buttons, plus the AI Navigation Mode toggle. What would you like to do?"
- "I have access to website component data including interactive elements like buttons and forms. I can help you navigate and interact with them."

Be helpful, clear, and focused on voice chat assistance!"""
    
    def get_action_hints(self, user_input: str) -> Dict[str, str]:
        """Analyze user input to suggest action type"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['click', 'tap', 'press', 'select']):
            return {"suggested": "click", "reason": "action_verb"}
        elif any(word in user_lower for word in ['go to', 'navigate', 'open', 'show me']):
            return {"suggested": "navigate", "reason": "navigation_intent"}
        elif any(word in user_lower for word in ['what', 'how', 'why', 'tell me', 'explain']):
            return {"suggested": "audio_only", "reason": "information_request"}
        else:
            return {"suggested": "navigate", "reason": "default"}
    
    def build_prompt_with_context(
        self,
        user_input: str,
        components: List[Component],
        app_intents: List[Intent] = None,
        dom_data: List[AppIntentItem] = None,
        current_screen: str = "home"
    ) -> str:
        """
        Build a context-rich prompt for the LLM
        
        Args:
            user_input: User's input text
            components: List of available components
            app_intents: List of app-specific intents
            dom_data: DOM elements from client
            current_screen: Current screen name
            
        Returns:
            Formatted prompt string
        """
        try:
            app_intents = app_intents or []
            dom_data = dom_data or []
            
            # Prepare components info
            components_info = []
            for component in components:
                comp_info = {
                    "name": component.name,
                    "routeName": component.routeName,
                    "description": component.description or "",
                    "elements": ""
                }
                
                # Process interactive elements if available
                if component.interactiveElements:
                    elements = []
                    for el in component.interactiveElements:
                        if el.type.lower() != el.testID.lower():
                            element_str = f"{el.type}:{el.testID}"
                            if el.textContent:
                                element_str += f":{el.textContent}"
                            elements.append(element_str)
                    comp_info["elements"] = "|".join(elements)
                
                components_info.append(comp_info)
            
            # Prepare DOM info
            dom_info = ""
            if dom_data:
                dom_info = "\n".join([f"{d.hash}|{d.text}|{d.componentType}" for d in dom_data])
            
            # Prepare intents info
            intents_info = ""
            if app_intents:
                intents_info = "\n".join([f"{intent.schema}: {intent.text}" for intent in app_intents])
            
            # Get action hints
            action_hints = self.get_action_hints(user_input)
            
            # Create optimized prompt
            suggested_action = action_hints['suggested']
            dom_elements_section = f"DOM_ELEMENTS:\n{dom_info}" if dom_info else ""
            faq_intents_section = f"FAQ_INTENTS:\n{intents_info}" if intents_info else ""
            
            prompt = f"""Analyze user intent and respond with JSON only.

USER: "{user_input}"
CURRENT_SCREEN: {current_screen}
ACTION_HINTS: {action_hints}

AVAILABLE_SCREENS: {json.dumps(components_info)}
{dom_elements_section}
{faq_intents_section}

LOGIC:
1. If DOM match found → use hash as intent, routeName={current_screen} for clicks
2. If screen navigation needed → use matching routeName from screens
3. If info query → use audio_only with FAQ content

REQUIRED_JSON_FORMAT:
{{
    "intent": "string",
    "routeName": "valid_route_from_screens", 
    "responseText": "user_friendly_response",
    "actionType": "{suggested_action}",
    "confidence": 0.9,
    "actionMetadata": {{"elementId": "if_click_action"}}
}}"""
            
            logger.debug(f"Built prompt with {len(components_info)} components, {len(dom_data)} DOM elements")
            return prompt
            
        except Exception as e:
            logger.error(f"Error building prompt with context: {e}")
            # Return fallback prompt
            return f"""Analyze user intent and respond with JSON only.

USER: "{user_input}"
CURRENT_SCREEN: {current_screen}

REQUIRED_JSON_FORMAT:
{{
    "intent": "Unknown",
    "routeName": "{current_screen}",
    "responseText": "I understand your request.",
    "actionType": "navigate",
    "confidence": 0.5,
    "actionMetadata": {{}}
}}"""
    
    def build_website_assistant_prompt(self, user_input: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Build a prompt specifically for website assistance
        
        Args:
            user_input: User's input text
            conversation_history: Previous conversation messages
            
        Returns:
            Formatted website assistant prompt
        """
        try:
            history_text = ""
            if conversation_history:
                history_messages = []
                for msg in conversation_history[-5:]:  # Last 5 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    history_messages.append(f"{role}: {content}")
                history_text = "\n".join(history_messages)
            
            prompt = f"""{self.system_prompt}

CONVERSATION HISTORY:
{history_text}

USER: {user_input}

Please respond naturally as Website Assistant, keeping your response helpful and clear."""
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error building website assistant prompt: {e}")
            return f"{self.system_prompt}\n\nUSER: {user_input}\n\nPlease respond naturally as Website Assistant."

# Global context builder instance
context_builder = LLMContextBuilder() 