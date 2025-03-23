/**
 * SVS Extension Logger
 * Provides consistent, configurable logging for both extension and content script
 */

// Log levels
const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
};

// Default configuration
const config = {
  level: LogLevel.INFO,         // Current log level
  debugMode: false,             // Enable extra verbose debugging
  prefix: '[SVS]',              // Prefix for all log messages
  useColors: true,              // Use colored console output
  logToStorage: true,           // Save logs to local storage
  maxStoredLogs: 100,           // Maximum number of logs to store
  contentScriptId: null,        // ID for the content script (auto-generated)
  errorHandler: null            // Optional custom error handler
};

// Colors for different log types
const colors = {
  debug: '#8a8a8a',
  info: '#0066cc',
  warn: '#ff9900',
  error: '#cc0000',
  success: '#00aa00',
  focus: '#9900cc',
  dim: '#666666'
};

// Storage key for logs
const LOGS_STORAGE_KEY = 'svs_extension_logs';

/**
 * Initialize the logger with custom settings
 * @param {Object} options - Configuration options
 */
function init(options = {}) {
  Object.assign(config, options);
  
  // Generate a unique ID for content script instances
  if (options.isContentScript && !config.contentScriptId) {
    config.contentScriptId = generateId();
    log('debug', `Content script initialized with ID: ${config.contentScriptId}`);
  }
  
  // Set up global error handling
  if (config.debugMode) {
    setupGlobalErrorHandling();
  }
  
  // Clear old logs on startup if we're the background script
  if (options.isBackground && config.logToStorage) {
    clearOldLogs();
  }
}

/**
 * Generate a simple unique ID
 * @returns {string} A unique identifier
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

/**
 * Generic logging function
 * @param {string} level - Log level (debug, info, warn, error)
 * @param {...any} args - Data to log
 */
function log(level, ...args) {
  // Skip if log level is below configured threshold
  if (LogLevel[level.toUpperCase()] < config.level) {
    return;
  }
  
  const timestamp = new Date().toISOString();
  let prefix = config.prefix;
  
  // Add content script ID if applicable
  if (config.contentScriptId) {
    prefix += ` [Content-${config.contentScriptId.substr(0, 4)}]`;
  }
  
  // Format the message
  const message = args.map(arg => {
    if (typeof arg === 'object') {
      try {
        return JSON.stringify(arg);
      } catch (e) {
        return arg.toString();
      }
    }
    return arg;
  }).join(' ');
  
  // Output to console with appropriate styling
  if (config.useColors) {
    const color = colors[level] || colors.info;
    console[level === 'debug' ? 'log' : level](
      `%c${prefix}%c ${timestamp} %c${level.toUpperCase()}%c ${message}`,
      `color:${colors.focus}; font-weight:bold;`,
      `color:${colors.dim};`,
      `color:${color}; font-weight:bold;`,
      'color:inherit;'
    );
  } else {
    console[level === 'debug' ? 'log' : level](`${prefix} ${level.toUpperCase()} ${message}`);
  }
  
  // Store in local storage if enabled
  if (config.logToStorage) {
    storeLog({
      timestamp,
      level,
      message,
      source: config.contentScriptId ? 'content' : 'extension'
    });
  }
  
  // Call custom error handler for errors if provided
  if (level === 'error' && config.errorHandler) {
    config.errorHandler(message, args);
  }
}

/**
 * Store a log entry in extension storage
 * @param {Object} logEntry - The log entry to store
 */
function storeLog(logEntry) {
  chrome.storage.local.get([LOGS_STORAGE_KEY], (result) => {
    const logs = result[LOGS_STORAGE_KEY] || [];
    logs.push(logEntry);
    
    // Keep only the most recent logs
    while (logs.length > config.maxStoredLogs) {
      logs.shift();
    }
    
    chrome.storage.local.set({ [LOGS_STORAGE_KEY]: logs });
    
    // If we have accumulated 25 logs, send them to the dashboard
    if (logs.length % 25 === 0) {
      sendLogsToDashboard(logs);
    }
  });
}

/**
 * Clear logs older than a certain threshold
 */
