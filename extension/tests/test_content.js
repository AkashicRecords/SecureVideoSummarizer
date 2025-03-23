/**
 * Tests for the content.js script of the Secure Video Summarizer extension.
 * 
 * To run these tests:
 * 1. Install Jest: npm install --save-dev jest
 * 2. Run: npm test
 */

// Mock the DOM for content script testing
document.body.innerHTML = `
  <div class="video-container">
    <h2 class="video-title">Test Course Video</h2>
    <video id="main-video" src="https://example.com/test-video.mp4" width="640" height="360"></video>
  </div>
  <div class="secondary-container">
    <video id="secondary-video" src="https://example.com/secondary.mp4" width="320" height="180"></video>
  </div>
`;

// Mock video element properties and methods
const mockVideoElements = () => {
  const videos = document.querySelectorAll('video');
  videos.forEach(video => {
    // Create properties without redefining native prototypes
    video.duration = 120;
    video.currentTime = 30;
    video.paused = false;
    video.muted = false;
    video.volume = 0.8;
    video.playbackRate = 1.0;
    video.videoWidth = 1280;
    video.videoHeight = 720;
    video.currentSrc = video.getAttribute('src');
    
    // Store the original getBoundingClientRect
    const originalGetBoundingClientRect = video.getBoundingClientRect;
    
    // Replace with a mock function that returns our custom dimensions
    video.getBoundingClientRect = jest.fn().mockImplementation(() => ({
      width: parseInt(video.getAttribute('width') || '640'),
      height: parseInt(video.getAttribute('height') || '360'),
      top: 100,
      left: 100,
      bottom: 100 + parseInt(video.getAttribute('height') || '360'),
      right: 100 + parseInt(video.getAttribute('width') || '640')
    }));
    
    // Mock methods
    video.play = jest.fn().mockResolvedValue(undefined);
    video.pause = jest.fn();
  });
};

// Mock chrome API
global.chrome = {
  runtime: {
    onMessage: {
      addListener: jest.fn()
    }
  }
};

// Mock window properties
Object.defineProperty(window, 'innerWidth', { value: 1920 });
Object.defineProperty(window, 'innerHeight', { value: 1080 });
Object.defineProperty(window, 'location', { 
  value: { 
    href: 'https://olympus-learning.com/courses/test-course' 
  } 
});

// Import the functions from content.js
const { 
  findMainVideoElement,
  extractVideoMetadata,
  getNearbyHeadings,
  detectPlatform,
  handleMessage
} = require('../content.js');

// Mock variables needed by the content script
global.primaryVideoElement = null;
global.isOlympusPlayer = false;
global.window._initialVideoMetadata = null;

