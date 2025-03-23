/**
 * Tests for the popup.js script of the Secure Video Summarizer extension.
 */

// Define global mock for currentState before requiring the module
global.currentState = {
  backendConnected: false,
  videoData: null,
  summarizing: false,
  summary: null,
  popupOpen: true
};

// Mock the DOM elements that popup.js interacts with
document.body.innerHTML = `
  <div id="loading" class="status-message hidden"></div>
  <div id="no-video" class="status-message hidden"></div>
  <div id="video-detected" class="status-message"></div>
  <div id="extension-error" class="status-message error hidden">
    <p>⚠️ There was an error connecting to the backend.</p>
    <p id="error-message-text">Please ensure the application is running.</p>
    <button id="retry-connection" class="btn">Retry Connection</button>
  </div>
  <div id="summary-result" class="summary-container hidden"></div>
  <div id="video-title"></div>
  <div id="video-duration"></div>
  <div id="video-warning" class="warning-text hidden"></div>
  <div id="video-info"></div>
  <div id="summary-content"></div>
  
  <div id="playback-controls" class="playback-controls">
    <button id="play-btn">Play</button>
    <button id="pause-btn">Pause</button>
    <button id="seek-back-btn">-10s</button>
    <button id="seek-forward-btn">+10s</button>
    <button id="decrease-rate-btn">-</button>
    <button id="increase-rate-btn">+</button>
    <span id="playback-rate">1.0x</span>
  </div>
  
  <button id="summarize-btn"></button>
  <button id="open-app-btn"></button>
  <button id="retry-connection" class="btn">Retry Connection</button>
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
    lastError: null,
    id: 'test-extension-id'
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

// Import the actual code
const popupModule = require('../popup.js');

// Extract functions from the module for testing
const {
  checkBackendConnection,
  showVideoDetected,
  showNoVideo,
  updateVideoInfo,
  saveSummary
} = popupModule;

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
    global.currentState.backendConnected = false;
    global.currentState.videoData = null;
    global.currentState.summarizing = false;
    global.currentState.summary = null;
  });
  
  describe('checkBackendConnection', () => {
    test('should set backendConnected to true on successful connection', async () => {
      // Mock a successful API response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          status: 'connected',
          version: '1.0.0'
        })
      });
      
      const result = await checkBackendConnection();
      
      expect(result).toBe(true);
      expect(global.currentState.backendConnected).toBe(true);
      expect(document.getElementById('loading').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('http://127.0.0.1:8080/api/extension/ping'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-Extension-ID': 'test-extension-id',
            'Origin': 'chrome-extension://test-extension-id'
          }),
          credentials: 'include',
          cache: 'no-cache'
        })
      );
    });
    
    test('should set backendConnected to false on failed connection', async () => {
      // Mock a failed API response
      fetch.mockRejectedValueOnce(new Error('Connection failed'));
      
      const result = await checkBackendConnection();
      
      expect(result).toBe(false);
      expect(global.currentState.backendConnected).toBe(false);
      expect(document.getElementById('loading').classList.contains('hidden')).toBe(true);
      expect(document.getElementById('extension-error').classList.contains('hidden')).toBe(false);
    });
  });
  
  describe('Video Controls', () => {
    test('should enable controls for standard video', () => {
      const videoData = {
        title: 'Test Video',
        duration: 120,
        src: 'https://example.com/video.mp4',
        inIframe: false,
        isVirtualVideo: false
      };
      
      updateVideoInfo(videoData);
      
      expect(document.getElementById('play-btn').disabled).toBe(false);
      expect(document.getElementById('pause-btn').disabled).toBe(false);
      expect(document.getElementById('seek-back-btn').disabled).toBe(false);
      expect(document.getElementById('seek-forward-btn').disabled).toBe(false);
      expect(document.getElementById('decrease-rate-btn').disabled).toBe(false);
      expect(document.getElementById('increase-rate-btn').disabled).toBe(false);
      expect(document.getElementById('video-warning').style.display).toBe('none');
    });
    
    test('should disable controls for iframe video', () => {
      const videoData = {
        title: 'Iframe Video',
        duration: 120,
        src: 'https://example.com/video.mp4',
        inIframe: true,
        isVirtualVideo: false
      };
      
      updateVideoInfo(videoData);
      
      expect(document.getElementById('play-btn').disabled).toBe(true);
      expect(document.getElementById('pause-btn').disabled).toBe(true);
      expect(document.getElementById('seek-back-btn').disabled).toBe(true);
      expect(document.getElementById('seek-forward-btn').disabled).toBe(true);
      expect(document.getElementById('decrease-rate-btn').disabled).toBe(true);
      expect(document.getElementById('increase-rate-btn').disabled).toBe(true);
      expect(document.getElementById('video-warning').style.display).toBe('block');
      expect(document.getElementById('video-warning').textContent).toContain('iframe');
    });
  });
  
  describe('saveSummary', () => {
    test('should save summary successfully', async () => {
      // Setup state
      global.currentState.summary = 'Test summary';
      global.currentState.videoData = {
        title: 'Test Video',
        duration: 120,
        src: 'https://example.com/video.mp4'
      };
      
      // Mock save button
      const saveBtn = document.getElementById('save-summary');
      saveBtn.textContent = 'Save Summary';
      
      // Mock a successful API response
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });
      
      await saveSummary();
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('http://127.0.0.1:8080/api/extension/save_summary'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Extension-ID': 'test-extension-id',
            'Origin': 'chrome-extension://test-extension-id'
          }),
          body: JSON.stringify({
            summary: 'Test summary',
            video_data: global.currentState.videoData
          })
        })
      );
      
      // Check button text changed
      expect(saveBtn.textContent).toBe('Saved!');
      
      // Advance timers to check text reset
      jest.advanceTimersByTime(2000);
      expect(saveBtn.textContent).toBe('Save Summary');
    });
  });
  
  describe('showVideoDetected', () => {
    test('should show video detected UI and enable controls', () => {
      showVideoDetected(true);
      
      expect(document.getElementById('no-video').style.display).toBe('none');
      expect(document.getElementById('video-detected').style.display).toBe('block');
      expect(document.getElementById('playback-controls').style.display).toBe('flex');
      expect(document.getElementById('summarize-btn').disabled).toBe(!global.currentState.backendConnected);
    });
    
    test('should show no video UI and disable controls', () => {
      showVideoDetected(false);
      
      expect(document.getElementById('no-video').style.display).toBe('block');
      expect(document.getElementById('video-detected').style.display).toBe('none');
      expect(document.getElementById('playback-controls').style.display).toBe('none');
      expect(document.getElementById('summarize-btn').disabled).toBe(true);
    });
  });
});
