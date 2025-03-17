/**
 * Secure Video Summarizer - Content Script
 * 
 * This script interacts with the webpage and video player to:
 * 1. Detect video elements on the page
 * 2. Extract video metadata
 * 3. Control video playback when needed
 * 4. Observe video changes
 */

// Keep track of the main video element
let primaryVideoElement = null;
let videoObserver = null;

// Find all video elements on the page and return the main one
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
  // Strategy: Find the largest video that's visible and playing
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
  // Look for nearby heading elements
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
  
  // Check for headings in these relative positions
  const positions = [
    { relation: 'parent', selector: 'h1, h2, h3, h4, h5, h6, .video-title, .title' },
    { relation: 'sibling', selector: 'h1, h2, h3, h4, h5, h6, .video-title, .title' },
    { relation: 'prev-sibling', selector: 'h1, h2, h3, h4, h5, h6, .video-title, .title' },
    { relation: 'container', selector: '.video-container h1, .video-container h2, .player-container h1' }
  ];
  
  const headings = [];
  
  // Check parent for headings
  let parent = videoElement.parentElement;
  if (parent) {
    const parentHeadings = parent.querySelectorAll(positions[0].selector);
    headings.push(...Array.from(parentHeadings));
    
    // Check sibling elements
    const siblings = Array.from(parent.children);
    for (const sibling of siblings) {
      if (sibling !== videoElement) {
        const siblingHeadings = sibling.querySelectorAll(positions[1].selector);
        headings.push(...Array.from(siblingHeadings));
        
        // Check if the sibling itself is a heading
        if (sibling.matches(positions[1].selector)) {
          headings.push(sibling);
        }
      }
    }
    
    // Check for container classes
    const containers = document.querySelectorAll('.video-container, .player-container');
    for (const container of containers) {
      if (container.contains(videoElement)) {
        const containerHeadings = container.querySelectorAll(positions[3].selector);
        headings.push(...Array.from(containerHeadings));
      }
    }
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

// Setup video observer to detect changes to the video element
function setupVideoObserver() {
  if (videoObserver) {
    videoObserver.disconnect();
  }
  
  // Find the video again in case the DOM changed
  primaryVideoElement = findMainVideoElement();
  
  if (!primaryVideoElement) {
    // If no video found, check again later
    setTimeout(setupVideoObserver, 2000);
    return;
  }
  
  // Create a mutation observer to detect changes to the video element
  videoObserver = new MutationObserver((mutations) => {
    // Video might have been replaced, check again
    const currentVideo = findMainVideoElement();
    if (currentVideo !== primaryVideoElement) {
      primaryVideoElement = currentVideo;
      setupVideoObserver();
    }
  });
  
  // Observe changes to the video element's attributes
  videoObserver.observe(primaryVideoElement, {
    attributes: true,
    attributeFilter: ['src', 'currentSrc']
  });
  
  // Also observe changes to the document body in case video is added/removed
  const bodyObserver = new MutationObserver((mutations) => {
    // Check if video-related elements were added or removed
    const videoRelatedChange = mutations.some(mutation => {
      return Array.from(mutation.addedNodes).some(node => {
        return node.nodeName === 'VIDEO' || 
               (node.nodeType === Node.ELEMENT_NODE && node.querySelector('video'));
      }) || 
      Array.from(mutation.removedNodes).some(node => {
        return node.nodeName === 'VIDEO' || 
               (node.nodeType === Node.ELEMENT_NODE && node.querySelector('video'));
      });
    });
    
    if (videoRelatedChange) {
      // Re-find the primary video
      const newPrimaryVideo = findMainVideoElement();
      if (newPrimaryVideo !== primaryVideoElement) {
        primaryVideoElement = newPrimaryVideo;
        setupVideoObserver();
      }
    }
  });
  
  // Observe changes to the body
  bodyObserver.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Initialize when the page is loaded
function initialize() {
  primaryVideoElement = findMainVideoElement();
  setupVideoObserver();
  
  // Log for debugging
  console.log('Secure Video Summarizer content script initialized');
  if (primaryVideoElement) {
    console.log('Found primary video:', extractVideoMetadata(primaryVideoElement));
  } else {
    console.log('No video found on page');
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
      } else if (request.control === 'setPlaybackRate' && request.rate !== undefined) {
        // Set the playback rate
        const rate = parseFloat(request.rate);
        if (!isNaN(rate) && rate > 0) {
          videoElement.playbackRate = rate;
          console.log(`Playback rate set to ${rate}x`);
        } else {
          throw new Error('Invalid playback rate');
        }
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

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
} 