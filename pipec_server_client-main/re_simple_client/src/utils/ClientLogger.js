/**
 * Client-side logging utility
 * Saves logs to the logs folder for debugging
 */

class ClientLogger {
  constructor() {
    this.logs = [];
    this.maxLogs = 1000;
    this.logFile = null;
    this.sessionId = this.generateSessionId();
    this.startTime = new Date();
  }

  generateSessionId() {
    return `client_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  formatTimestamp() {
    return new Date().toISOString();
  }

  log(level, message, data = null) {
    const logEntry = {
      timestamp: this.formatTimestamp(),
      level: level.toUpperCase(),
      message: message,
      data: data,
      sessionId: this.sessionId
    };

    // Add to memory
    this.logs.push(logEntry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output
    const consoleMessage = `[${logEntry.timestamp}] [${logEntry.level}] ${message}`;
    switch (level.toLowerCase()) {
      case 'error':
        console.error(consoleMessage, data);
        break;
      case 'warn':
        console.warn(consoleMessage, data);
        break;
      case 'debug':
        console.debug(consoleMessage, data);
        break;
      default:
        console.log(consoleMessage, data);
    }

    // Try to save to server logs folder
    this.saveToServer(logEntry);
  }

  info(message, data = null) {
    this.log('info', message, data);
  }

  warn(message, data = null) {
    this.log('warn', message, data);
  }

  error(message, data = null) {
    this.log('error', message, data);
  }

  debug(message, data = null) {
    this.log('debug', message, data);
  }

  async saveToServer(logEntry) {
    try {
      const serverUrl = process.env.REACT_APP_SERVER_URL || 'http://localhost:8004';
      const response = await fetch(`${serverUrl}/api/client-log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logEntry)
      });
      
      if (!response.ok) {
        console.warn('Failed to save client log to server');
      }
    } catch (error) {
      // Silently fail - don't want logging to break the app
      console.debug('Could not save client log to server:', error.message);
    }
  }

  getLogs() {
    return this.logs;
  }

  exportLogs() {
    return {
      sessionId: this.sessionId,
      startTime: this.startTime.toISOString(),
      endTime: new Date().toISOString(),
      totalLogs: this.logs.length,
      logs: this.logs
    };
  }

  clear() {
    this.logs = [];
  }
}

// Create singleton instance
const clientLogger = new ClientLogger();

export default clientLogger; 