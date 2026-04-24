import React, { useState, useRef, useEffect } from 'react';
import {
  Room,
  RoomEvent,
  ConnectionState,
  Track,
} from 'livekit-client';
import './App.css';
import MonitoringSystem from './utils/MonitoringSystem';
import MonitoringDashboard from './components/MonitoringUI';
import clientLogger from './utils/ClientLogger';

// Configuration
const SERVER_URL = process.env.REACT_APP_SERVER_URL || 'http://localhost:8004';

function App() {
  // Auth state
  const [userName, setUserName] = useState('');
  const [apiKey, setApiKey] = useState('test_key_123');
  const [authResponse, setAuthResponse] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  // Connection state
  const [serverUrl, setServerUrl] = useState('');
  const [token, setToken] = useState('');
  const [roomName, setRoomName] = useState('');
  const [connectionState, setConnectionState] = useState(ConnectionState.Disconnected);
  const [participants, setParticipants] = useState([]);
  const [logs, setLogs] = useState(['🔐 Welcome to Re Simple Client - Auth-enabled Voice AI']);

  // Room reference
  const roomRef = useRef(null);
  const audioContainerRef = useRef(null);

  // Generate unique instance ID for multi-instance support
  const [instanceId] = useState(() => `instance_${Math.random().toString(36).substring(2, 8)}`);

  // Monitoring system state
  const [monitoringSystem, setMonitoringSystem] = useState(null);
  const [toolStatus, setToolStatus] = useState({
    staticDataLoader: 'inactive',
    smartActionExecutor: 'inactive',
    conversationTracker: 'inactive'
  });
  const [conversationLog, setConversationLog] = useState([]);
  const [intentLog, setIntentLog] = useState([]);
  const [staticDataStatus, setStaticDataStatus] = useState(null);
  const [showMonitoring, setShowMonitoring] = useState(true);

  const addLog = (message) => {
    const logMessage = `[${new Date().toLocaleTimeString()}] ${message}`;
    setLogs((prev) => [...prev.slice(-100), logMessage]);
    
    // Also log to client logger
    clientLogger.info(message);
  };

  // Initialize monitoring system
  const initializeMonitoringSystem = async () => {
    clientLogger.info('🔧 APP: initializeMonitoringSystem called');
    clientLogger.info('🔧 APP: SERVER_URL:', SERVER_URL);
    
    if (!SERVER_URL) {
      clientLogger.error('❌ APP: No SERVER_URL available, skipping monitoring initialization');
      return;
    }
    
    const monitoring = new MonitoringSystem(SERVER_URL);
    console.log('🔧 APP: MonitoringSystem instance created');
    
    // Set up callbacks
    monitoring.setCallbacks({
      onConversationUpdate: (entry) => {
        console.log('🔧 APP: onConversationUpdate callback called with:', entry);
        setConversationLog(prev => [...prev, entry]);
        addLog(`💬 ${entry.speaker === 'user' ? 'You' : 'AI'}: ${entry.text}`);
      },
      onIntentUpdate: (intent) => {
        console.log('🔧 APP: onIntentUpdate callback called with:', intent);
        setIntentLog(prev => [...prev, intent]);
        addLog(`🎯 AI Intent: ${intent.text} (${intent.actionType})`);
      },
      onToolStatusUpdate: (status) => {
        console.log('🔧 APP: onToolStatusUpdate callback called with:', status);
        setToolStatus(status);
      },
      onStaticDataUpdate: (status) => {
        console.log('🔧 APP: onStaticDataUpdate callback called with:', status);
        setStaticDataStatus(status);
        addLog(`📦 Static data: ${status.status}`);
      }
    });

    console.log('🔧 APP: Callbacks set, initializing monitoring system...');
    const success = await monitoring.initialize();
    if (success) {
      console.log('🔧 APP: Monitoring system initialized successfully, setting state...');
      setMonitoringSystem(monitoring);
      // Also store in window for global access
      window.monitoringSystem = monitoring;
      console.log('🔧 APP: Monitoring system state set:', monitoring);
      console.log('🔧 APP: Monitoring system stored in window:', window.monitoringSystem);
      addLog('✅ Monitoring system initialized');
    } else {
      console.log('❌ APP: Failed to initialize monitoring system');
      addLog('❌ Failed to initialize monitoring system');
    }
  };

  // Send static component data
  const sendStaticComponentData = async () => {
    console.log('📤 APP: sendStaticComponentData called');
    console.log('📤 APP: monitoringSystem available:', !!monitoringSystem);
    console.log('📤 APP: monitoringSystem state:', monitoringSystem);
    
    // Get monitoring system from window if not in state
    let currentMonitoringSystem = monitoringSystem;
    if (!currentMonitoringSystem) {
      console.log('🔧 APP: Trying to get monitoring system from window...');
      currentMonitoringSystem = window.monitoringSystem;
      if (currentMonitoringSystem) {
        console.log('🔧 APP: Found monitoring system in window, updating state...');
        setMonitoringSystem(currentMonitoringSystem);
      }
    }
    
    if (!currentMonitoringSystem) {
      console.log('🔧 APP: Trying to get monitoring system from state...');
      // Wait a bit for state to update
      await new Promise(resolve => setTimeout(resolve, 100));
      currentMonitoringSystem = monitoringSystem;
      console.log('🔧 APP: After wait, monitoringSystem available:', !!currentMonitoringSystem);
    }
    
    if (!currentMonitoringSystem) {
      console.log('❌ APP: No monitoring system available, skipping static data send');
      return;
    }
    
    const componentData = {
      name: 'Voice AI Interface',
      routeName: '/voice-chat',
      description: 'Voice AI interface with monitoring capabilities',
      navigatorType: 'screen',
      interactiveElements: [
        {
          type: 'button',
          testID: 'monitoring-toggle-btn',
          textContent: 'Toggle Monitoring',
          accessibilityLabel: 'Toggle monitoring dashboard visibility'
        },
        {
          type: 'button',
          testID: 'clear-logs-btn',
          textContent: 'Clear Logs',
          accessibilityLabel: 'Clear conversation and intent logs'
        }
      ],
      intents: [
        {
          schema: 'action.toggle_monitoring',
          text: 'Toggle monitoring dashboard'
        },
        {
          schema: 'action.clear_logs',
          text: 'Clear conversation logs'
        }
      ]
    };

    console.log('📤 APP: About to send component data:', componentData);
    await currentMonitoringSystem.sendStaticData(componentData);
    console.log('📤 APP: sendStaticData call completed');
  };

  // Auth function
  const handleAuth = async () => {
    if (!userName.trim() || !apiKey.trim()) {
      setAuthResponse({ error: 'Please enter both name and API key' });
      return;
    }

    setAuthLoading(true);
    setAuthResponse(null);
    addLog(`🔐 Authenticating user: ${userName}`);

    try {
      const response = await fetch(`${SERVER_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          user_identity: userName
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Success - store auth data and autofill connection
        setAuthResponse(data);
        setIsAuthenticated(true);
        setServerUrl(data.livekit_url);
        setToken(data.livekit_token);
        setRoomName(data.room_name);
        
        addLog(`✅ Authentication successful!`);
        addLog(`🏠 Room assigned: ${data.room_name}`);
        addLog(`⏰ Session expires in: ${data.expires_in} seconds`);
        
      } else {
        // Error
        setAuthResponse({ error: data.detail || 'Authentication failed' });
        addLog(`❌ Authentication failed: ${data.detail || 'Unknown error'}`);
      }

    } catch (error) {
      setAuthResponse({ error: `Connection error: ${error.message}` });
      addLog(`❌ Auth connection error: ${error.message}`);
    } finally {
      setAuthLoading(false);
    }
  };

  // Connection functions
  const connectToRoom = async () => {
    if (!serverUrl || !token) {
      addLog('❌ Missing server URL or token');
      return;
    }

    addLog(`🔗 Connecting to room: ${roomName}`);
    addLog(`🌐 Server: ${serverUrl}`);
    setConnectionState(ConnectionState.Connecting);

    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
    });

    // Register event listeners
    room.on(RoomEvent.ConnectionStateChanged, handleConnectionStateChange)
        .on(RoomEvent.ParticipantConnected, handleParticipantConnected)
        .on(RoomEvent.ParticipantDisconnected, handleParticipantDisconnected)
        .on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
        .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
        .on(RoomEvent.Disconnected, handleDisconnect);

    try {
      await room.connect(serverUrl, token);
      addLog(`✅ Connected to room: ${room.name}`);
      roomRef.current = room;

      // Update participants list
      updateParticipantsList();
      
      // Enable microphone
      try {
        await room.localParticipant.setMicrophoneEnabled(true);
        addLog('🎤 Microphone enabled - you can now talk to the AI');
      } catch (micError) {
        addLog(`⚠️ Microphone access failed: ${micError.message}`);
        addLog('💡 Please allow microphone access to talk to the AI');
      }

      // Initialize monitoring system after successful connection
      await initializeMonitoringSystem();
      
      // Send static component data when both participants are ready
      console.log('🔧 APP: Checking participants for static data send:', participants.length);
      
      // Force update participants list
      updateParticipantsList();
      
      // Wait a bit for participants to be detected, then retry
      setTimeout(async () => {
        console.log('🔧 APP: Retrying participant check after delay:', participants.length);
        updateParticipantsList(); // Force update again
        
        // Get current participants count
        const currentParticipants = roomRef.current ? [
          roomRef.current.localParticipant,
          ...Array.from(roomRef.current.remoteParticipants.values())
        ] : [];
        
        console.log('🔧 APP: Current participants count:', currentParticipants.length);
        
        if (currentParticipants.length >= 2) {
          console.log('🔧 APP: Participants >= 2, sending static component data...');
          await sendStaticComponentData();
        } else {
          console.log('🔧 APP: Still not enough participants, will retry again...');
          // Try one more time after another delay
          setTimeout(async () => {
            console.log('🔧 APP: Final participant check:', participants.length);
            updateParticipantsList(); // Force update one more time
            
            // Get current participants count again
            const finalParticipants = roomRef.current ? [
              roomRef.current.localParticipant,
              ...Array.from(roomRef.current.remoteParticipants.values())
            ] : [];
            
            console.log('🔧 APP: Final participants count:', finalParticipants.length);
            
            if (finalParticipants.length >= 2) {
              console.log('🔧 APP: Participants >= 2, sending static component data...');
              await sendStaticComponentData();
            } else {
              console.log('🔧 APP: Giving up on static data send, participants:', finalParticipants.length);
              // Try sending anyway after 5 seconds
              setTimeout(async () => {
                console.log('🔧 APP: Forcing static data send after timeout...');
                await sendStaticComponentData();
              }, 5000);
            }
          }, 2000);
        }
      }, 1000);

    } catch (error) {
      console.error('Connection failed:', error);
      addLog(`❌ Connection failed: ${error.message}`);
      setConnectionState(ConnectionState.Disconnected);
    }
  };

  const disconnectFromRoom = async () => {
    if (roomRef.current) {
      addLog('🔌 Disconnecting from room...');
      await roomRef.current.disconnect();
    }
  };

  // Event handlers
  const handleConnectionStateChange = (state) => {
    setConnectionState(state);
    addLog(`🔄 Connection state: ${state}`);
  };

  const handleParticipantConnected = (participant) => {
    addLog(`➡️ Participant joined: ${participant.identity}`);
    updateParticipantsList();
  };

  const handleParticipantDisconnected = (participant) => {
    addLog(`⬅️ Participant left: ${participant.identity}`);
    updateParticipantsList();
  };

  const handleTrackSubscribed = (track, publication, participant) => {
    if (track.kind === Track.Kind.Audio && !participant.isLocal) {
      addLog(`🔊 AI voice connected from ${participant.identity}`);
      const element = track.attach();
      audioContainerRef.current?.appendChild(element);
    }
  };

  const handleTrackUnsubscribed = (track) => {
    track.detach().forEach((element) => element.remove());
  };

  const handleDisconnect = () => {
    addLog('🔌 Disconnected from room');
    roomRef.current = null;
    setParticipants([]);
    setConnectionState(ConnectionState.Disconnected);
    
    // Disconnect monitoring system
    if (monitoringSystem) {
      monitoringSystem.disconnect();
      setMonitoringSystem(null);
    }
  };

  const updateParticipantsList = () => {
    console.log('🔧 APP: updateParticipantsList called');
    if (roomRef.current) {
      const localParticipant = roomRef.current.localParticipant;
      const remoteParticipants = Array.from(roomRef.current.remoteParticipants.values());
      
      console.log('🔧 APP: Local participant:', localParticipant?.identity);
      console.log('🔧 APP: Remote participants:', remoteParticipants.map(p => p.identity));
      
      const allParticipants = [localParticipant, ...remoteParticipants];
      console.log('🔧 APP: Total participants:', allParticipants.length);
      console.log('🔧 APP: All participant identities:', allParticipants.map(p => p?.identity));
      
      setParticipants(allParticipants);
    } else {
      console.log('🔧 APP: No room reference available');
    }
  };

  // Reset auth (logout)
  const handleLogout = () => {
    setIsAuthenticated(false);
    setAuthResponse(null);
    setServerUrl('');
    setToken('');
    setRoomName('');
    if (roomRef.current) {
      roomRef.current.disconnect();
    }
    addLog('🔐 Logged out - session cleared');
  };

  const isConnected = connectionState === ConnectionState.Connected;
  const isConnecting = connectionState === ConnectionState.Connecting;

  return (
    <div className="container">
      <h1>🔐 Re Simple Client - Auth Voice AI</h1>
      
      {/* Multi-instance info */}
      <div className="multi-instance-info">
        <h4>🌐 Multi-Instance Support</h4>
        <p>You can open multiple tabs/windows - each will get a separate room and AI context!</p>
        <div className="instance-list">
          <span className="instance-badge">Current: {instanceId}</span>
        </div>
      </div>

      {/* Auth Section */}
      <div className="auth-section">
        <h2>🔐 Authentication</h2>
        
        {!isAuthenticated ? (
          <div className="auth-form">
            <div className="form-group">
              <label htmlFor="userName">Your Name:</label>
              <input
                type="text"
                id="userName"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="Enter your name (e.g., john_doe)"
                disabled={authLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="apiKey">X-API-Key:</label>
              <input
                type="text"
                id="apiKey"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                disabled={authLoading}
              />
            </div>

            <div className="button-group">
              <button 
                className="btn btn-primary" 
                onClick={handleAuth}
                disabled={authLoading || !userName.trim() || !apiKey.trim()}
              >
                {authLoading ? '🔄 Authenticating...' : '🔐 Authenticate'}
              </button>
            </div>

            {/* Auth Response Display */}
            {authResponse && (
              <div className={`auth-response ${authResponse.error ? 'error' : 'success'}`}>
                {authResponse.error ? (
                  <div>
                    <strong>❌ Authentication Failed:</strong><br/>
                    {authResponse.error}
                  </div>
                ) : (
                  <div>
                    <strong>✅ Authentication Successful!</strong><br/>
                    <strong>Session ID:</strong> {authResponse.session_id}<br/>
                    <strong>Room Name:</strong> {authResponse.room_name}<br/>
                    <strong>User Identity:</strong> {authResponse.user_identity}<br/>
                    <strong>Expires In:</strong> {authResponse.expires_in} seconds<br/>
                    <strong>LiveKit URL:</strong> {authResponse.livekit_url}<br/>
                    <strong>Token:</strong> {authResponse.livekit_token.substring(0, 50)}...<br/>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div>
            <p>✅ Authenticated as: <strong>{userName}</strong></p>
            <p>🏠 Room: <strong>{roomName}</strong></p>
            <button className="btn btn-secondary" onClick={handleLogout}>
              🚪 Logout
            </button>
          </div>
        )}
      </div>

      {/* Connection Section */}
      <div className={`connection-section ${!isAuthenticated ? 'disabled' : ''}`}>
        <h2>🔗 LiveKit Connection</h2>
        
        <div className="form-group">
          <label htmlFor="serverUrl">LiveKit Server URL:</label>
          <input
            type="text"
            id="serverUrl"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="Auto-filled from auth response"
            disabled={!isAuthenticated}
          />
        </div>

        <div className="form-group">
          <label htmlFor="token">JWT Token:</label>
          <input
            type="text"
            id="token"
            value={token ? `${token.substring(0, 50)}...` : ''}
            placeholder="Auto-filled from auth response"
            disabled={true}
          />
        </div>

        <div className="form-group">
          <label htmlFor="roomName">Room Name:</label>
          <input
            type="text"
            id="roomName"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            placeholder="Auto-filled from auth response"
            disabled={!isAuthenticated}
          />
        </div>

        <div className="button-group">
          <button 
            className="btn btn-success" 
            onClick={connectToRoom} 
            disabled={!isAuthenticated || isConnected || isConnecting || !serverUrl || !token}
          >
            {isConnecting ? '🔄 Connecting...' : '🚀 Connect to AI'}
          </button>
          <button 
            className="btn btn-danger" 
            onClick={disconnectFromRoom} 
            disabled={!isConnected}
          >
            🔌 Disconnect
          </button>
        </div>

        <div className={`status-display ${connectionState.toLowerCase()}`}>
          <strong>Connection Status:</strong> {connectionState}
        </div>
      </div>

      {/* Participants Section */}
      {isConnected && (
        <div className="participants-section">
          <h2>👥 Participants ({participants.length})</h2>
          <div className="participants-list">
            {participants.map((p) => (
              <div key={p.sid} className="participant">
                <span>
                  {p.identity} {p.isLocal ? '(You)' : '(AI Assistant)'}
                </span>
                <span>
                  {p.isMicrophoneEnabled ? '🎤' : '🔇'}
                  {p.isSpeaking ? ' 🗣️' : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Voice Chat Section */}
      {isConnected && (
        <div className="voice-chat-section">
          <h2>🎤 Voice Chat with AI</h2>
          <div className="voice-controls">
            <div className="voice-status">
              <div className={`voice-indicator ${isConnected ? 'active' : ''}`}></div>
              <div>
                <strong>Status:</strong> {isConnected ? 'Ready to chat!' : 'Not connected'}<br/>
                <strong>Instructions:</strong> Just speak naturally - the AI will respond with voice
              </div>
            </div>
            
            <div style={{ padding: '15px', background: '#e7f3ff', borderRadius: '8px' }}>
              <h4>💡 Try saying:</h4>
              <ul>
                <li>"Hello, can you hear me?"</li>
                <li>"What can you help me with?"</li>
                <li>"Tell me about this application"</li>
                <li>"How does multi-room support work?"</li>
              </ul>
            </div>
          </div>
          
          {/* Monitoring Toggle Button */}
          <div className="monitoring-controls">
            <button 
              className="btn btn-secondary"
              onClick={() => setShowMonitoring(!showMonitoring)}
            >
              {showMonitoring ? '📊 Hide Monitoring' : '📊 Show Monitoring'}
            </button>
            <button 
              className="btn btn-warning"
              onClick={() => {
                setConversationLog([]);
                setIntentLog([]);
                addLog('🧹 Conversation and intent logs cleared');
              }}
            >
              🧹 Clear Logs
            </button>
          </div>
        </div>
      )}

      {/* Monitoring Dashboard */}
      {isConnected && showMonitoring && (
        <div className="monitoring-section">
          <MonitoringDashboard
            toolStatus={toolStatus}
            conversationLog={conversationLog}
            intentLog={intentLog}
            staticDataStatus={staticDataStatus}
          />
        </div>
      )}

      {/* Logs Section */}
      <div className="logs-section">
        <h2>📜 Activity Log</h2>
        <div className="logs">
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>

      {/* Hidden audio container for AI voice */}
      <div ref={audioContainerRef} style={{ display: 'none' }} />
    </div>
  );
}

export default App;