function clearOldLogs() {
  // Keep only logs from the last 24 hours
  chrome.storage.local.get([LOGS_STORAGE_KEY], (result) => {
    const logs = result[LOGS_STORAGE_KEY] || [];
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const filteredLogs = logs.filter(log => {
      return new Date(log.timestamp) > oneDayAgo;
    });
    
    if (filteredLogs.length < logs.length) {
      chrome.storage.local.set({ [LOGS_STORAGE_KEY]: filteredLogs });
      log('debug', `Cleared ${logs.length - filteredLogs.length} old log entries`);
    }
  });
}

/**
 * Set up global error handling
 */
function setupGlobalErrorHandling() {
  // Handle uncaught exceptions
  window.addEventListener('error', (event) => {
    const { message, filename, lineno, colno, error } = event;
    log('error', `Uncaught exception: ${message} at ${filename}:${lineno}:${colno}`, error?.stack || '');
    
    // Don't prevent default error handling
    return false;
  });
  
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    log('error', `Unhandled promise rejection: ${event.reason}`, event.reason?.stack || '');
    
    // Don't prevent default rejection handling
    return false;
  });
  
  // Patch XMLHttpRequest to log errors
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function(...args) {
    this.addEventListener('error', (e) => {
      log('error', `XHR request failed: ${this.responseURL}`, e);
    });
    this.addEventListener('load', () => {
      if (this.status >= 400) {
        log('error', `XHR request failed with status ${this.status}: ${this.responseURL}`, this.responseText);
      } else if (config.debugMode) {
        log('debug', `XHR request succeeded: ${this.responseURL}`);
      }
    });
    return originalSend.apply(this, args);
  };
  
  log('debug', 'Global error handling initialized');
}

/**
 * Get all stored logs
 * @param {Function} callback - Callback function to receive logs
 */
function getLogs(callback) {
  chrome.storage.local.get([LOGS_STORAGE_KEY], (result) => {
    callback(result[LOGS_STORAGE_KEY] || []);
  });
}

/**
 * Set the current log level
 * @param {string|number} level - New log level
 */
function setLogLevel(level) {
  if (typeof level === 'string') {
    level = LogLevel[level.toUpperCase()];
  }
  if (typeof level === 'number' && level >= LogLevel.DEBUG && level <= LogLevel.NONE) {
    config.level = level;
    log('info', `Log level set to ${Object.keys(LogLevel)[level]}`);
  }
}

/**
 * Enable or disable debug mode
 * @param {boolean} enabled - Whether debug mode should be enabled
 */
function setDebugMode(enabled) {
  config.debugMode = !!enabled;
  if (enabled) {
    config.level = LogLevel.DEBUG;
    log('info', 'Debug mode enabled');
    setupGlobalErrorHandling();
  } else {
    log('info', 'Debug mode disabled');
  }
}

// Convenience methods for different log levels
const debug = (...args) => log('debug', ...args);
const info = (...args) => log('info', ...args);
const warn = (...args) => log('warn', ...args);
const error = (...args) => log('error', ...args);
const success = (...args) => log('success', ...args);

// Add a function to send logs to the dashboard
function sendLogsToDashboard(logs) {
  if (!logs || logs.length === 0) return;
  
  // Get the dashboard URL from config or use default
  const backendUrl = getBackendUrl();
  const url = `${backendUrl}/api/admin/extension/logs`;
  
  // Prepare the log data
  const logData = {
    browser: 'chrome',
    url: window.location.href,
    timestamp: new Date().toISOString(),
    content: {
      logs: logs.slice(-50), // Send the last 50 logs
      userAgent: navigator.userAgent,
      videoState: window.lastVideoState || null
    }
  };
  
  // Send the logs to the dashboard
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-ID': chrome.runtime.id
    },
    body: JSON.stringify(logData)
  }).catch(error => {
    console.error('Failed to send logs to dashboard:', error);
  });
}

// Get backend URL from config or use default
function getBackendUrl() {
  // Try to get from config
  try {
    if (typeof config !== 'undefined' && config.apiUrl) {
      return config.apiUrl;
    }
  } catch (e) {
    // Ignore
  }
  
  // Default to localhost
  return 'http://localhost:8080';
}

// Export the logger API
export default {
  LogLevel,
  init,
  debug,
  info,
  warn,
  error,
  success,
  setLogLevel,
  setDebugMode,
  getLogs
}; 