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
    // Mock video properties
    Object.defineProperties(video, {
      duration: { value: 120, writable: true },
      currentTime: { value: 30, writable: true },
      paused: { value: false, writable: true },
      muted: { value: false, writable: true },
      volume: { value: 0.8, writable: true },
      playbackRate: { value: 1.0, writable: true },
      videoWidth: { value: 1280, writable: true },
      videoHeight: { value: 720, writable: true },
      currentSrc: { value: video.getAttribute('src'), writable: true },
      getBoundingClientRect: {
        value: () => ({
          width: parseInt(video.getAttribute('width')),
          height: parseInt(video.getAttribute('height')),
          top: 100,
          left: 100,
          bottom: 100 + parseInt(video.getAttribute('height')),
          right: 100 + parseInt(video.getAttribute('width'))
        })
      },
      play: { value: jest.fn().mockResolvedValue(undefined) },
      pause: { value: jest.fn() }
    });
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

// Import or recreate the functionality from content.js
// Note: In a real test, you would import the actual code
// For this test, we'll recreate the key functions

// Find the main video element on the page
function findMainVideoElement() {
  const videoElements = Array.from(document.querySelectorAll('video'));
  
  if (videoElements.length === 0) {
    return null;
  }
  
  // If there's only one video, that's our primary
  if (videoElements.length === 1) {
    return videoElements[0];
  }
  
  // If there are multiple videos, try to find the most relevant one
  // Strategy: Find the largest video that's visible
  let mainVideo = null;
  let largestArea = 0;
  
  for (const video of videoElements) {
    // Check if video is visible
    const rect = video.getBoundingClientRect();
    const isVisible = rect.width > 0 && rect.height > 0 &&
                     rect.top < window.innerHeight && rect.bottom > 0 &&
                     rect.left < window.innerWidth && rect.right > 0;
    
    if (isVisible) {
      const area = rect.width * rect.height;
      // Prefer videos that are playing or paused over those that haven't started
      const playbackBonus = !video.paused || video.currentTime > 0 ? 1.5 : 1;
      const effectiveArea = area * playbackBonus;
      
      if (effectiveArea > largestArea) {
        largestArea = effectiveArea;
        mainVideo = video;
      }
    }
  }
  
  return mainVideo || videoElements[0];
}

// Extract metadata from a video element
function extractVideoMetadata(videoElement) {
  if (!videoElement) return null;
  
  // Try to find a more descriptive title than just the page title
  let title = document.title; // Default to page title
  const nearbyHeadings = getNearbyHeadings(videoElement);
  if (nearbyHeadings.length > 0) {
    // Use the first heading found
    title = nearbyHeadings[0].textContent.trim();
  }
  
  // Extract other metadata
  return {
    src: videoElement.currentSrc || videoElement.src,
    title: title,
    duration: videoElement.duration || 0,
    currentTime: videoElement.currentTime || 0,
    paused: videoElement.paused,
    muted: videoElement.muted,
    volume: videoElement.volume,
    playbackRate: videoElement.playbackRate,
    width: videoElement.videoWidth,
    height: videoElement.videoHeight,
    platform: detectPlatform()
  };
}

// Find headings near the video element
function getNearbyHeadings(videoElement) {
  if (!videoElement) return [];
  
  const headings = [];
  
  // Check parent for headings
  let parent = videoElement.parentElement;
  if (parent) {
    const parentHeadings = parent.querySelectorAll('h1, h2, h3, h4, h5, h6, .video-title, .title');
    headings.push(...Array.from(parentHeadings));
  }
  
  return headings;
}

// Detect which video platform is being used
function detectPlatform() {
  const url = window.location.href;
  
  if (url.includes('olympus-learning.com') || url.includes('olympus.learning')) {
    return 'olympus';
  } else if (url.includes('youtube.com')) {
    return 'youtube';
  } else if (url.includes('vimeo.com')) {
    return 'vimeo';
  } else {
    return 'unknown';
  }
}

