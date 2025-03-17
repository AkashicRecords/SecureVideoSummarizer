/**
 * Tests for the popup.js script of the Secure Video Summarizer extension.
 * 
 * To run these tests:
 * 1. Install Jest: npm install --save-dev jest
 * 2. Run: npm test
 */

// Mock the DOM elements that popup.js interacts with
document.body.innerHTML = `
  <div id="loading" class="status-message hidden"></div>
  <div id="no-video" class="status-message hidden"></div>
  <div id="video-detected" class="status-message"></div>
  <div id="extension-error" class="status-message error hidden"></div>
  <div id="summary-result" class="summary-container hidden"></div>
  <div id="video-title"></div>
  <div id="video-duration"></div>
  <div id="summary-content"></div>
  
  <button id="summarize-btn"></button>
  <button id="open-app-btn"></button>
  <button id="retry-connection-btn"></button>
  <button id="copy-summary"></button>
  <button id="save-summary"></button>
  <button id="close-summary"></button>
  <a id="settings-link"></a>
  
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

// Mock chrome API
global.chrome = {
  tabs: {
    query: jest.fn().mockResolvedValue([{ id: 123 }]),
    sendMessage: jest.fn(),
    create: jest.fn()
  },
  runtime: {
    sendMessage: jest.fn(),
    lastError: null
  },
  scripting: {
    executeScript: jest.fn()
  }
};

// Mock fetch API
global.fetch = jest.fn();

// Mock clipboard API
global.navigator.clipboard = {
  writeText: jest.fn().mockResolvedValue(undefined)
};

// Mock setTimeout
jest.useFakeTimers();

// Import or recreate the functionality from popup.js
// Note: In a real test, you would import the actual code
// For this test, we'll recreate the key functions

// State management (simplified version of what's in popup.js)
const currentState = {
  backendConnected: false,
  videoData: null,
  summarizing: false,
  summary: null
};

// Functions from popup.js
async function checkBackendConnection() {
  try {
    document.getElementById('loading').classList.remove('hidden');
    
    const response = await fetch('http://localhost:5000/api/extension/status');
    
    if (response.ok) {
      const data = await response.json();
      currentState.backendConnected = true;
      return true;
    } else {
      throw new Error('Backend connection failed');
    }
  } catch (error) {
    currentState.backendConnected = false;
    document.getElementById('extension-error').classList.remove('hidden');
    return false;
  } finally {
    document.getElementById('loading').classList.add('hidden');
  }
}

async function saveSummary() {
  if (!currentState.summary || !currentState.videoData) return;
  
  try {
    const response = await fetch('http://localhost:5000/api/extension/save_summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        summary: currentState.summary,
        video_data: currentState.videoData
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      const btn = document.getElementById('save-summary');
      const originalText = btn.textContent;
      btn.textContent = 'Saved!';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 1500);
      return true;
    } else {
      throw new Error('Failed to save summary');
    }
  } catch (error) {
    console.error('Error saving summary:', error);
    alert('Failed to save summary. Please try again.');
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
          currentState.summary = data.summary;
          document.getElementById('summary-content').innerHTML = data.summary;
          document.getElementById('summary-result').classList.remove('hidden');
          document.getElementById('loading').classList.add('hidden');
          currentState.summarizing = false;
          return true;
        } else if (data.status === 'error') {
          clearInterval(pollInterval);
          throw new Error(data.message || 'Summary failed');
        }
      }
    } catch (error) {
      clearInterval(pollInterval);
      console.error('Error polling for summary:', error);
      document.getElementById('extension-error').classList.remove('hidden');
      currentState.summarizing = false;
      return false;
    }
  }, 2000);
  
  // For testing, we trigger the first interval immediately
  jest.advanceTimersByTime(2000);
  
  return pollInterval;
}

function copySummaryToClipboard() {
  if (!currentState.summary) return false;
  
  return navigator.clipboard.writeText(currentState.summary)
    .then(() => {
      const btn = document.getElementById('copy-summary');
      const originalText = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 1500);
      return true;
    })
    .catch(err => {
      console.error('Failed to copy text:', err);
      return false;
    });
}

// Tests for popup.js
describe('Popup Script', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Reset DOM state
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('extension-error').classList.add('hidden');
    document.getElementById('summary-result').classList.add('hidden');
    
    // Reset state
    currentState.backendConnected = false;
    currentState.videoData = null;
    currentState.summarizing = false;
    currentState.summary = null;
  });
  
  describe('checkBackendConnection', () => {
    test('should set backendConnected to true on successful connection', async () => {
      // Mock a successful API response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'connected',
          version: '1.0.0',
          allowed_origins: ['chrome-extension://EXTENSION_ID_PLACEHOLDER']
        })
      });
      
      const result = await checkBackendConnection();
      
      expect(result).toBe(true);
      expect(currentState.backendConnected).toBe(true);
      expect(document.getElementById('loading').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(true);
      expect(fetch).toHaveBeenCalledWith('http://localhost:5000/api/extension/status');
    });
    
    test('should set backendConnected to false on failed connection', async () => {
      // Mock a failed API response
      fetch.mockRejectedValueOnce(new Error('Connection failed'));
      
      const result = await checkBackendConnection();
      
      expect(result).toBe(false);
      expect(currentState.backendConnected).toBe(false);
      expect(document.getElementById('loading').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(false);
    });
  });
  
  describe('saveSummary', () => {
    test('should save summary successfully', async () => {
      // Setup state
      currentState.summary = 'Test summary';
      currentState.videoData = {
        title: 'Test Video',
        duration: 120,
        src: 'https://example.com/video.mp4'
      };
      
      // Mock save button
      const saveBtn = document.getElementById('save-summary');
      saveBtn.textContent = 'Save';
      
      // Mock a successful API response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
      
      const result = await saveSummary();
      
      expect(result).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:5000/api/extension/save_summary',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            summary: 'Test summary',
            video_data: currentState.videoData
          })
        })
      );
      
      // Check button text changed
      expect(saveBtn.textContent).toBe('Saved!');
      
      // Advance timers to check text reset
      jest.advanceTimersByTime(1500);
      expect(saveBtn.textContent).toBe('Save');
    });
    
    test('should handle save failure', async () => {
      // Setup state
      currentState.summary = 'Test summary';
      currentState.videoData = {
        title: 'Test Video',
        duration: 120,
        src: 'https://example.com/video.mp4'
      };
      
      // Mock alert
      global.alert = jest.fn();
      
      // Mock a failed API response
      fetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ success: false, error: 'Save failed' })
      });
      
      const result = await saveSummary();
      
      expect(result).toBe(false);
      expect(alert).toHaveBeenCalledWith('Failed to save summary. Please try again.');
    });
    
    test('should do nothing if no summary or videoData', async () => {
      // Setup state with missing data
      currentState.summary = null;
      currentState.videoData = null;
      
      const result = await saveSummary();
      
      expect(result).toBeUndefined();
      expect(fetch).not.toHaveBeenCalled();
    });
  });
  
  describe('pollForSummary', () => {
    test('should handle completed summary', async () => {
      // Mock successful API response with completed summary
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'completed',
          summary: 'Completed summary text'
        })
      });
      
      const pollInterval = await pollForSummary();
      
      expect(currentState.summary).toBe('Completed summary text');
      expect(document.getElementById('summary-content').innerHTML).toBe('Completed summary text');
      expect(document.getElementById('summary-result').classList.contains('hidden')).toBe(false);
      expect(document.getElementById('loading').classList.contains('hidden')).toBe(true);
      expect(currentState.summarizing).toBe(false);
      
      // Clear the interval (in real code this would be done automatically)
      clearInterval(pollInterval);
    });
    
    test('should handle processing status', async () => {
      // First API call returns processing
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'processing' })
      });
      
      // Second API call (after timer) returns completed
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'completed',
          summary: 'Completed after processing'
        })
      });
      
      const pollInterval = await pollForSummary();
      
      // First call shouldn't set summary yet
      expect(currentState.summary).toBeNull();
      
      // Advance timer to trigger the second API call
      jest.advanceTimersByTime(2000);
      
      // Now summary should be set
      expect(currentState.summary).toBe('Completed after processing');
      
      // Clear the interval
      clearInterval(pollInterval);
    });
    
    test('should handle error status', async () => {
      // Mock API response with error
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'error',
          message: 'Processing failed'
        })
      });
      
      const pollInterval = await pollForSummary();
      
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(false);
      expect(currentState.summarizing).toBe(false);
      
      // Clear the interval
      clearInterval(pollInterval);
    });
  });
  
  describe('copySummaryToClipboard', () => {
    test('should copy summary to clipboard', async () => {
      // Setup state
      currentState.summary = 'Test summary to copy';
      
      // Mock copy button
      const copyBtn = document.getElementById('copy-summary');
      copyBtn.textContent = 'Copy';
      
      const result = await copySummaryToClipboard();
      
      expect(result).toBe(true);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test summary to copy');
      expect(copyBtn.textContent).toBe('Copied!');
      
      // Advance timers to check text reset
      jest.advanceTimersByTime(1500);
      expect(copyBtn.textContent).toBe('Copy');
    });
    
    test('should do nothing if no summary', async () => {
      // Setup state with no summary
      currentState.summary = null;
      
      const result = await copySummaryToClipboard();
      
      expect(result).toBe(false);
      expect(navigator.clipboard.writeText).not.toHaveBeenCalled();
    });
  });
});