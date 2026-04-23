import React, { useState, useRef, useEffect } from 'react';
import {
  Room,
  RoomEvent,
  ConnectionState,
  Track,
} from 'livekit-client';
// App selection removed per requirements
import './App.css';

// Configuration from environment variables
const SERVER_URL = process.env.REACT_APP_SERVER_URL || 'https://api-webrtc.cuekit.ai';
const API_KEY = process.env.REACT_APP_API_KEY || 'test_api_key_123';

function App() {
  const [serverUrl, setServerUrl] = useState('');
  const [token, setToken] = useState('');
  const [connectionState, setConnectionState] = useState(ConnectionState.Disconnected);
  const [participants, setParticipants] = useState([]);
  const [logs, setLogs] = useState(['📝 Starting auto-connection process...']);
  const [toolLogs, setToolLogs] = useState([]);
  const [userIdentity, setUserIdentity] = useState('user_' + Math.random().toString(36).substr(2, 9));
  const [autoConnecting, setAutoConnecting] = useState(true);
  // App selection removed
  const [aiNavigationMode, setAiNavigationMode] = useState(false);
  const [testCommand, setTestCommand] = useState('');
  const [currentPage, setCurrentPage] = useState('voice_chat');
  const [navigationCommands, setNavigationCommands] = useState([]);
  
  const roomRef = useRef(null);
  const audioContainerRef = useRef(null);

  const addLog = (message) => {
    setLogs((prev) => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  // Auto-connect on component mount
  useEffect(() => {
    autoConnect();
    return () => {
      roomRef.current?.disconnect();
    };
  }, []);

  // Listen for navigation commands via Server-Sent Events
  useEffect(() => {
    let eventSource = null;
    let reconnectTimeout = null;
    
    const connectSSE = () => {
      try {
        addLog(`🔄 Connecting to SSE stream...`);
        eventSource = new EventSource(`${SERVER_URL}/navigation/stream`);
        
        eventSource.onmessage = (event) => {
          try {
            console.log('🔍 SSE message received:', event.data);
            const command = JSON.parse(event.data);
            console.log('🔍 Parsed command:', command);
            
            if (command.type === 'navigation_command' || command.type === 'ui_action') {
              setNavigationCommands(prev => [...prev, command]);
              executeNavigationCommand(command);
              addLog(`📡 Received real-time command: ${command.data?.instruction || 'Unknown command'}`);
            } else if (command.type === 'tool_log') {
              console.log('🛠️ Tool log received:', command.data);
              setToolLogs(prev => [...prev.slice(-200), command.data]);
              addLog(`🛠️ Tool: ${command.data.tool} • ${command.data.action}`);
            } else {
              console.log('🔍 Unknown command type:', command.type);
            }
          } catch (error) {
            console.error('❌ Error parsing SSE data:', error);
            addLog(`❌ Error parsing SSE data: ${error.message}`);
          }
        };

        eventSource.onerror = (error) => {
          console.error('🔌 SSE connection error:', error);
          addLog(`🔌 SSE connection error, will auto-reconnect in 3 seconds...`);
          if (eventSource) {
            eventSource.close();
          }
          // Auto-reconnect after 3 seconds
          reconnectTimeout = setTimeout(connectSSE, 3000);
        };

        eventSource.onopen = () => {
          addLog(`✅ Real-time navigation stream connected`);
          // Send dashboard data to server once connected (via HTTP to /ai/data)
          sendDashboardData();
        };
        
      } catch (error) {
        console.error('❌ Error creating SSE connection:', error);
        addLog(`❌ Error creating SSE connection: ${error.message}`);
        // Auto-reconnect after 3 seconds
        reconnectTimeout = setTimeout(connectSSE, 3000);
      }
    };
    
    // Start the connection
    connectSSE();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      addLog(`🔌 SSE connection closed`);
    };
  }, []);

  const sendDashboardData = async () => {
    const dashboardData = {
      type: 'dashboard_data',
      data: {
        name: '🧪 AI Navigation Test Dashboard',
        routeName: '/test-dashboard',
        description: 'Test dashboard with 3 buttons, 1 text input, 1 toggle, 1 status box',
        navigatorType: 'screen',
        interactiveElements: [
          {
            type: 'button',
            testID: 'go-to-dashboard-btn',
            textContent: 'Go to Dashboard',
            accessibilityLabel: 'Navigate to dashboard page'
          },
          {
            type: 'button',
            testID: 'save-profile-btn',
            textContent: 'Save Profile',
            accessibilityLabel: 'Save profile changes'
          },
          {
            type: 'button',
            testID: 'send-screen-status-btn',
            textContent: 'Send Screen Status',
            accessibilityLabel: 'Send current screen status'
          },
          {
            type: 'input',
            testID: 'test-command-input',
            textContent: '',
            accessibilityLabel: 'Enter command to test'
          },
          {
            type: 'toggle',
            testID: 'ai-navigation-toggle',
            textContent: 'AI Navigation Mode',
            accessibilityLabel: 'Toggle AI navigation mode'
          },
          {
            type: 'status',
            testID: 'live-status-box',
            textContent: 'Live Status',
            accessibilityLabel: 'Current live status display'
          }
        ],
        intents: [
          {
            schema: 'action.go_to_dashboard',
            text: 'Navigate to the dashboard page'
          },
          {
            schema: 'action.save_profile',
            text: 'Save profile changes'
          },
          {
            schema: 'action.send_screen_status',
            text: 'Send current screen status'
          },
          {
            schema: 'action.test_command',
            text: 'Enter a test command'
          },
          {
            schema: 'action.toggle_ai_navigation',
            text: 'Toggle AI navigation mode on or off'
          },
          {
            schema: 'action.check_live_status',
            text: 'Check the current live status'
          }
        ]
      }
    };

    try {
      // Send dashboard data to server (post to /ai/data so bot handles it immediately)
      const response = await fetch(`${SERVER_URL}/ai/data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dashboardData)
      });
      
      if (response.ok) {
        addLog('✅ Dashboard data sent to server');
      } else {
        addLog('❌ Failed to send dashboard data');
      }
    } catch (error) {
      addLog(`❌ Error sending dashboard data: ${error.message}`);
    }
  };

  const executeNavigationCommand = (command) => {
    addLog(`📡 RECEIVED AI COMMAND: ${JSON.stringify(command, null, 2)}`);
    
    // Just log the received JSON - don't actually execute actions yet
    if (command.type === 'ui_action') {
      const { action_type, target_element, instruction, confidence } = command.data;
      addLog(`🎯 Action Type: ${action_type}`);
      addLog(`🎯 Target Element: ${target_element}`);
      addLog(`🎯 Instruction: ${instruction}`);
      addLog(`🎯 Confidence: ${confidence}`);
    } else if (command.type === 'navigation_command') {
      const { action, target, instruction } = command.data;
      addLog(`🧭 Navigation Action: ${action}`);
      addLog(`🧭 Target: ${target}`);
      addLog(`🧭 Instruction: ${instruction}`);
    }
    
    // TODO: Actual execution will be implemented later
    addLog(`✅ Command logged successfully`);
  };

  const autoConnect = async () => {
    addLog('🚀 Starting auto-connection...');
    
    try {
      // Step 1: Get server config
      addLog('📡 Fetching server configuration...');
      addLog(`🔗 Request URL: ${SERVER_URL}/api/v1/config`);
      addLog(`🔑 API Key: ${API_KEY}`);
      
      const configResponse = await fetch(`${SERVER_URL}/api/v1/config`, {
        headers: {
          'X-API-Key': API_KEY
        }
      });
      
      addLog(`📊 Config Response Status: ${configResponse.status}`);
      
      if (!configResponse.ok) {
        const errorText = await configResponse.text();
        addLog(`❌ Config Error: ${errorText}`);
        throw new Error(`Failed to fetch server config: ${configResponse.status}`);
      }
      
      const config = await configResponse.json();
      addLog(`✅ Server config loaded: ${config.livekit_url}`);
      addLog(`🏠 Room name: ${config.room_name}`);
      setServerUrl(config.livekit_url);
      
      // Step 2: Generate token automatically
      addLog('🎫 Generating token...');
      addLog(`👤 User Identity: ${userIdentity}`);
      addLog(`🏠 Room Name: ${config.room_name}`);
      addLog(`⏰ TTL: 7200 seconds`);
      
      const tokenPayload = {
        user_identity: userIdentity,
        room_name: config.room_name,
        ttl_seconds: 7200
      };
      
      addLog(`📦 Token Payload: ${JSON.stringify(tokenPayload)}`);
      
      const tokenResponse = await fetch(`${SERVER_URL}/api/v1/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify(tokenPayload)
      });
      
      addLog(`📊 Token Response Status: ${tokenResponse.status}`);
      
      if (!tokenResponse.ok) {
        const errorText = await tokenResponse.text();
        addLog(`❌ Token Error: ${errorText}`);
        throw new Error(`Failed to generate token: ${tokenResponse.status}`);
      }
      
      const tokenData = await tokenResponse.json();
      addLog(`✅ Token generated successfully!`);
      addLog(`🏠 Token Room: ${tokenData.room_name}`);
      addLog(`⏰ Token Expires In: ${tokenData.expires_in} seconds`);
      addLog(`🎫 Token Preview: ${tokenData.token.substring(0, 50)}...`);
      setToken(tokenData.token);
      
      // Step 3: Start AI bot (no app selection)
      addLog(`🤖 Starting AI bot...`);
      
      const botPayload = {};
      addLog(`📦 Bot Payload: ${JSON.stringify(botPayload)}`);
      
      const botResponse = await fetch(`${SERVER_URL}/bot/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        },
        body: JSON.stringify(botPayload)
      });
      
      addLog(`📊 Bot Response Status: ${botResponse.status}`);
      
      if (botResponse.ok) {
        const botData = await botResponse.json();
        addLog(`✅ AI bot started successfully!`);
        addLog(`📱 Bot App ID: ${botData.app_id || 'default'}`);
        addLog(`🤖 Bot Status: ${botData.status}`);
      } else {
        const errorText = await botResponse.text();
        addLog(`⚠️ Bot start response: ${errorText}`);
      }
      
      // Step 4: Auto-connect to room
      addLog('🔗 Connecting to LiveKit room...');
      await connectToRoom(config.livekit_url, tokenData.token);
      
    } catch (error) {
      addLog(`❌ Auto-connection failed: ${error.message}`);
      setAutoConnecting(false);
    }
  };

  // Event handlers
  const handleParticipantConnected = (participant) => {
    addLog(`➡️ Participant connected: ${participant.identity}`);
    updateParticipantsList();
  };

  const handleParticipantDisconnected = (participant) => {
    addLog(`⬅️ Participant disconnected: ${participant.identity}`);
    updateParticipantsList();
  };

  const updateParticipantsList = () => {
    if (roomRef.current) {
      const allParticipants = [
        roomRef.current.localParticipant,
        ...Array.from(roomRef.current.remoteParticipants.values())
      ];
      setParticipants(allParticipants);
    }
  };

  const handleConnectionStateChange = (state) => {
    setConnectionState(state);
    addLog(`Connection state changed: ${state}`);
    if (state === ConnectionState.Connected) {
      setAutoConnecting(false);
    }
  };

  const handleTrackSubscribed = (track, publication, participant) => {
    if (track.kind === Track.Kind.Audio && !participant.isLocal) {
      addLog(`🔊 Subscribed to audio track from ${participant.identity}`);
      const element = track.attach();
      audioContainerRef.current?.appendChild(element);
    }
  };

  const handleDataReceived = (payload, participant) => {
    try {
      const message = JSON.parse(new TextDecoder().decode(payload));
      addLog(`📡 Data received from ${participant?.identity}: ${message.type}`);
      
      if (message.type === 'navigation_command') {
        const { action, target, instruction } = message.data;
        addLog(`🧭 Navigation: ${instruction}`);
        
        // Execute navigation command
        if (action === 'navigate' && target) {
          addLog(`➡️ Navigating to: ${target}`);
          // Here you would implement actual navigation
          // window.location.href = target; // Example
        }
      } else if (message.type === 'ai_response') {
        addLog(`🤖 AI: ${message.data.message}`);
      }
    } catch (error) {
      addLog(`❌ Error parsing data: ${error.message}`);
    }
  };

  const sendScreenStatus = async (room) => {
    if (!room) return;
    
    const screenStatus = {
      type: 'screen_status',
      data: {
        current_page: '🧪 AI Navigation Test Dashboard',
        route: '/test-dashboard',
        elements_visible: ['go-to-dashboard-btn', 'save-profile-btn', 'send-screen-status-btn', 'test-command-input', 'ai-navigation-toggle', 'live-status-box'],
        user_action: 'page_active',
        timestamp: new Date().toISOString(),
        element_states: {
          'go-to-dashboard-btn': { enabled: true, visible: true },
          'save-profile-btn': { enabled: true, visible: true },
          'send-screen-status-btn': { enabled: true, visible: true },
          'test-command-input': { enabled: true, visible: true, value: testCommand },
          'ai-navigation-toggle': { enabled: true, visible: true, checked: aiNavigationMode },
          'live-status-box': { enabled: true, visible: true, value: `Current Page: ${currentPage} | AI Mode: ${aiNavigationMode ? 'Active' : 'Inactive'} | Route: / | Connection: ${connectionState}` }
        },
        dashboard_name: '🧪 AI Navigation Test Dashboard'
      }
    };
    
    try {
      // Send via HTTP so server bot always receives it (LiveKit data is optional)
      await fetch(`${SERVER_URL}/ai/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(screenStatus),
      });
      addLog(`📤 Sent screen status: ${screenStatus.data.current_page}`);
    } catch (error) {
      addLog(`❌ Error sending screen status: ${error.message}`);
    }
  };

  const sendTestCommand = async (room, command) => {
    if (!room) return;
    
    const userCommand = {
      type: 'user_command',
      data: {
        command: command,
        timestamp: new Date().toISOString()
      }
    };
    
    try {
      await room.localParticipant.publishData(
        new TextEncoder().encode(JSON.stringify(userCommand)),
        { reliable: true }
      );
      addLog(`📤 Sent command: ${command}`);
    } catch (error) {
      addLog(`❌ Error sending command: ${error.message}`);
    }
  };

  const handleTrackUnsubscribed = (track) => {
    track.detach().forEach((element) => element.remove());
  };

  const handleDisconnect = () => {
    addLog('Disconnected from the room.');
    roomRef.current = null;
    setParticipants([]);
    setConnectionState(ConnectionState.Disconnected);
    setAutoConnecting(false);
  };

  const connectToRoom = async (liveKitUrl, jwtToken) => {
    if (!liveKitUrl || !jwtToken) {
      addLog('❌ Missing server URL or token');
      return;
    }

    addLog(`Connecting to ${liveKitUrl}...`);
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
        .on(RoomEvent.DataReceived, handleDataReceived)
        .on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
        .on(RoomEvent.Disconnected, handleDisconnect);

    try {
      await room.connect(liveKitUrl, jwtToken);
      addLog(`✅ Successfully connected to room: ${room.name}`);
      roomRef.current = room;

      // Update participants list with all current participants
      updateParticipantsList();
      
      // Enable microphone with error handling
      try {
        await room.localParticipant.setMicrophoneEnabled(true);
        addLog('🎤 Microphone enabled successfully.');
      } catch (micError) {
        addLog(`⚠️ Microphone access failed: ${micError.message}`);
        addLog('💡 Please allow microphone access in your browser settings.');
        // Continue without microphone - you can still hear the AI
      }

      // Send initial screen status
      setTimeout(() => sendScreenStatus(room), 1000);
      
    } catch (error) {
      console.error('Connection failed:', error);
      addLog(`❌ Connection failed: ${error.message}`);
      setConnectionState(ConnectionState.Disconnected);
      setAutoConnecting(false);
    }
  };

  const disconnectFromRoom = async () => {
    if (roomRef.current) {
      addLog('Disconnecting...');
      await roomRef.current.disconnect();
    }
  };

  const isConnected = connectionState === ConnectionState.Connected;

  return (
    <div className="container">
      <h1>🎙️ Simple LiveKit Client</h1>
      
      {autoConnecting && (
        <div className="auto-connect">
          <div className="loading">🔄 Auto-connecting to voice AI...</div>
          <p>Fetching config → Generating token → Connecting to room</p>
        </div>
      )}

      {/* App selection removed */}

      <div className="config-section">
        <div className="form-group">
          <label htmlFor="userIdentity">Your Identity:</label>
          <input
            type="text"
            id="userIdentity"
            value={userIdentity}
            onChange={(e) => setUserIdentity(e.target.value)}
            disabled={isConnected}
          />
        </div>
        
        {/* Selected App ID removed */}
        
        <div className="form-group">
          <label htmlFor="serverUrl">LiveKit Server URL:</label>
          <input
            type="text"
            id="serverUrl"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="Auto-filled from server config"
            disabled={true}
          />
        </div>

        <div className="form-group">
          <label htmlFor="token">JWT Token:</label>
          <input
            type="text"
            id="token"
            value={token ? `${token.substring(0, 50)}...` : ''}
            placeholder="Auto-generated token"
            disabled={true}
          />
        </div>
      </div>

      <div className="button-group">
        <button 
          className="btn-primary" 
          onClick={() => connectToRoom(serverUrl, token)} 
          disabled={isConnected || !serverUrl || !token}
        >
          🚀 Connect
        </button>
        <button 
          className="btn-secondary" 
          onClick={disconnectFromRoom} 
          disabled={!isConnected}
        >
          ⏹️ Disconnect
        </button>
        <button 
          className="btn-primary" 
          onClick={autoConnect} 
          disabled={isConnected || autoConnecting}
        >
          🔄 Reconnect
        </button>
      </div>

      <div className="status-display">
        <strong>Connection Status:</strong> {connectionState}
      </div>

      {isConnected && (
        <div className="participants-section">
          <h3>👥 Participants ({participants.length})</h3>
          <div className="participants-list">
            {participants.map((p) => (
              <div key={p.sid} className="participant">
                <span>{p.identity} {p.isLocal ? '(You)' : ''}</span>
                <span>{p.isMicrophoneEnabled ? '🎤' : '🔇'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {isConnected && (
        <div className="test-dashboard">
          <h3>🧪 AI Navigation Test Dashboard</h3>
          
          <div className="dashboard-controls">
            <div className="control-group">
              <label>
                <input
                  id="ai-navigation-toggle"
                  type="checkbox"
                  checked={aiNavigationMode}
                  onChange={(e) => {
                    setAiNavigationMode(e.target.checked);
                    addLog(`🖱️ User clicked: AI Navigation Mode toggle - ${e.target.checked ? 'ON' : 'OFF'}`);
                  }}
                />
                🤖 AI Navigation Mode
              </label>
            </div>

            <div className="control-group">
              <label>Test Command:</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  id="test-command-input"
                  type="text"
                  value={testCommand}
                  onChange={(e) => {
                    setTestCommand(e.target.value);
                    addLog(`📝 User typing in test command input: ${e.target.value}`);
                  }}
                  placeholder="Enter command to test..."
                  style={{ flex: 1 }}
                />
                <button 
                  className="btn-primary"
                  onClick={() => {
                    if (testCommand.trim()) {
                      sendTestCommand(roomRef.current, testCommand);
                      addLog(`🖱️ User clicked: Send button with command: ${testCommand}`);
                      setTestCommand('');
                    }
                  }}
                  disabled={!testCommand.trim()}
                >
                  📤 Send
                </button>
              </div>
            </div>

            <div className="demo-buttons">
              <h4>🎯 Demo Scenarios:</h4>
              <button 
                id="go-to-dashboard-btn"
                className="btn-primary"
                onClick={() => {
                  sendTestCommand(roomRef.current, 'navigate to dashboard');
                  addLog('🖱️ User clicked: Go to Dashboard button');
                }}
              >
                🏠 Go to Dashboard
              </button>
              <button 
                id="save-profile-btn"
                className="btn-primary"
                onClick={() => {
                  sendTestCommand(roomRef.current, 'save my profile');
                  addLog('🖱️ User clicked: Save Profile button');
                }}
              >
                💾 Save Profile
              </button>
              <button 
                id="send-screen-status-btn"
                className="btn-primary"
                onClick={() => {
                  sendScreenStatus(roomRef.current);
                  addLog('🖱️ User clicked: Send Screen Status button');
                }}
              >
                📊 Send Screen Status
              </button>
              <button 
                className="btn-secondary"
                onClick={async () => {
                  try {
                    const response = await fetch(`${SERVER_URL}/navigation/command`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        type: 'tool_log',
                        data: {
                          tool: 'TEST_TOOL',
                          action: 'test_action',
                          input: { test: 'input data' },
                          output: { test: 'output data' },
                          timestamp: Date.now() / 1000
                        }
                      })
                    });
                    if (response.ok) {
                      addLog('🧪 Test tool log sent to server');
                    } else {
                      addLog('❌ Failed to send test tool log');
                    }
                  } catch (error) {
                    addLog(`❌ Error sending test tool log: ${error.message}`);
                  }
                }}
              >
                🧪 Test Tool Log
              </button>
            </div>

            <div className="status-panel">
              <h4>📊 Live Status:</h4>
              <div id="live-status-box">
                <p><strong>Current Page:</strong> {currentPage}</p>
                <p><strong>AI Mode:</strong> {aiNavigationMode ? '🟢 Active' : '🔴 Inactive'}</p>
                <p><strong>Route:</strong> {window.location.pathname}</p>
                <p><strong>Connection:</strong> {connectionState}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="tools-log-section">
        <h3>🧰 AI Tools Log ({toolLogs.length} entries)</h3>
        <div className="logs" style={{borderColor:'#17a2b8'}}>
          {toolLogs.length === 0 ? (
            <div>No tool activity yet... (Check browser console for SSE messages)</div>
          ) : (
            toolLogs.map((log, i) => (
              <div key={i} style={{marginBottom: '10px', padding: '5px', border: '1px solid #ddd'}}>
                <strong>{new Date(log.timestamp * 1000).toLocaleTimeString()} — {log.tool} • {log.action}</strong>
                <pre style={{whiteSpace:'pre-wrap', fontSize: '12px'}}>{JSON.stringify(log.input, null, 2)}</pre>
                <pre style={{whiteSpace:'pre-wrap', background:'#f5fff5', fontSize: '12px'}}>{JSON.stringify(log.output, null, 2)}</pre>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="logs-section">
        <h3>📜 Connection Log</h3>
        <div className="logs">
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>

      <div ref={audioContainerRef} style={{ display: 'none' }} />
    </div>
  );
}

export default App;