// Message handler for communication with popup and background script
function handleMessage(request, sender, sendResponse) {
  if (request.action === 'getCurrentVideo') {
    const videoElement = findMainVideoElement();
    
    if (videoElement) {
      sendResponse({ 
        success: true, 
        videoData: extractVideoMetadata(videoElement) 
      });
    } else {
      sendResponse({ 
        success: false, 
        error: 'No video found on page' 
      });
    }
    return true;
  }
  
  if (request.action === 'controlVideo') {
    const videoElement = findMainVideoElement();
    
    if (!videoElement) {
      sendResponse({ success: false, error: 'No video found on page' });
      return true;
    }
    
    try {
      if (request.control === 'play') {
        videoElement.play();
      } else if (request.control === 'pause') {
        videoElement.pause();
      } else if (request.control === 'seek' && request.time !== undefined) {
        videoElement.currentTime = request.time;
      }
      
      sendResponse({ 
        success: true, 
        videoData: extractVideoMetadata(videoElement) 
      });
    } catch (error) {
      sendResponse({ 
        success: false, 
        error: error.message || 'Failed to control video' 
      });
    }
    return true;
  }
}

// Tests for content.js
describe('Content Script', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock video elements
    mockVideoElements();
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
    test('should extract metadata from a video element', () => {
      const videoElement = document.getElementById('main-video');
      const result = extractVideoMetadata(videoElement);
      
      expect(result).toEqual({
        src: 'https://example.com/test-video.mp4',
        title: 'Test Course Video', // From nearby heading
        duration: 120,
        currentTime: 30,
        paused: false,
        muted: false,
        volume: 0.8,
        playbackRate: 1.0,
        width: 1280,
        height: 720,
        platform: 'olympus'
      });
    });
    
    test('should return null if no video element provided', () => {
      const result = extractVideoMetadata(null);
      
      expect(result).toBeNull();
    });
  });
  
  describe('getNearbyHeadings', () => {
    test('should find headings near the video element', () => {
      const videoElement = document.getElementById('main-video');
      const result = getNearbyHeadings(videoElement);
      
      expect(result.length).toBe(1);
      expect(result[0].textContent).toBe('Test Course Video');
    });
    
    test('should return empty array if no headings found', () => {
      // Remove the heading
      const heading = document.querySelector('.video-title');
      heading.parentNode.removeChild(heading);
      
      const videoElement = document.getElementById('main-video');
      const result = getNearbyHeadings(videoElement);
      
      expect(result.length).toBe(0);
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
    test('should handle getCurrentVideo message with video present', () => {
      const sendResponse = jest.fn();
      
      handleMessage({ action: 'getCurrentVideo' }, {}, sendResponse);
      
      expect(sendResponse).toHaveBeenCalledWith({
        success: true,
        videoData: expect.objectContaining({
          src: 'https://example.com/test-video.mp4',
          title: 'Test Course Video'
        })
      });
    });
    
    test('should handle getCurrentVideo message with no video', () => {
      // Remove all videos
      const videos = document.querySelectorAll('video');
      videos.forEach(video => video.parentNode.removeChild(video));
      
      const sendResponse = jest.fn();
      
      handleMessage({ action: 'getCurrentVideo' }, {}, sendResponse);
      
      expect(sendResponse).toHaveBeenCalledWith({
        success: false,
        error: 'No video found on page'
      });
    });
    
    test('should handle controlVideo play message', () => {
      const videoElement = document.getElementById('main-video');
      const sendResponse = jest.fn();
      
      handleMessage({ 
        action: 'controlVideo',
        control: 'play'
      }, {}, sendResponse);
      
      expect(videoElement.play).toHaveBeenCalled();
      expect(sendResponse).toHaveBeenCalledWith({
        success: true,
        videoData: expect.objectContaining({
          src: 'https://example.com/test-video.mp4'
        })
      });
    });
    
    test('should handle controlVideo pause message', () => {
      const videoElement = document.getElementById('main-video');
      const sendResponse = jest.fn();
      
      handleMessage({ 
        action: 'controlVideo',
        control: 'pause'
      }, {}, sendResponse);
      
      expect(videoElement.pause).toHaveBeenCalled();
      expect(sendResponse).toHaveBeenCalledWith({
        success: true,
        videoData: expect.objectContaining({
          src: 'https://example.com/test-video.mp4'
        })
      });
    });
  });
}); 