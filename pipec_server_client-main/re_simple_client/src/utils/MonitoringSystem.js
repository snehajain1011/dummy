// Monitoring System - Three Core Tools Implementation
// StaticDataLoader, SmartActionExecutor, ConversationTracker

class MonitoringSystem {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.eventSource = null;
        this.isConnected = false;
        
        // State tracking
        this.staticDataSent = false;
        this.conversationLog = [];
        this.intentLog = [];
        this.toolStatus = {
            staticDataLoader: false,
            smartActionExecutor: false,
            conversationTracker: false
        };
        
        // Callbacks for UI updates
        this.callbacks = {};
        
        console.log('🔧 MonitoringSystem constructor called with serverUrl:', serverUrl);
    }

    async initialize() {
        console.log('🔄 Initializing monitoring system...');
        console.log('📍 Server URL:', this.serverUrl);
        
        try {
            await this.connectSSE();
            this.updateToolStatus('staticDataLoader', true);
            this.updateToolStatus('smartActionExecutor', true);
            this.updateToolStatus('conversationTracker', true);
            console.log('✅ Monitoring system initialized successfully');
            return true; // Return success
        } catch (error) {
            console.error('❌ Failed to initialize monitoring system:', error);
            return false; // Return failure
        }
    }

    connectSSE() {
        console.log('🔌 Attempting to connect to SSE...');
        console.log('📍 SSE URL:', `${this.serverUrl}/navigation/stream`);
        
        return new Promise((resolve, reject) => {
            try {
                this.eventSource = new EventSource(`${this.serverUrl}/navigation/stream`);
                
                this.eventSource.onopen = (event) => {
                    console.log('🔗 SSE connection opened:', event);
                    this.isConnected = true;
                    resolve();
                };
                
                this.eventSource.onmessage = (event) => {
                    console.log('📡 CLIENT SSE MESSAGE RECEIVED:', event.data);
                    console.log('📡 CLIENT SSE EVENT TYPE:', event.type);
                    console.log('📡 CLIENT SSE EVENT ORIGIN:', event.origin);
                    console.log('📡 CLIENT SSE EVENT LAST EVENT ID:', event.lastEventId);
                    
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📡 CLIENT SSE MESSAGE PARSED:', data);
                        console.log('📡 CLIENT SSE FULL JSON:', JSON.stringify(data, null, 2));
                        this.handleSSEMessage(data);
                    } catch (error) {
                        console.error('❌ Failed to parse SSE message:', error);
                        console.error('❌ Raw message data:', event.data);
                    }
                };
                
                this.eventSource.onerror = (error) => {
                    console.error('❌ SSE connection error:', error);
                    console.error('❌ SSE readyState:', this.eventSource.readyState);
                    this.isConnected = false;
                    
                    // Auto-reconnect logic
                    if (this.eventSource.readyState === EventSource.CLOSED) {
                        console.log('🔄 Attempting to reconnect SSE in 5 seconds...');
                        setTimeout(() => {
                            console.log('🔄 Reconnecting SSE...');
                            this.connectSSE();
                        }, 5000);
                    }
                };
                
                console.log('✅ SSE connection established for monitoring');
                
            } catch (error) {
                console.error('❌ Failed to create EventSource:', error);
                reject(error);
            }
        });
    }

    handleSSEMessage(data) {
        console.log('🔍 Processing SSE message type:', data.type);
        
        switch (data.type) {
            case 'static_data_ready':
                console.log('📦 Handling static_data_ready event');
                this.handleStaticDataReady(data);
                break;
            case 'ai_intent':
                console.log('🎯 Handling ai_intent event');
                this.handleAIIntent(data);
                break;
            case 'user_speech_text':
                console.log('👤 Handling user_speech_text event');
                this.handleUserSpeechText(data);
                break;
            case 'ai_speech_text':
                console.log('🤖 Handling ai_speech_text event');
                this.handleAISpeechText(data);
                break;
            case 'tool_log':
                console.log('🔧 Handling tool_log event');
                this.handleToolLog(data);
                break;
            case 'connection':
                console.log('🔗 Handling connection event');
                console.log('🔗 Connection status:', data.status);
                break;
            case 'keepalive':
                console.log('💓 Handling keepalive event');
                break;
            default:
                console.log('🔍 Unknown SSE message type:', data.type);
                console.log('🔍 Full message data:', data);
        }
    }

    async sendStaticData(componentData) {
        console.log('📤 CLIENT: About to send static component data...');
        console.log('📤 CLIENT: Component data:', componentData);
        console.log('📤 CLIENT: Component data JSON:', JSON.stringify(componentData, null, 2));
        console.log('📤 CLIENT: Target URL:', `${this.serverUrl}/ai/data`);
        
        try {
            const response = await fetch(`${this.serverUrl}/ai/data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'dashboard_data',
                    data: componentData
                })
            });
            
            console.log('📤 CLIENT: HTTP response status:', response.status);
            console.log('📤 CLIENT: HTTP response headers:', response.headers);
            
            if (response.ok) {
                const responseData = await response.json();
                console.log('📤 CLIENT: HTTP response data:', responseData);
                console.log('✅ CLIENT: Static data sent successfully');
                this.staticDataSent = true;
                this.updateToolStatus('staticDataLoader', true);
            } else {
                console.error('❌ CLIENT: Failed to send static data, status:', response.status);
                const errorText = await response.text();
                console.error('❌ CLIENT: Error response:', errorText);
            }
        } catch (error) {
            console.error('❌ CLIENT: Exception sending static data:', error);
        }
    }

    handleStaticDataReady(message) {
        console.log('📦 CLIENT: Processing static_data_ready message:', message);
        this.staticDataSent = true;
        this.updateToolStatus('staticDataLoader', true);
        
        if (this.callbacks.onStaticDataReady) {
            console.log('📦 CLIENT: Calling onStaticDataReady callback');
            this.callbacks.onStaticDataReady(message);
        }
    }

    handleAIIntent(message) {
        console.log('🎯 CLIENT: Processing ai_intent message:', message);
        this.intentLog.push({
            timestamp: new Date().toISOString(),
            action: message.action,
            text: message.text,
            confidence: message.confidence,
            rawData: message
        });
        
        if (this.callbacks.onIntentReceived) {
            console.log('🎯 CLIENT: Calling onIntentReceived callback');
            this.callbacks.onIntentReceived(message);
        }
    }

    handleUserSpeechText(message) {
        console.log('👤 CLIENT: Processing user_speech_text message:', message);
        this.conversationLog.push({
            timestamp: new Date().toISOString(),
            speaker: 'user',
            text: message.text,
            duration: message.duration,
            confidence: message.confidence
        });
        
        if (this.callbacks.onUserSpeech) {
            console.log('👤 CLIENT: Calling onUserSpeech callback');
            this.callbacks.onUserSpeech(message);
        }
    }

    handleAISpeechText(message) {
        console.log('🤖 CLIENT: Processing ai_speech_text message:', message);
        this.conversationLog.push({
            timestamp: new Date().toISOString(),
            speaker: 'ai',
            text: message.text,
            duration: message.duration,
            intent: message.intent
        });
        
        if (this.callbacks.onAISpeech) {
            console.log('🤖 CLIENT: Calling onAISpeech callback');
            this.callbacks.onAISpeech(message);
        }
    }

    handleToolLog(message) {
        console.log('🔧 CLIENT: Processing tool_log message:', message);
        // Handle tool logs if needed
    }

    updateToolStatus(tool, status) {
        console.log(`🔧 CLIENT: Updating tool status - ${tool}: ${status}`);
        this.toolStatus[tool] = status;
        
        if (this.callbacks.onToolStatusUpdate) {
            console.log(`🔧 CLIENT: Calling onToolStatusUpdate callback for ${tool}`);
            this.callbacks.onToolStatusUpdate(tool, status);
        }
    }

    disconnect() {
        console.log('🔌 CLIENT: Disconnecting monitoring system...');
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
        console.log('🔌 CLIENT: Monitoring system disconnected');
    }

    setCallbacks(callbacks) {
        console.log('🔧 CLIENT: Setting callbacks:', Object.keys(callbacks));
        this.callbacks = callbacks;
    }
}

export default MonitoringSystem; 