// Tests for content.js
describe('Content Script', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    global.primaryVideoElement = null;
    global.isOlympusPlayer = false;
    
    // Setup test DOM
    document.body.innerHTML = `
      <div class="video-container">
        <h2 class="video-title">Test Course Video</h2>
        <video id="main-video" 
               src="https://example.com/test-video.mp4" 
               width="640" 
               height="360">
        </video>
      </div>
      <div class="secondary-container">
        <video id="secondary-video" 
               src="https://example.com/secondary.mp4" 
               width="320" 
               height="180">
        </video>
      </div>
    `;
    
    // Mock the video elements
    const mockVideos = document.querySelectorAll('video');
    mockVideos.forEach(video => {
      video.duration = 120;
      video.currentTime = 30;
      video.paused = false;
      video.muted = false;
      video.volume = 0.8;
      video.playbackRate = 1.0;
      video.videoWidth = 1280;
      video.videoHeight = 720;
      video.currentSrc = video.getAttribute('src');
      video.play = jest.fn().mockResolvedValue(undefined);
      video.pause = jest.fn();
      video.readyState = 4; // HAVE_ENOUGH_DATA
      
      // Mock getBoundingClientRect
      video.getBoundingClientRect = jest.fn().mockReturnValue({
        width: 640,
        height: 360,
        top: 100,
        left: 100,
        bottom: 460,
        right: 740
      });
    });
    
    // Set up window location for platform detection
    Object.defineProperty(window, 'location', {
      value: {
        href: 'https://olympus-learning.com/course/123',
        hostname: 'olympus-learning.com'
      },
      writable: true
    });
  });
  
  describe('findMainVideoElement', () => {
    test('should find the main video element when only one exists', () => {
      // Remove the secondary video
      const secondaryVideo = document.getElementById('secondary-video');
      secondaryVideo.parentNode.removeChild(secondaryVideo);
      
      const result = findMainVideoElement();
      
      expect(result).not.toBeNull();
      expect(result.id).toBe('main-video');
    });
    
    test('should find the largest visible video when multiple exist', () => {
      const result = findMainVideoElement();
      
      expect(result).not.toBeNull();
      expect(result.id).toBe('main-video');
    });
    
    test('should return null when no videos exist', () => {
      // Remove all videos
      const videos = document.querySelectorAll('video');
      videos.forEach(video => video.parentNode.removeChild(video));
      
      const result = findMainVideoElement();
      
      expect(result).toBeNull();
    });
  });
  
  describe('extractVideoMetadata', () => {
    test('should return null for null input', () => {
      const result = extractVideoMetadata(null);
      expect(result).toBeNull();
    });
    
    test('should extract basic metadata from video element', () => {
      const videoElement = document.getElementById('main-video');
      const result = extractVideoMetadata(videoElement);
      
      expect(result).toBeDefined();
      expect(result.src).toBe('https://example.com/test-video.mp4');
      expect(result.duration).toBe(120);
      expect(result.currentTime).toBe(30);
      expect(result.paused).toBe(false);
    });
  });
  
  describe('getNearbyHeadings', () => {
    test('should return empty array for null input', () => {
      const result = getNearbyHeadings(null);
      expect(result).toEqual([]);
    });
    
    test('should find headings near the video element', () => {
      const videoElement = document.getElementById('main-video');
      const result = getNearbyHeadings(videoElement);
      
      // We should find at least one heading
      expect(result.length).toBeGreaterThan(0);
    });
  });
  
  describe('detectPlatform', () => {
    test('should detect olympus platform', () => {
      // Already set in the mock
      const result = detectPlatform();
      
      expect(result).toBe('olympus');
    });
    
    test('should detect youtube platform', () => {
      // Change the location
      Object.defineProperty(window, 'location', { 
        value: { href: 'https://youtube.com/watch?v=12345' } 
      });
      
      const result = detectPlatform();
      
      expect(result).toBe('youtube');
    });
    
    test('should return unknown for unrecognized platforms', () => {
      // Change the location
      Object.defineProperty(window, 'location', { 
        value: { href: 'https://example.com/video' } 
      });
      
      const result = detectPlatform();
      
      expect(result).toBe('unknown');
    });
  });
  
  describe('handleMessage', () => {
    test('should respond correctly to getCurrentVideo message', () => {
      const sendResponse = jest.fn();
      
      // Set up a mock implementation of findMainVideoElement
      global.findMainVideoElement = jest.fn(() => document.getElementById('main-video'));
      
      handleMessage({ action: 'getCurrentVideo' }, {}, sendResponse);
      
      expect(sendResponse).toHaveBeenCalled();
      const response = sendResponse.mock.calls[0][0];
      
      expect(response.success).toBe(true);
      expect(response.videoData).toBeDefined();
    });
    
    test('should handle controlVideo message', () => {
      const videoElement = document.getElementById('main-video');
      const sendResponse = jest.fn();
      
      // Set up a mock implementation
      global.findMainVideoElement = jest.fn(() => videoElement);
      
      // Test play control
      handleMessage({ 
        action: 'controlVideo',
        control: 'play'
      }, {}, sendResponse);
      
      expect(videoElement.play).toHaveBeenCalled();
      expect(sendResponse).toHaveBeenCalled();
    });
  });
}); 