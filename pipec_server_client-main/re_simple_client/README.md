# 🔐 Re Simple Client - Auth-enabled Voice AI

A React-based client that demonstrates the complete authentication flow with multi-room support for the LiveKit Voice AI system.

## ✨ Features

### 🔐 Authentication Flow
1. **Auth Box**: Enter name and X-API-Key
2. **Instant Response**: Get auth response displayed below input
3. **Auto-fill**: Connection details automatically populated
4. **Secure**: Proper token-based authentication

### 🌐 Multi-Room Support
- **Multiple Instances**: Open multiple tabs/windows
- **Separate Rooms**: Each instance gets its own room
- **Isolated Context**: AI maintains separate conversations
- **Concurrent Users**: All instances work simultaneously

### 🎤 Voice Chat
- **Real-time Audio**: Talk directly to AI assistant
- **Voice Response**: AI responds with natural speech
- **Microphone Control**: Easy enable/disable
- **Connection Status**: Clear visual indicators

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd re_simple_client
npm install
```

### 2. Configure Environment (Optional)
Create `.env` file:
```env
REACT_APP_SERVER_URL=http://localhost:8004
```

### 3. Start the Client
```bash
npm start
```

### 4. Use the Application

#### Step 1: Authenticate
1. Enter your name (e.g., `john_doe`)
2. Enter API key (e.g., `test_key_123`)
3. Click "🔐 Authenticate"
4. See response below with session details

#### Step 2: Connect
1. Connection details auto-filled from auth response
2. Click "🚀 Connect to AI"
3. Allow microphone access when prompted
4. Start talking to the AI!

## 🧪 Testing Multi-Room Support

### Test Scenario 1: Multiple Users
1. Open 3 browser tabs
2. Use different names in each:
   - Tab 1: `alice_smith` + `test_key_123`
   - Tab 2: `john_doe` + `d761c33b-e40c-4d95-8570-ecde948ac425`
   - Tab 3: `bob_wilson` + `another_test_key_456`
3. Authenticate and connect all tabs
4. Each gets separate room and AI context

### Test Scenario 2: Same User, Multiple Sessions
1. Open 2 tabs with same credentials
2. Each gets different room name (timestamp-based)
3. AI maintains separate conversation in each

## 📊 Expected Behavior

### Authentication Response
```json
{
  "session_id": "sess_abc12345",
  "room_name": "room_john_doe_1737000123",
  "livekit_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "livekit_url": "wss://your-livekit-server.com",
  "expires_in": 1800,
  "expires_at": "2025-01-15T10:30:00Z",
  "user_identity": "john_doe"
}
```

### Connection Flow
1. **Auth**: `POST /auth/login` → Get session + token
2. **Connect**: LiveKit connection with token
3. **AI Join**: Bot joins room in background
4. **Voice Chat**: Real-time audio conversation

## 🔧 Configuration

### Server URL
- Default: `http://localhost:8004`
- Override with `REACT_APP_SERVER_URL` env var

### API Keys (for testing)
- `test_key_123`
- `d761c33b-e40c-4d95-8570-ecde948ac425`
- `another_test_key_456`

## 🎯 Architecture

```
Re Simple Client
├── Auth Section
│   ├── Name Input
│   ├── API Key Input
│   ├── Auth Button
│   └── Response Display
├── Connection Section (auto-filled)
│   ├── LiveKit URL
│   ├── JWT Token
│   ├── Room Name
│   └── Connect Button
├── Voice Chat Section
│   ├── Participants List
│   ├── Voice Status
│   └── Chat Instructions
└── Activity Log
    └── Real-time Events
```

## 🌟 Key Benefits

1. **Fast Authentication**: Sub-second auth response
2. **Multi-Room Ready**: Scales to multiple concurrent users
3. **User-Friendly**: Clear visual feedback and instructions
4. **Production-Ready**: Proper error handling and logging
5. **Responsive Design**: Works on desktop and mobile

## 🔍 Troubleshooting

### Authentication Issues
- Check API key format
- Verify server is running on correct port
- Check network connectivity

### Connection Issues
- Ensure microphone permissions granted
- Check LiveKit server accessibility
- Verify token hasn't expired

### Multi-Room Issues
- Each tab should show different room names
- Check server logs for bot connections
- Verify separate AI contexts

## 📝 Development

### File Structure
```
re_simple_client/
├── public/
│   └── index.html
├── src/
│   ├── App.js          # Main component
│   ├── App.css         # Styles
│   ├── index.js        # Entry point
│   └── index.css       # Global styles
├── package.json        # Dependencies
└── README.md          # This file
```

### Key Components
- **Auth Section**: Handles login flow
- **Connection Section**: Manages LiveKit connection
- **Voice Chat**: Real-time audio interface
- **Activity Log**: Event tracking and debugging

This client demonstrates the complete auth-enabled voice AI experience with multi-room support! 🎉