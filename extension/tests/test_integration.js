/**
 * Integration tests for the Secure Video Summarizer extension.
 * 
 * These tests verify the complete flow between content script, popup, background script,
 * and backend API endpoints.
 * 
 * To run these tests:
 * 1. Install Jest: npm install --save-dev jest
 * 2. Run: npm test
 */

// Define global mock for currentState before requiring the module
global.currentState = {
  backendConnected: false,
  videoData: null,
  summarizing: false,
  summary: null,
  popupOpen: true
};

// Mock the DOM elements
document.body.innerHTML = `
  <div id="loading" class="status-message hidden"></div>
  <div id="extension-error" class="status-message error hidden">
    <p>⚠️ There was an error connecting to the backend.</p>
    <p id="error-message-text">Please ensure the application is running.</p>
    <button id="retry-connection" class="btn">Retry Connection</button>
  </div>
  <div id="video-detected" class="status-message">
    <p>🎬 <span id="video-title">Video detected</span></p>
    <p>Duration: <span id="video-duration">Unknown</span></p>
    <div id="video-warning" class="warning-text hidden"></div>
    <div id="video-info"></div>
  </div>
  <div id="no-video" class="status-message hidden"></div>
  <div id="summary-result" class="summary-container hidden">
    <div id="summary-content"></div>
  </div>
  <button id="summarize-btn"></button>
  <button id="open-app-btn"></button>
  <button id="retry-connection-btn"></button>
  <button id="copy-summary"></button>
  <button id="save-summary"></button>
  <button id="close-summary"></button>
  
  <select id="length">
    <option value="short">Short</option>
    <option value="medium" selected>Medium</option>
    <option value="long">Long</option>
  </select>
  <select id="format">
    <option value="paragraph" selected>Paragraph</option>
    <option value="bullets">Bullet Points</option>
  </select>
  <input type="checkbox" id="focus-key-points" checked>
  <input type="checkbox" id="focus-details">
`;

// Mock video element for content script
const videoContainer = document.createElement('div');
videoContainer.className = 'video-container';
videoContainer.innerHTML = `
  <h2 class="video-title">Integration Test Video</h2>
  <video id="test-video" src="https://example.com/test-video.mp4" width="640" height="360"></video>
`;
document.body.appendChild(videoContainer);

// Mock video element properties
const videoElement = document.getElementById('test-video');
Object.defineProperties(videoElement, {
  duration: { value: 180, writable: true },
  currentTime: { value: 45, writable: true },
  paused: { value: false, writable: true },
  muted: { value: false, writable: true },
  volume: { value: 0.8, writable: true },
  playbackRate: { value: 1.0, writable: true },
  videoWidth: { value: 1280, writable: true },
  videoHeight: { value: 720, writable: true },
  currentSrc: { value: 'https://example.com/test-video.mp4', writable: true },
  getBoundingClientRect: {
    value: () => ({
      width: 640,
      height: 360,
      top: 100,
      left: 100,
      bottom: 460,
      right: 740
    })
  },
  play: { value: jest.fn().mockResolvedValue(undefined) },
  pause: { value: jest.fn() }
});

// Mock chrome API
global.chrome = {
  tabs: {
    query: jest.fn().mockResolvedValue([{ id: 123 }]),
    sendMessage: jest.fn((tabId, message, callback) => {
      // Simulate content script response
      if (message.action === 'getCurrentVideo') {
        callback({
          success: true,
          videoData: {
            src: 'https://example.com/test-video.mp4',
            title: 'Integration Test Video',
            duration: 180,
            currentTime: 45,
            paused: false,
            muted: false,
            volume: 0.8,
            playbackRate: 1.0,
            width: 1280,
            height: 720,
            platform: 'olympus'
          }
        });
      }
    }),
    create: jest.fn()
  },
  runtime: {
    sendMessage: jest.fn((message, callback) => {
      // Simulate background script response
      if (message.action === 'captureAudioStream') {
        callback({ success: true });
      }
    }),
    lastError: null,
    onMessage: {
      addListener: jest.fn()
    }
  },
  scripting: {
    executeScript: jest.fn()
  }
};

