# 🤖 Qubekit Voice AI Server

A comprehensive voice AI system with LiveKit integration, featuring dynamic app selection, real-time voice chat, and MongoDB-powered website assistance.

## 🚀 Features

### Core Functionality
- **🎙️ Real-time Voice Chat** - Bi-directional voice communication with AI
- **🤖 Website Assistant** - AI trained on your website's components and intents
- **🔄 Dynamic App Selection** - Choose from multiple apps with real-time data loading
- **🎫 JWT Token Management** - Secure LiveKit authentication
- **📱 React Client** - Modern web interface with auto-connection
- **🗄️ MongoDB Integration** - Dynamic data fetching from database

### AI Services
- **🧠 Claude (Anthropic)** - Advanced language model for conversations
- **🔊 ElevenLabs** - High-quality text-to-speech
- **👂 Deepgram** - Accurate speech-to-text
- **📡 LiveKit** - Real-time audio/video infrastructure

### Technical Stack
- **Backend**: Python, FastAPI, Pipecat AI
- **Frontend**: React, LiveKit Client SDK
- **Database**: MongoDB with Motor async driver
- **Authentication**: JWT tokens with API key validation

## 📁 Project Structure

```
├── src/                          # Python backend
│   ├── api/                      # FastAPI routes
│   │   └── auth_router.py        # Authentication endpoints
│   ├── auth/                     # Authentication services
│   │   └── token_service.py      # JWT token management
│   ├── db/                       # Database layer
│   │   ├── models.py             # Pydantic models
│   │   └── mongodb_service.py    # MongoDB operations
│   ├── pipecat_bot/              # AI bot implementation
│   │   ├── bot_runner.py         # Main bot orchestration
│   │   └── llm_context_builder.py # AI context management
│   ├── config.py                 # Configuration management
│   └── main.py                   # FastAPI application
├── simple-react-client/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── AppSelector.js    # App selection component
│   │   └── App.js                # Main React application
│   └── package.json
├── test/                         # Testing utilities
│   └── fetch_all_apps.py         # MongoDB data discovery
├── requirements.txt              # Python dependencies
├── runServer.py                  # Server startup script
└── .env                          # Environment configuration
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- MongoDB Atlas account
- LiveKit account
- API keys for Claude, ElevenLabs, and Deepgram

### 1. Environment Setup
```bash
# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt

# Install React dependencies
cd simple-react-client
npm install
cd ..
```

### 2. Configuration
Copy `.env.example` to `.env` and configure:

```env
# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_ROOM_NAME=your_room_name
LIVEKIT_PARTICIPANT_NAME=WebsiteAssistant
LIVEKIT_URL=wss://your-project.livekit.cloud

# AI Services
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_DEFAULT_MODEL=claude-3-5-sonnet-20241022
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id
DEEPGRAM_API_KEY=your_deepgram_key

# Database
MONGODB_URI=your_mongodb_connection_string

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8002
DEBUG=false
```

### 3. Database Setup
Run the data discovery script to fetch available apps:
```bash
python test/fetch_all_apps.py
```

## 🚀 Running the Application

### Start the Server
```bash
source .venv/bin/activate
python runServer.py
```

### Start the React Client
```bash
cd simple-react-client
npm start
```

The application will be available at:
- **React Client**: http://localhost:3000
- **API Server**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs

## 🎯 Usage

### 1. App Selection
- The client automatically loads available apps from MongoDB
- Select an app ID to load its website data into the AI context
- Default app is pre-selected based on component count

### 2. Voice Interaction
- Click "Connect" to start the voice chat
- Allow microphone access when prompted
- Speak naturally with the AI assistant
- The AI has knowledge of your website's components and intents

### 3. API Endpoints

#### Authentication
- `POST /api/v1/token` - Generate LiveKit JWT token
- `GET /api/v1/token/validate` - Validate existing token
- `GET /api/v1/config` - Get server configuration
- `GET /api/v1/apps` - List available apps

#### Bot Control
- `POST /bot/start` - Start AI bot with app ID
- `POST /bot/stop` - Stop AI bot
- `GET /bot/status` - Get bot status

## 🔧 Development

### Adding New Apps
1. Add app data to MongoDB with collections:
   - `components` - Website components with interactive elements
   - `intents` - User intents and patterns
   - `apps` - App metadata (optional)

2. Use the app ID in the React client to load the data

### Customizing AI Behavior
Edit `src/pipecat_bot/llm_context_builder.py` to modify:
- System prompts
- Context building logic
- Response formatting

### Testing
```bash
# Test MongoDB connection and data
python test/fetch_all_apps.py

# Test API endpoints
curl -H "X-API-Key: test_api_key_123" http://localhost:8002/api/v1/apps
```

## 🌐 Deployment

### Environment Variables
Ensure all production environment variables are set:
- Use production MongoDB URI
- Set `DEBUG=false`
- Use production API keys
- Configure proper CORS origins

### Docker (Optional)
```dockerfile
# Example Dockerfile structure
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8002
CMD ["python", "runServer.py"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Allow microphone permissions in browser
   - Check browser security settings for localhost

2. **MongoDB Connection Failed**
   - Verify MongoDB URI in `.env`
   - Check network connectivity
   - Ensure database exists

3. **LiveKit Connection Issues**
   - Verify LiveKit credentials
   - Check room name configuration
   - Ensure WebRTC is supported

4. **AI Service Errors**
   - Verify API keys for Claude, ElevenLabs, Deepgram
   - Check API quotas and limits
   - Review model names and availability

### Debug Mode
Set `DEBUG=true` in `.env` for detailed logging.

## 📝 API Documentation

Full API documentation is available at `/docs` when the server is running.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Pipecat AI** - Voice AI pipeline framework
- **LiveKit** - Real-time communication infrastructure
- **Anthropic Claude** - Advanced language model
- **ElevenLabs** - Text-to-speech synthesis
- **Deepgram** - Speech-to-text recognition

---

**Built with ❤️ for seamless voice AI experiences**