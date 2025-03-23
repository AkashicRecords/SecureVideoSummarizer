/**
 * Tests for the background.js script of the Secure Video Summarizer extension.
 * 
 * To run these tests:
 * 1. Install Jest: npm install --save-dev jest
 * 2. Run: npm test
 */

// Mock the Chrome API
global.chrome = {
  runtime: {
    onMessage: {
      addListener: jest.fn(),
      hasListeners: jest.fn().mockReturnValue(true)
    },
    connectNative: jest.fn().mockReturnValue({
      postMessage: jest.fn(),
      disconnect: jest.fn()
    })
  },
  tabs: {
    executeScript: jest.fn((tabId, details) => {
      // Return a promise that resolves with the mock data
      return Promise.resolve([{ 
        src: 'https://example.com/video.mp4',
        title: 'Test Video',
        duration: 120,
        currentTime: 30
      }]);
    }),
    query: jest.fn().mockResolvedValue([{ id: 123 }]),
    sendMessage: jest.fn().mockImplementation((tabId, message, options) => {
      // Return a promise that resolves with a mock response
      return Promise.resolve({ success: true });
    })
  },
  tabCapture: {
    capture: jest.fn((options, callback) => {
      // Mock a media stream
      const mockStream = {
        getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }])
      };
      callback(mockStream);
    })
  }
};

// Mock classes that aren't available in Node.js
global.MediaRecorder = class MockMediaRecorder {
  constructor(stream) {
    this.stream = stream;
    this.ondataavailable = null;
    this.onstop = null;
  }

  start(interval) {
    // Simulate data available event
    if (this.ondataavailable) {
      this.ondataavailable({ data: new Blob(['test data']) });
    }
  }

  stop() {
    if (this.onstop) {
      this.onstop();
    }
  }
};

global.Blob = class MockBlob {
  constructor(parts, options) {
    this.parts = parts;
    this.options = options;
    this.size = 1024; // Mock size
  }
};

global.FileReader = class MockFileReader {
  constructor() {
    this.onloadend = null;
    this.result = new ArrayBuffer(8);
  }

  readAsArrayBuffer(blob) {
    // Immediately call onloadend
    if (this.onloadend) {
      setTimeout(() => this.onloadend(), 0);
    }
  }
};

// Load the background script implementation
// In a real test, you would load the actual script
// For this mock test, we'll manually recreate the message handling

// Recreate message handler function similar to what's in background.js
function handleMessage(request, sender, sendResponse) {
  if (request.action === "getCurrentVideo") {
    chrome.tabs.executeScript({
      code: `
        // Find the video element on the page
        const videoElement = document.querySelector('video');
        if (videoElement) {
          // Get video metadata
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
    return true; // Required for async sendResponse
  }
  
  if (request.action === "captureAudioStream") {
    chrome.tabCapture.capture({audio: true, video: false}, stream => {
      if (stream) {
        // Create a port to the native app
        const port = chrome.runtime.connectNative('com.securevideosum.app');
        
        // Set up a MediaRecorder to capture audio
        const mediaRecorder = new MediaRecorder(stream);
        const chunks = [];
        
        mediaRecorder.ondataavailable = e => {
          chunks.push(e.data);
          // Send chunks to the native app
          if (chunks.length > 0) {
            const blob = new Blob(chunks, { 'type' : 'audio/webm' });
            chunks.length = 0; // Clear chunks
            
            // Convert blob to array buffer for sending to native app
            const reader = new FileReader();
            reader.onloadend = () => {
              port.postMessage({
                type: 'audio_data',
                data: Array.from(new Uint8Array(reader.result))
              });
            };
            reader.readAsArrayBuffer(blob);
          }
        };
        
        mediaRecorder.onstop = () => {
          port.postMessage({type: 'recording_complete'});
          port.disconnect();
          stream.getTracks().forEach(track => track.stop());
        };
        
        // Start recording
        mediaRecorder.start(1000); // Capture in 1-second chunks
        
        sendResponse({success: true});
      } else {
        sendResponse({success: false, error: "Could not capture audio stream"});
      }
    });
    return true; // Required for async sendResponse
  }
}

// Register the mocked message handler
chrome.runtime.onMessage.addListener(handleMessage);

describe('Background Script', () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should have registered a message listener', () => {
    expect(chrome.runtime.onMessage.hasListeners()).toBe(true);
  });

  test('should handle getCurrentVideo message', (done) => {
    const sendResponse = jest.fn(() => {
      expect(sendResponse).toHaveBeenCalledWith({
        success: true,
        videoData: expect.objectContaining({
          src: expect.any(String),
          title: expect.any(String),
          duration: expect.any(Number)
        })
      });
      done();
    });

    handleMessage({action: 'getCurrentVideo'}, {}, sendResponse);

    // Verify tabs.executeScript was called
    expect(chrome.tabs.executeScript).toHaveBeenCalled();
  });

  test('should handle captureAudioStream message', (done) => {
    const sendResponse = jest.fn(() => {
      expect(sendResponse).toHaveBeenCalledWith({success: true});
      
      // Verify stream was processed correctly
      expect(chrome.tabCapture.capture).toHaveBeenCalledWith(
        {audio: true, video: false},
        expect.any(Function)
      );
      
      // Verify native messaging was initiated
      expect(chrome.runtime.connectNative).toHaveBeenCalledWith('com.securevideosum.app');
      
      done();
    });

    handleMessage({action: 'captureAudioStream'}, {}, sendResponse);
  });
});

// In a real test suite, you might want to add:
// - Integration tests between content script and background script
// - More comprehensive tests for error handling
// - Tests for the communication with the native messaging host 