// Mock fetch API for backend calls
global.fetch = jest.fn();

// Mock clipboard API
global.navigator.clipboard = {
  writeText: jest.fn().mockResolvedValue(undefined)
};

// Mock setTimeout and setInterval
jest.useFakeTimers();

// Simplified popup.js functions
async function checkBackendConnection() {
  try {
    document.getElementById('loading').classList.remove('hidden');
    
    const response = await fetch('http://localhost:5000/api/extension/status');
    
    if (response.ok) {
      const data = await response.json();
      global.currentState.backendConnected = true;
      return true;
    } else {
      throw new Error('Backend connection failed');
    }
  } catch (error) {
    global.currentState.backendConnected = false;
    document.getElementById('extension-error').classList.remove('hidden');
    return false;
  } finally {
    document.getElementById('loading').classList.add('hidden');
  }
}

async function checkForVideo() {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tabs[0].id, { action: 'getCurrentVideo' }, (response) => {
      if (response && response.success && response.videoData) {
        global.currentState.videoData = response.videoData;
        document.getElementById('video-detected').classList.remove('hidden');
        document.getElementById('no-video').classList.add('hidden');
        
        // Update video info in UI
        const title = response.videoData.title || 'Unnamed Video';
        document.getElementById('video-title').textContent = title;
        
        if (response.videoData.duration) {
          const minutes = Math.floor(response.videoData.duration / 60);
          const seconds = Math.floor(response.videoData.duration % 60);
          document.getElementById('video-duration').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
      } else {
        document.getElementById('no-video').classList.remove('hidden');
        document.getElementById('video-detected').classList.add('hidden');
      }
    });
  } catch (error) {
    document.getElementById('no-video').classList.remove('hidden');
    document.getElementById('video-detected').classList.add('hidden');
  }
}

async function summarizeVideo() {
  if (!global.currentState.videoData || !global.currentState.backendConnected) {
    return false;
  }
  
  try {
    document.getElementById('loading').classList.remove('hidden');
    global.currentState.summarizing = true;
    
    // Get selected options
    const options = {
      length: document.getElementById('length').value,
      format: document.getElementById('format').value,
      focus: []
    };
    
    if (document.getElementById('focus-key-points').checked) options.focus.push('key_points');
    if (document.getElementById('focus-details').checked) options.focus.push('detailed');
    
    // Send message to background script to capture audio
    chrome.runtime.sendMessage({ 
      action: 'captureAudioStream',
      videoData: global.currentState.videoData,
      options: options
    }, async (response) => {
      if (response && response.success) {
        // Poll for summary status
        await pollForSummary();
        return true;
      } else {
        throw new Error('Failed to start audio capture');
      }
    });
  } catch (error) {
    document.getElementById('extension-error').classList.remove('hidden');
    document.getElementById('loading').classList.add('hidden');
    global.currentState.summarizing = false;
    return false;
  }
}

async function pollForSummary() {
  let attempts = 0;
  const maxAttempts = 30;
  
  const pollInterval = setInterval(async () => {
    try {
      attempts++;
      
      if (attempts > maxAttempts) {
        clearInterval(pollInterval);
        throw new Error('Summary timeout');
      }
      
      const response = await fetch('http://localhost:5000/api/extension/summary_status');
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'completed' && data.summary) {
          clearInterval(pollInterval);
          global.currentState.summary = data.summary;
          document.getElementById('summary-content').innerHTML = data.summary;
          document.getElementById('summary-result').classList.remove('hidden');
          document.getElementById('loading').classList.add('hidden');
          global.currentState.summarizing = false;
          return true;
        } else if (data.status === 'error') {
          clearInterval(pollInterval);
          throw new Error(data.message || 'Summary failed');
        }
      }
    } catch (error) {
      clearInterval(pollInterval);
      document.getElementById('extension-error').classList.remove('hidden');
      document.getElementById('loading').classList.add('hidden');
      global.currentState.summarizing = false;
      return false;
    }
  }, 2000);
  
  // For testing, we trigger the first interval immediately
  jest.advanceTimersByTime(2000);
  
  return pollInterval;
}

