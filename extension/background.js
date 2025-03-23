// Constants for API configuration
const API_CONFIG = {
  baseUrl: 'http://localhost:8080',
  maxRetries: 3,
  retryDelay: 1000,
  timeout: 30000
};

// Error types
const ErrorTypes = {
  NETWORK: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT_ERROR',
  API: 'API_ERROR',
  AUTH: 'AUTH_ERROR'
};

// Retry mechanism for API calls
async function retryableRequest(requestFn, options = {}) {
  const retries = options.retries || API_CONFIG.maxRetries;
  const delay = options.delay || API_CONFIG.retryDelay;
  
  let lastError;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await Promise.race([
        requestFn(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), API_CONFIG.timeout)
        )
      ]);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      lastError = error;
      console.error(`Request attempt ${attempt + 1} failed:`, error);
      
      if (attempt < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
      }
    }
  }
  
  throw new Error(`Failed after ${retries} attempts: ${lastError.message}`);
}

// API request wrapper with error handling
async function makeRequest(endpoint, options = {}) {
  const url = `${API_CONFIG.baseUrl}${endpoint}`;
  const requestOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-ID': chrome.runtime.id,
      'Origin': `chrome-extension://${chrome.runtime.id}`,
      ...options.headers
    },
    credentials: 'include',
    cache: 'no-cache'
  };
  
  try {
    return await retryableRequest(() => fetch(url, requestOptions));
  } catch (error) {
    const errorType = categorizeError(error);
    handleError(error, errorType);
    throw error;
  }
}

// Categorize errors
function categorizeError(error) {
  if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
    return ErrorTypes.NETWORK;
  }
  if (error.message.includes('timeout')) {
    return ErrorTypes.TIMEOUT;
  }
  if (error.message.includes('API error')) {
    return ErrorTypes.API;
  }
  return ErrorTypes.NETWORK;
}

// Handle errors
function handleError(error, type) {
  console.error(`[${type}] Error:`, error);
  
  // Notify any active popups
  chrome.runtime.sendMessage({
    type: 'error',
    error: {
      type,
      message: error.message
    }
  }).catch(() => {
    // Ignore errors from sending message (popup might not be open)
  });
}

// Check backend connection
async function checkBackendConnection() {
  try {
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const response = await makeRequest(`/api/extension/ping?t=${timestamp}`);
    return {
      connected: true,
      version: response.version
    };
  } catch (error) {
    console.error('Backend connection check failed:', error);
    return {
      connected: false,
      error: error.message
    };
  }
}

// Listen for messages from the webpage or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background script received message:', request);
  
  if (request.type === 'checkConnection') {
    checkBackendConnection()
      .then(result => {
        console.log('Backend connection check result:', result);
        sendResponse(result);
      })
      .catch(error => {
        console.error('Error checking backend connection:', error);
        sendResponse({
          connected: false,
          error: error.message || 'Connection check failed'
        });
      });
    return true; // Required for async sendResponse
  }
  
  if (request.action === 'generateSummary') {
    console.log('Generating summary for video:', request.videoData);
    
    // Determine which endpoint to use based on the platform
    let endpoint = '/api/summarize';
    if (request.videoData.platform === 'olympus') {
      endpoint = '/api/olympus/capture';
    } else if (request.videoData.platform === 'youtube') {
      endpoint = '/api/summarize/youtube';
    }
    
    // Prepare data for the API
    const apiData = {
      title: request.videoData.title || 'Unknown Video',
      url: request.videoData.src || '',
      videoId: request.videoData.videoId || '',
      platform: request.videoData.platform || 'unknown',
      options: {
        max_length: parseInt(request.options.length) || 150,
        min_length: 30,
        focus_key_points: request.options.focusKeyPoints || true,
        focus_details: request.options.focusDetails || false,
        format: request.options.format || 'paragraph'
      }
    };
    
    // Add platform-specific data
    if (request.videoData.platform === 'olympus' && request.videoData.transcript) {
      apiData.transcript = request.videoData.transcript;
    }
    
    // Make API request
    makeRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(apiData)
    })
      .then(result => {
        console.log('Summary generation result:', result);
        sendResponse({
          success: true,
          summary: result.summary || '',
          source: result.source || request.videoData.platform,
          metadata: result.metadata || {}
        });
      })
      .catch(error => {
        console.error('Error generating summary:', error);
        sendResponse({
          success: false,
          error: error.message || 'Failed to generate summary'
        });
      });
    
    return true; // Required for async sendResponse
  }
  
  if (request.action === "getCurrentVideo") {
    chrome.tabs.executeScript({
      code: `
        const videoElement = document.querySelector('video');
        if (videoElement) {
          const videoData = {
            src: videoElement.currentSrc,
            title: document.title,
            duration: videoElement.duration,
            currentTime: videoElement.currentTime
          };
          videoData;
        } else {
          null;
        }
      `
    }, (results) => {
      if (results && results[0]) {
        sendResponse({success: true, videoData: results[0]});
      } else {
        sendResponse({success: false, error: "No video found on page"});
      }
    });
    return true;
  }
});

// Handle installation/update
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    console.log('Extension installed');
    const status = await checkBackendConnection();
    console.log('Initial backend status:', status);
  }
});

// Export functions for testing (will only be used in Node.js/test environment)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    handleMessage,
    captureAudio,
    getCurrentVideo,
    sendMessageToCurrentTab
  };
}
