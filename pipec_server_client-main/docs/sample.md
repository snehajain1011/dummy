📡 SSE Message Formats
1. Connection Event (Server → Client)

{
  "type": "connection",
  "status": "connected",
  "timestamp": 1755183209.2106001
}
2. Keepalive Event (Server → Client)
{
  "type": "keepalive",
  "timestamp": 1755183239.2106342
}
3. UI Action Command (Bot → Client via SSE)
{
  "type": "ui_action",
  "data": {
    "action_type": "click",
    "target_element": "refresh-btn",
    "current_page": "/dashboard",
    "confidence": 0.9,
    "instruction": "I'll refresh the data for you.",
    "user_request": "refresh the data"
  }
}
4. Navigation Command (Bot → Client via SSE)
{
  "type": "navigation_command",
  "data": {
    "action": "navigate",
    "target": "/profile",
    "instruction": "I'll take you to the profile page.",
    "user_request": "go to profile"
  }
}
5. Tool Log Event (Bot → Client via SSE)
{
  "type": "tool_log",
  "data": {
    "tool": "StaticDataLoader",
    "action": "load_app_data_sync",
    "input": {
      "components_count": 1,
      "intents_count": 6
    },
    "output": {
      "pages": 1,
      "elements": 6,
      "routes": ["/test-dashboard"],
      "element_ids": ["go-to-dashboard-btn", "save-profile-btn"]
    },
    "timestamp": 1755177777.4854045
  }
}
6. Error Event (Server → Client)
{
  "type": "error",
  "message": "Error description here"
}