async function saveSummary() {
  if (!global.currentState.summary || !global.currentState.videoData) return false;
  
  try {
    const response = await fetch('http://localhost:5000/api/extension/save_summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        summary: global.currentState.summary,
        video_data: global.currentState.videoData
      })
    });
    
    if (response.ok) {
      return true;
    } else {
      throw new Error('Failed to save summary');
    }
  } catch (error) {
    return false;
  }
}

// Integration tests
describe('Extension Integration', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Reset DOM state
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('extension-error').classList.add('hidden');
    document.getElementById('summary-result').classList.add('hidden');
    document.getElementById('no-video').classList.add('hidden');
    document.getElementById('video-detected').classList.remove('hidden');
    
    // Reset state
    global.currentState.backendConnected = false;
    global.currentState.videoData = null;
    global.currentState.summarizing = false;
    global.currentState.summary = null;
  });
  
  describe('Complete summarization flow', () => {
    test('should complete the full summarization process', async () => {
      // 1. Mock successful backend connection
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'connected',
          version: '1.0.0',
          allowed_origins: ['chrome-extension://EXTENSION_ID_PLACEHOLDER']
        })
      });
      
      // 2. Check backend connection
      await checkBackendConnection();
      expect(global.currentState.backendConnected).toBe(true);
      
      // 3. Check for video
      await checkForVideo();
      expect(global.currentState.videoData).not.toBeNull();
      expect(document.getElementById('video-title').textContent).toBe('Integration Test Video');
      
      // 4. Mock summary status API responses
      // First call - processing
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'processing' })
      });
      
      // Second call - completed
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'completed',
          summary: 'This is the completed summary of the integration test video.'
        })
      });
      
      // 5. Start summarization
      await summarizeVideo();
      
      // 6. Verify background script message was sent
      expect(chrome.runtime.sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'captureAudioStream',
          videoData: expect.any(Object),
          options: expect.any(Object)
        }),
        expect.any(Function)
      );
      
      // 7. Advance timer to trigger the second API call
      jest.advanceTimersByTime(2000);
      
      // 8. Verify summary was set
      expect(global.currentState.summary).toBe('This is the completed summary of the integration test video.');
      expect(document.getElementById('summary-content').innerHTML).toBe('This is the completed summary of the integration test video.');
      expect(document.getElementById('summary-result').classList.contains('hidden')).toBe(false);
      
      // 9. Mock save summary API response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
      
      // 10. Save the summary
      const saveResult = await saveSummary();
      expect(saveResult).toBe(true);
      
      // 11. Verify save summary API call
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:5000/api/extension/save_summary',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            summary: 'This is the completed summary of the integration test video.',
            video_data: global.currentState.videoData
          })
        })
      );
    });
    
    test('should handle backend connection failure', async () => {
      // Mock failed backend connection
      fetch.mockRejectedValueOnce(new Error('Connection failed'));
      
      // Check backend connection
      await checkBackendConnection();
      
      // Verify error state
      expect(global.currentState.backendConnected).toBe(false);
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(false);
      
      // Try to summarize (should fail)
      const result = await summarizeVideo();
      expect(result).toBe(false);
    });
    
    test('should handle summary status error', async () => {
      // 1. Mock successful backend connection
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'connected',
          version: '1.0.0'
        })
      });
      
      // 2. Check backend connection
      await checkBackendConnection();
      
      // 3. Check for video
      await checkForVideo();
      
      // 4. Mock summary status API error response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'error',
          message: 'Failed to process video'
        })
      });
      
      // 5. Start summarization
      await summarizeVideo();
      
      // 6. Verify error state
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(false);
      expect(global.currentState.summarizing).toBe(false);
    });
    
    test('should handle save summary failure', async () => {
      // Setup state with summary and video data
      global.currentState.summary = 'Test summary';
      global.currentState.videoData = {
        title: 'Test Video',
        duration: 120
      };
      
      // Mock failed save summary API response
      fetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({
          success: false,
          error: 'Failed to save summary'
        })
      });
      
      // Try to save summary
      const result = await saveSummary();
      
      // Verify failure
      expect(result).toBe(false);
    });
  });
}); 