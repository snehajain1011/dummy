import React from 'react';

// Tool Status Panel Component
export const ToolStatusPanel = ({ toolStatus }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
      case 'connected':
      case 'completed':
        return '#10b981'; // green
      case 'processing':
        return '#f59e0b'; // yellow
      case 'error':
        return '#ef4444'; // red
      case 'inactive':
      case 'disconnected':
        return '#6b7280'; // gray
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
      case 'connected':
        return '🟢';
      case 'processing':
        return '🟡';
      case 'completed':
        return '✅';
      case 'error':
        return '🔴';
      case 'inactive':
      case 'disconnected':
        return '⚪';
      default:
        return '⚪';
    }
  };

  return (
    <div className="tool-status-panel">
      <h3>🛠️ Tool Status</h3>
      <div className="tool-grid">
        <div className="tool-item">
          <span className="tool-icon">📦</span>
          <span className="tool-name">Static Data Loader</span>
          <span 
            className="tool-status"
            style={{ color: getStatusColor(toolStatus.staticDataLoader) }}
          >
            {getStatusIcon(toolStatus.staticDataLoader)} {toolStatus.staticDataLoader}
          </span>
        </div>
        
        <div className="tool-item">
          <span className="tool-icon">🎯</span>
          <span className="tool-name">Smart Action Executor</span>
          <span 
            className="tool-status"
            style={{ color: getStatusColor(toolStatus.smartActionExecutor) }}
          >
            {getStatusIcon(toolStatus.smartActionExecutor)} {toolStatus.smartActionExecutor}
          </span>
        </div>
        
        <div className="tool-item">
          <span className="tool-icon">💬</span>
          <span className="tool-name">Conversation Tracker</span>
          <span 
            className="tool-status"
            style={{ color: getStatusColor(toolStatus.conversationTracker) }}
          >
            {getStatusIcon(toolStatus.conversationTracker)} {toolStatus.conversationTracker}
          </span>
        </div>
      </div>
    </div>
  );
};

// Conversation Log Component
export const ConversationLog = ({ conversationLog }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getSpeakerIcon = (speaker) => {
    return speaker === 'user' ? '👤' : '🤖';
  };

  const getSpeakerClass = (speaker) => {
    return speaker === 'user' ? 'user-message' : 'ai-message';
  };

  return (
    <div className="conversation-log">
      <h3>💬 Conversation Log</h3>
      <div className="conversation-container">
        {conversationLog.length === 0 ? (
          <div className="no-messages">
            <p>No conversation yet. Start talking to see the log!</p>
          </div>
        ) : (
          conversationLog.map((entry, index) => (
            <div 
              key={index} 
              className={`conversation-entry ${getSpeakerClass(entry.speaker)}`}
            >
              <div className="message-header">
                <span className="speaker-icon">{getSpeakerIcon(entry.speaker)}</span>
                <span className="speaker-name">
                  {entry.speaker === 'user' ? 'You' : 'AI Assistant'}
                </span>
                <span className="message-time">{formatTime(entry.timestamp)}</span>
              </div>
              <div className="message-text">{entry.text}</div>
              {entry.duration && (
                <div className="message-meta">
                  Duration: {entry.duration}ms
                </div>
              )}
              {entry.confidence && (
                <div className="message-meta">
                  Confidence: {(entry.confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Intent Display Component
export const IntentDisplay = ({ intentLog }) => {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatJSON = (data) => {
    try {
      return JSON.stringify(data, null, 2);
    } catch (error) {
      return 'Invalid JSON';
    }
  };

  return (
    <div className="intent-display">
      <h3>🎯 AI Intent Log</h3>
      <div className="intent-container">
        {intentLog.length === 0 ? (
          <div className="no-intents">
            <p>No AI intents yet. AI will show intents when actions are needed.</p>
          </div>
        ) : (
          intentLog.map((intent, index) => (
            <div key={index} className="intent-entry">
              <div className="intent-header">
                <span className="intent-time">{formatTime(intent.timestamp)}</span>
                <span className="intent-type">{intent.actionType}</span>
                <span className="intent-confidence">
                  {(intent.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="intent-text">{intent.text}</div>
              <div className="intent-hash">Hash: {intent.intent}</div>
              <details className="intent-details">
                <summary>Raw JSON Data</summary>
                <pre className="intent-json">
                  {formatJSON(intent.rawData)}
                </pre>
              </details>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Static Data Status Component
export const StaticDataStatus = ({ staticDataStatus }) => {
  if (!staticDataStatus) {
    return null;
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="static-data-status">
      <h3>📦 Static Data Status</h3>
      <div className="status-info">
        <div className="status-item">
          <span className="status-label">Status:</span>
          <span className={`status-value ${staticDataStatus.status}`}>
            {staticDataStatus.status === 'sent' ? '✅ Sent' : 
             staticDataStatus.status === 'confirmed' ? '✅ Confirmed' : '❌ Error'}
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">Time:</span>
          <span className="status-value">{formatTime(staticDataStatus.timestamp)}</span>
        </div>
        {staticDataStatus.data && (
          <details className="data-details">
            <summary>Component Data</summary>
            <pre className="data-json">
              {JSON.stringify(staticDataStatus.data, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
};

// Main Monitoring Dashboard Component
export const MonitoringDashboard = ({ 
  toolStatus, 
  conversationLog, 
  intentLog, 
  staticDataStatus 
}) => {
  return (
    <div className="monitoring-dashboard">
      <h2>📊 Monitoring Dashboard</h2>
      
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <ToolStatusPanel toolStatus={toolStatus} />
        </div>
        
        <div className="dashboard-section">
          <StaticDataStatus staticDataStatus={staticDataStatus} />
        </div>
        
        <div className="dashboard-section full-width">
          <ConversationLog conversationLog={conversationLog} />
        </div>
        
        <div className="dashboard-section full-width">
          <IntentDisplay intentLog={intentLog} />
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard; 