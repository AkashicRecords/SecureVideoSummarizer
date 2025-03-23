/**
 * Secure Video Summarizer - Content Script
 * 
 * This script interacts with the webpage and video player to:
 * 1. Detect video elements on the page
 * 2. Extract video metadata
 * 3. Control video playback when needed
 * 4. Observe video changes
 */

// Keep track of the main video element and its state
let primaryVideoElement = null;
let videoObserver = null;
let isOlympusPlayer = false;
let retryAttempts = 0;
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY = 1000; // 1 second

// Cleanup function for observers
function cleanupObservers() {
  if (videoObserver) {
    videoObserver.disconnect();
    videoObserver = null;
  }
}

// Initialize video detection with retry mechanism
async function initializeVideoDetection() {
  cleanupObservers(); // Cleanup any existing observers
  
  try {
    const video = await findMainVideoElementWithRetry();
    if (video) {
      primaryVideoElement = video;
      setupVideoObserver(video);
      return video;
    }
    return null;
  } catch (error) {
    console.error('Failed to initialize video detection:', error);
    return null;
  }
}

// Find main video element with retry mechanism
async function findMainVideoElementWithRetry() {
  return new Promise((resolve, reject) => {
    const attemptFind = async () => {
      try {
        const video = findMainVideoElement();
        if (video) {
          retryAttempts = 0;
          resolve(video);
          return;
        }
        
        if (retryAttempts < MAX_RETRY_ATTEMPTS) {
          retryAttempts++;
          setTimeout(attemptFind, RETRY_DELAY);
        } else {
          reject(new Error('Failed to find video element after maximum retries'));
        }
      } catch (error) {
        reject(error);
      }
    };
    
    attemptFind();
  });
}

// Find all video elements on the page and return the main one
function findMainVideoElement() {
  // First, check if we're on the Olympus platform
  const platform = detectPlatform();
  if (platform === 'olympus') {
    console.log('Detected Olympus platform, looking for Olympus player...');
    const olympusVideo = findOlympusPlayer();
    if (olympusVideo) {
      isOlympusPlayer = true;
      return olympusVideo;
    }
  }
  
  // Standard video element detection with improved error handling
  try {
    const videoElements = Array.from(document.querySelectorAll('video'));
    
    if (videoElements.length === 0) {
      // Check for iframes
      const iframes = Array.from(document.querySelectorAll('iframe'));
      if (iframes.length > 0) {
        console.log('Found iframes, checking for video content...');
        return handleIframeVideos(iframes);
      }
      return null;
    }
    
    // If there's only one video, validate it before returning
    if (videoElements.length === 1) {
      return validateVideoElement(videoElements[0]);
    }
    
    // Find the most relevant video
    return findMostRelevantVideo(videoElements);
  } catch (error) {
    console.error('Error in findMainVideoElement:', error);
    return null;
  }
}

// Validate a video element
function validateVideoElement(video) {
  if (!video) return null;
  
  try {
    // Check if the video element is functional
    if (typeof video.play !== 'function' || typeof video.pause !== 'function') {
      console.warn('Invalid video element: missing play/pause functions');
      return null;
    }
    
    // Check if the video is actually playable
    if (video.readyState === 0 && !video.src && !video.querySelector('source')) {
      console.warn('Invalid video element: no playable source');
      return null;
    }
    
    return video;
  } catch (error) {
    console.error('Error validating video element:', error);
    return null;
  }
}

// Find the most relevant video from a list
function findMostRelevantVideo(videos) {
  let mainVideo = null;
  let maxScore = 0;
  
  for (const video of videos) {
    try {
      const score = calculateVideoScore(video);
      if (score > maxScore) {
        maxScore = score;
        mainVideo = video;
      }
    } catch (error) {
      console.warn('Error calculating video score:', error);
    }
  }
  
  return mainVideo;
}

// Calculate a relevance score for a video
function calculateVideoScore(video) {
  let score = 0;
  
  try {
    // Check visibility
    const rect = video.getBoundingClientRect();
    const isVisible = rect.width > 0 && rect.height > 0 &&
                     rect.top < window.innerHeight && rect.bottom > 0 &&
                     rect.left < window.innerWidth && rect.right > 0;
    
    if (!isVisible) return 0;
    
    // Base score from size
    score += (rect.width * rect.height) / (window.innerWidth * window.innerHeight);
    
    // Playback state bonus
    if (!video.paused) score += 0.3;
    if (video.currentTime > 0) score += 0.2;
    
    // Source quality bonus
    if (video.src) score += 0.1;
    if (video.readyState >= 3) score += 0.1;
    
    return score;
  } catch (error) {
    console.warn('Error in calculateVideoScore:', error);
    return 0;
  }
}

// Handle iframe videos
function handleIframeVideos(iframes) {
  for (const iframe of iframes) {
    try {
      // Try to detect video player iframes
      const isVideoFrame = 
        iframe.src.includes('player') ||
        iframe.src.includes('video') ||
        iframe.src.includes('embed');
      
      if (isVideoFrame) {
        return createVirtualVideo(iframe.src);
      }
    } catch (error) {
      console.warn('Error checking iframe:', error);
    }
  }
  return null;
}

// Setup video observer
function setupVideoObserver(video) {
  if (!video) return;
  
  cleanupObservers(); // Cleanup existing observer
  
  try {
    videoObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'attributes') {
          // Handle video attribute changes
          handleVideoAttributeChange(video, mutation.attributeName);
        }
      }
    });
    
    videoObserver.observe(video, {
      attributes: true,
      attributeFilter: ['src', 'currentSrc', 'readyState', 'paused']
    });
  } catch (error) {
    console.error('Error setting up video observer:', error);
  }
}

// Handle video attribute changes
function handleVideoAttributeChange(video, attributeName) {
  try {
    switch (attributeName) {
      case 'src':
      case 'currentSrc':
        // Re-validate video source
        if (!validateVideoElement(video)) {
          cleanupObservers();
          initializeVideoDetection();
        }
        break;
      case 'readyState':
        // Handle ready state changes
        if (video.readyState >= 3) {
          // Video is ready for playback
          chrome.runtime.sendMessage({
            type: 'videoStateUpdate',
            data: { ready: true }
          });
        }
        break;
    }
  } catch (error) {
    console.warn('Error handling video attribute change:', error);
  }
}

// Cleanup when the content script is unloaded
window.addEventListener('unload', () => {
  cleanupObservers();
});

// Enhanced version of findOlympusPlayer to better handle VideoJS on Olympus platform
function findOlympusPlayer() {
  if (!window.videojs) {
    console.debug('Olympus: VideoJS API not found');
    return null;
  }

  try {
    // Try to get players using different VideoJS API methods
    let player = null;
    let players = {};
    
    // Method 1: videojs.getPlayers()
    if (typeof videojs.getPlayers === 'function') {
      players = videojs.getPlayers();
      if (Object.keys(players).length > 0) {
        player = players[Object.keys(players)[0]];
        console.debug('Olympus: Found player using videojs.getPlayers()');
      }
    }
    
    // Method 2: videojs.getAllPlayers()
    if (!player && typeof videojs.getAllPlayers === 'function') {
      const allPlayers = videojs.getAllPlayers();
      if (allPlayers && allPlayers.length > 0) {
        player = allPlayers[0];
        console.debug('Olympus: Found player using videojs.getAllPlayers()');
      }
    }
    
    // Method 3: Look for .video-js elements and get their player
    if (!player) {
      const videoJsElements = document.querySelectorAll('.video-js');
      if (videoJsElements.length > 0) {
        // Try to get the player from the element
        for (const element of videoJsElements) {
          try {
            if (element.player) {
              player = element.player;
              console.debug('Olympus: Found player via element.player');
              break;
            } else if (element.id && videojs(element.id)) {
              player = videojs(element.id);
              console.debug(`Olympus: Found player via videojs('${element.id}')`);
              break;
            }
          } catch (err) {
            console.debug('Olympus: Error getting player from element:', err);
            continue;
          }
        }
      }
    }
    
    if (!player) {
      console.debug('Olympus: No VideoJS player found');
      return null;
    }
    
    // Get video element from player
    let videoElement = null;
    
    // Try player.el().querySelector('video')
    try {
      if (player.el()) {
        videoElement = player.el().querySelector('video');
        if (videoElement) {
          console.debug('Olympus: Found video element from player element');
        }
      }
    } catch (err) {
      console.debug('Olympus: Error finding video element in player element:', err);
    }
    
    // Try player.tech().el()
    if (!videoElement) {
      try {
        if (player.tech && typeof player.tech === 'function' && player.tech()) {
          videoElement = player.tech().el();
          if (videoElement) {
            console.debug('Olympus: Found video element from player.tech().el()');
          }
        }
      } catch (err) {
        console.debug('Olympus: Error getting tech element:', err);
      }
    }
    
    // If we still don't have a video element, create a virtual one
    if (!videoElement) {
      console.debug('Olympus: Creating virtual video element for VideoJS player');
      videoElement = document.createElement('video');
      
      // Set up properties based on player API
      Object.defineProperty(videoElement, 'currentTime', {
        get: function() { 
          try { return player.currentTime(); } 
          catch (e) { return 0; }
        },
        set: function(time) { 
          try { player.currentTime(time); } 
          catch (e) { console.error('Failed to set currentTime', e); }
        }
      });
      
      Object.defineProperty(videoElement, 'duration', {
        get: function() { 
          try { return player.duration(); } 
          catch (e) { return 0; }
        }
      });
      
      Object.defineProperty(videoElement, 'paused', {
        get: function() { 
          try { return player.paused(); } 
          catch (e) { return true; }
        }
      });
      
      // Add methods
      videoElement.play = function() { 
        try { return player.play(); } 
        catch (e) { console.error('Failed to play', e); return Promise.reject(e); }
      };
      
      videoElement.pause = function() { 
        try { return player.pause(); } 
        catch (e) { console.error('Failed to pause', e); }
      };
      
      // Mark as virtual
      videoElement._isVirtual = true;
      videoElement._videojsPlayer = player;
    }
    
    return {
      videoElement,
      player
    };
  } catch (err) {
    console.error('Olympus: Error finding VideoJS player:', err);
    return null;
  }
}

// Extract metadata from a video element
function extractVideoMetadata(videoElement) {
  if (!videoElement) return null;
  
  // Handle virtual video elements
  if (videoElement.tagName === 'VIRTUAL-VIDEO') {
    return {
      src: videoElement.src || '',
      title: document.title,
      duration: videoElement.duration || 0,
      currentTime: videoElement.currentTime || 0,
      paused: videoElement.paused,
      muted: videoElement.muted,
      volume: videoElement.volume,
      playbackRate: videoElement.playbackRate,
      width: videoElement.videoWidth,
      height: videoElement.videoHeight,
      platform: detectPlatform(),
      isVirtual: true
    };
  }
  
  // Handle iframe elements
  if (videoElement.tagName === 'IFRAME') {
    return {
      src: videoElement.src || '',
      title: document.title,
      duration: 0, // We can't access iframe content directly
      currentTime: 0,
      paused: true,
      muted: false,
      volume: 1,
      playbackRate: 1,
      width: videoElement.width,
      height: videoElement.height,
      platform: detectPlatform(),
      isIframe: true
    };
  }
  
  // Check if this is an Olympus VideoJS player
  const isOlympusVideoJS = videoElement.classList.contains('vjs-tech') || 
                          document.querySelector('.video-js') !== null ||
                          (videoElement.src && videoElement.src.startsWith('blob:')) ||
                          isOlympusPlayer;
  
  if (isOlympusVideoJS) {
    return extractOlympusVideoMetadata(videoElement);
  }
  
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

// Extract metadata specifically from Olympus VideoJS player
function extractOlympusVideoMetadata(videoElement) {
  try {
    const olympusData = findOlympusPlayer();
    if (!olympusData) {
      console.debug('Olympus: No player found for metadata extraction');
      return null;
    }
    
    const { videoElement: olympusVideoElement, player } = olympusData;
    
    // Initialize metadata object
    const metadata = {
      src: '',
      title: '',
      poster: '',
      duration: 0,
      currentTime: 0,
      isLive: false,
      isStreaming: false,
      streamSources: [],
      platform: 'olympus',
      player: 'videojs'
    };
    
    // Get basic properties from video element
    if (olympusVideoElement) {
      if (olympusVideoElement.src) metadata.src = olympusVideoElement.src;
      if (olympusVideoElement.currentTime) metadata.currentTime = olympusVideoElement.currentTime;
      if (olympusVideoElement.duration && !isNaN(olympusVideoElement.duration)) metadata.duration = olympusVideoElement.duration;
    }
    
    // Try to get the src from the player if we don't have it
    if (!metadata.src && player) {
      try {
        // Check for current source
        const currentSrc = player.currentSrc();
        if (currentSrc) metadata.src = currentSrc;
        
        // Check for sources array
        const sources = player.currentSources();
        if (sources && Array.isArray(sources) && sources.length > 0) {
          metadata.streamSources = sources.map(s => ({
            src: s.src,
            type: s.type,
            label: s.label || '',
            res: s.res || s.resolution || ''
          }));
          
          // If we still don't have a src, use the first source
          if (!metadata.src && metadata.streamSources.length > 0) {
            metadata.src = metadata.streamSources[0].src;
          }
          
          // Check if this is HLS or other streaming format
          if (sources.some(s => 
            s.type === 'application/x-mpegURL' || 
            s.type === 'application/vnd.apple.mpegurl' ||
            (s.src && (s.src.includes('.m3u8') || s.src.includes('streaming')))
          )) {
            metadata.isStreaming = true;
          }
        }
      } catch (e) {
        console.debug('Olympus: Error getting sources from player', e);
      }
    }
    
    // Try to find title from the UI
    try {
      // Look for video title in common locations
      const possibleTitleElements = [
        document.querySelector('.video-title'),
        document.querySelector('.lesson-title'),
        document.querySelector('.course-video-title'),
        document.querySelector('h1'),
        document.querySelector('h2'),
        ...document.querySelectorAll('[class*="title"]:not(meta)'),
        ...document.querySelectorAll('[class*="heading"]:not(meta)')
      ];
      
      for (const element of possibleTitleElements) {
        if (element && element.textContent.trim().length > 0) {
          metadata.title = element.textContent.trim();
          break;
        }
      }
    } catch (e) {
      console.debug('Olympus: Error finding video title', e);
    }
    
    // Get additional metadata from player
    if (player) {
      try {
        // Get poster
        if (player.poster) {
          const posterUrl = typeof player.poster === 'function' ? player.poster() : player.poster;
          if (posterUrl) metadata.poster = posterUrl;
        }
        
        // Check if video is live
        if (player.duration) {
          const duration = player.duration();
          if (duration === Infinity || (duration > 0 && player.liveTracker && player.liveTracker.isLive())) {
            metadata.isLive = true;
          }
        }
        
        // If we still don't have duration, try to get it from the player
        if (metadata.duration === 0 && player.duration) {
          const duration = player.duration();
          if (duration && !isNaN(duration) && duration !== Infinity) {
            metadata.duration = duration;
          }
        }
      } catch (e) {
        console.debug('Olympus: Error getting additional metadata from player', e);
      }
    }
    
    // Try to parse duration from UI if we still don't have it
    if (metadata.duration === 0) {
      try {
        // Look for duration in time displays
        const timeElements = document.querySelectorAll('.vjs-duration, .vjs-time-display, [class*="duration"], [class*="time-display"]');
        for (const element of timeElements) {
          const text = element.textContent.trim();
          if (text.match(/\d+:\d+/)) {
            // Parse time in format MM:SS or HH:MM:SS
            const parts = text.split(':').map(Number);
            if (parts.length === 2) { // MM:SS
              metadata.duration = parts[0] * 60 + parts[1];
              break;
            } else if (parts.length === 3) { // HH:MM:SS
              metadata.duration = parts[0] * 3600 + parts[1] * 60 + parts[2];
              break;
            }
          }
        }
      } catch (e) {
        console.debug('Olympus: Error parsing duration from UI', e);
      }
    }
    
    // If we still have no title, use the URL
    if (!metadata.title && metadata.src) {
      try {
        const urlObj = new URL(metadata.src);
        const pathParts = urlObj.pathname.split('/');
        const filename = pathParts[pathParts.length - 1];
        metadata.title = filename.split('.')[0] || 'Olympus Video';
      } catch (e) {
        metadata.title = 'Olympus Video';
      }
    }
    
    return metadata;
  } catch (err) {
    console.error('Olympus: Error extracting video metadata:', err);
    return null;
  }
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
  const url = window.location.href.toLowerCase();
  
  if (url.includes('youtube.com')) {
    return 'youtube';
  } else if (url.includes('vimeo.com')) {
    return 'vimeo';
  } else if (url.includes('olympus-learning.com') || url.includes('olympus.learning') || url.includes('mygreatlearning.com')) {
    return 'olympus';
  }
  
  // Check for common video platforms based on elements
  // ... existing code ...
}

// Add a message listener to handle communication from the popup
chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  try {
    console.log('Content script received message:', message);
    
    // Handle ping action to verify content script is loaded
    if (message.action === 'ping') {
      console.log('Ping received, content script is loaded');
      sendResponse({ status: 'ok' });
      return true;
    }
    
    // Handle other message actions as needed
    if (message.action === 'getCurrentVideo') {
      const videoElement = findMainVideoElement();
      
      if (videoElement) {
        sendResponse({ 
          success: true, 
          videoData: extractVideoMetadata(videoElement) 
        });
      } else {
        // If we previously had a video but can't find it now, try to recover using stored metadata
        if (window._initialVideoMetadata) {
          console.log('Video element not found, but returning previously stored metadata');
          sendResponse({
            success: true,
            videoData: window._initialVideoMetadata,
            warning: 'Using cached video metadata. Some player controls may not work.'
          });
          return true;
        }
        
        // Try one more desperate attempt to find a video
        const anyVideo = document.querySelector('video');
        if (anyVideo) {
          console.log('Found video element with generic querySelector as last resort');
          primaryVideoElement = anyVideo;
          sendResponse({
            success: true,
            videoData: extractVideoMetadata(anyVideo)
          });
          return true;
        }
        
        sendResponse({ 
          success: false, 
          error: 'No video found on page' 
        });
      }
      return true;
    } else if (message.action === 'controlVideo') {
      const videoElement = findMainVideoElement();
      
      if (!videoElement) {
        sendResponse({ success: false, error: 'No video found on page' });
        return true;
      }
      
      try {
        // Check if this is a VideoJS/Olympus player
        const isVideoJS = videoElement.isVideoJS || isOlympusPlayer || document.querySelector('.video-js') !== null;
        
        if (isVideoJS) {
          console.log('Controlling VideoJS player:', message.control);
          
          // Get the player instance through our helpers
          const playerInstance = videoElement.playerInstance || window._videoJSPlayer || getVideoJSInstance();
          let success = false;
          
          if (playerInstance) {
            console.log('Found VideoJS player instance, using its API');
            
            switch (message.control) {
              case 'play':
                if (typeof playerInstance.play === 'function') {
                  try {
                    const playPromise = playerInstance.play();
                    if (playPromise && typeof playPromise.then === 'function') {
                      playPromise
                        .then(() => console.log('Successfully started playback via VideoJS API'))
                        .catch(error => {
                          console.error('Error during play() via VideoJS API:', error);
                          // Try clicking the play button as fallback
                          success = tryClickVideoJSPlayButton();
                        });
                    }
                    success = true;
                  } catch (e) {
                    console.error('Error calling play() on player instance:', e);
                    // Try clicking the play button as fallback
                    success = tryClickVideoJSPlayButton();
                  }
                } else {
                  console.log('No play method available, trying button click fallback');
                  success = tryClickVideoJSPlayButton();
                }
                break;
                
              case 'pause':
                if (typeof playerInstance.pause === 'function') {
                  try {
                    playerInstance.pause();
                    console.log('Successfully paused via VideoJS API');
                    success = true;
                  } catch (e) {
                    console.error('Error calling pause() on player instance:', e);
                    // Try clicking pause button as fallback
                    success = tryClickVideoJSPauseButton();
                  }
                } else {
                  console.log('No pause method available, trying button click fallback');
                  success = tryClickVideoJSPauseButton();
                }
                break;
                
              case 'seek':
                if (message.time !== undefined) {
                  const time = parseFloat(message.time);
                  if (!isNaN(time) && time >= 0) {
                    if (typeof playerInstance.currentTime === 'function') {
                      try {
                        playerInstance.currentTime(time);
                        console.log('Successfully seeked to', time, 'via VideoJS API');
                        success = true;
                      } catch (e) {
                        console.error('Error calling currentTime() on player instance:', e);
                      }
                    }
                  } else {
                    console.error('Invalid seek time:', message.time);
                  }
                }
                break;
                
              case 'setPlaybackRate':
                if (message.rate !== undefined) {
                  const rate = parseFloat(message.rate);
                  if (!isNaN(rate) && rate > 0) {
                    if (typeof playerInstance.playbackRate === 'function') {
                      try {
                        playerInstance.playbackRate(rate);
                        console.log('Successfully set playback rate to', rate, 'via VideoJS API');
                        success = true;
                      } catch (e) {
                        console.error('Error calling playbackRate() on player instance:', e);
                      }
                    }
                  } else {
                    console.error('Invalid playback rate:', message.rate);
                  }
                }
                break;
            }
            
            // If successful, extract metadata and respond
            if (success) {
              sendResponse({
                success: true,
                videoData: extractVideoMetadata(videoElement),
                message: `Successfully executed ${message.control} command on VideoJS player`
              });
              return true;
            }
          } else {
            console.log('No player instance found, trying button click fallbacks');
            
            // Try button click fallbacks
            switch (message.control) {
              case 'play':
                success = tryClickVideoJSPlayButton();
                break;
              case 'pause':
                success = tryClickVideoJSPauseButton();
                break;
            }
            
            if (success) {
              sendResponse({
                success: true,
                videoData: extractVideoMetadata(videoElement),
                warning: 'Limited control available for this video player'
              });
              return true;
            }
          }
          
          // If we get here, all VideoJS-specific attempts failed
          console.log('All VideoJS control attempts failed, falling back to standard video controls');
        }
        
        // Standard HTML5 video element control
        if (videoElement.tagName === 'VIDEO') {
          if (message.control === 'play') {
            videoElement.play();
          } else if (message.control === 'pause') {
            videoElement.pause();
          } else if (message.control === 'seek' && message.time !== undefined) {
            const time = parseFloat(message.time);
            if (!isNaN(time) && time >= 0) {
              videoElement.currentTime = time;
            } else {
              throw new Error('Invalid seek time');
            }
          } else if (message.control === 'setPlaybackRate' && message.rate !== undefined) {
            const rate = parseFloat(message.rate);
            if (!isNaN(rate) && rate > 0) {
              videoElement.playbackRate = rate;
            } else {
              throw new Error('Invalid playback rate');
            }
          }
          
          sendResponse({
            success: true,
            videoData: extractVideoMetadata(videoElement)
          });
        } else {
          sendResponse({
            success: false,
            error: 'This video player has limited control capabilities',
            videoData: extractVideoMetadata(videoElement),
            warning: 'Limited control available for this video player'
          });
        }
      } catch (error) {
        sendResponse({
          success: false,
          error: error.message || 'Failed to control video',
          videoData: extractVideoMetadata(videoElement)
        });
      }
      return true;
    }
  } catch (error) {
    console.error('Error handling message in content script:', error);
    sendResponse({ error: error.message });
  }
  return true; // Keep the message channel open for async responses
});

// Helper function to get VideoJS player instance
function getVideoJSInstance() {
  console.log('Attempting to find VideoJS player instance using multiple methods');
  
  // Check if we have a stored videoJS player from the detection phase
  if (window._videoJSPlayer) {
    console.log('Using stored VideoJS player instance from earlier detection');
    return window._videoJSPlayer;
  }
  
  // Method 1: Check if videojs is directly accessible in global scope
  // This is the most reliable method according to VideoJS docs
  if (typeof window.videojs !== 'undefined') {
    console.log('VideoJS found in global scope');
    try {
      // Try to get players using official API methods
      // Method 1a: Try videojs.getPlayers() (older versions)
      if (typeof videojs.getPlayers === 'function') {
        const players = videojs.getPlayers();
        if (players && Object.keys(players).length > 0) {
          const playerId = Object.keys(players)[0];
          console.log('Found player via videojs.getPlayers():', playerId);
          return players[playerId];
        }
      }
      
      // Method 1b: Try videojs.getAllPlayers() (newer versions)
      if (typeof videojs.getAllPlayers === 'function') {
        const players = videojs.getAllPlayers();
        if (players && players.length > 0) {
          console.log('Found player via videojs.getAllPlayers()');
          return players[0];
        }
      }
      
      // Method 1c: Try to get player by element ID
      const videoJsPlayer = document.querySelector('.video-js');
      if (videoJsPlayer && videoJsPlayer.id) {
        try {
          console.log('Found player via element ID:', videoJsPlayer.id);
          return videojs(videoJsPlayer.id);
        } catch (e) {
          console.log('Error getting player by ID:', e);
        }
      }
      
      // Method 1d: Try videojs.getPlayer() method if available (some versions)
      if (typeof videojs.getPlayer === 'function') {
        const videoJsPlayer = document.querySelector('.video-js');
        if (videoJsPlayer && videoJsPlayer.id) {
          try {
            const player = videojs.getPlayer(videoJsPlayer.id);
            if (player) {
              console.log('Found player via videojs.getPlayer():', videoJsPlayer.id);
              return player;
            }
          } catch (e) {
            console.log('Error getting player via getPlayer():', e);
          }
        }
      }
    } catch (e) {
      console.log('Error accessing VideoJS player via global object:', e);
    }
  } else {
    console.log('VideoJS not found in global scope, checking for alternative access methods');
  }
  
  // Method 2: Look for player instance in data attributes
  const videoJsPlayer = document.querySelector('.video-js');
  if (videoJsPlayer) {
    console.log('Found .video-js element, checking for player data');
    
    // Check for player instance in known property names
    const possibleProperties = [
      'player',
      '_player', 
      '__player', 
      'vjs', 
      'videojs',
      '_vjs',
      'vjsPlayer',
      '__videojs__',
      'tech', // VideoJS 7+ might store the player in the tech object
      'tech_'  // VideoJS tech object naming
    ];
    
    for (const prop of possibleProperties) {
      if (videoJsPlayer[prop]) {
        console.log('Found player instance in element property:', prop);
        return videoJsPlayer[prop];
      }
    }
    
    // Check if player is attached via jQuery data
    if (typeof $ !== 'undefined' && typeof $.fn !== 'undefined' && typeof $.fn.data !== 'undefined') {
      try {
        const jqPlayer = $(videoJsPlayer).data('videojs') || 
                        $(videoJsPlayer).data('player') || 
                        $(videoJsPlayer).data('vjs');
        if (jqPlayer) {
          console.log('Found player via jQuery data attribute');
          return jqPlayer;
        }
      } catch (e) {
        console.log('Error checking jQuery data:', e);
      }
    }
  }
  
  // Method 3: Check for player in window objects (some implementations store the player instance here)
  const potentialWindowProps = [
    'videojs',
    'vjs',
    'videoPlayer',
    'player',
    'videoJSPlayer',
    'vjsPlayer',
    'videojs_player', // Some implementations use underscores
    'video_player',
    '_player',
    'olympusPlayer'
  ];
  
  for (const prop of potentialWindowProps) {
    if (window[prop] && typeof window[prop] === 'object') {
      console.log('Found potential player object in window.' + prop);
      // Check if it has typical videojs methods
      if ((typeof window[prop].play === 'function' && 
          typeof window[prop].pause === 'function') ||
          (window[prop].tech_ && window[prop].tech_.el_)) { // VideoJS 7+ structure
        console.log('Object appears to be a video player with standard methods');
        return window[prop];
      }
    }
  }
  
  // Method 4: Look for player methods directly on video element (fallback)
  const vjsTechVideo = document.querySelector('video.vjs-tech');
  if (vjsTechVideo) {
    console.log('Found video.vjs-tech element, creating wrapper with basic API');
    
    // Create a wrapper with available methods that work directly on the video element
    return {
      play: function() { 
        console.log('Calling play directly on video element');
        return vjsTechVideo.play(); 
      },
      pause: function() { 
        console.log('Calling pause directly on video element');
        vjsTechVideo.pause(); 
      },
      currentTime: function(time) {
        if (time !== undefined) {
          console.log('Setting currentTime directly on video element:', time);
          vjsTechVideo.currentTime = time;
          return vjsTechVideo.currentTime;
        }
        return vjsTechVideo.currentTime;
      },
      duration: function() { return vjsTechVideo.duration; },
      paused: function() { return vjsTechVideo.paused; },
      muted: function(muted) {
        if (muted !== undefined) {
          vjsTechVideo.muted = muted;
          return vjsTechVideo.muted;
        }
        return vjsTechVideo.muted;
      },
      volume: function(vol) {
        if (vol !== undefined) {
          vjsTechVideo.volume = vol;
          return vjsTechVideo.volume;
        }
        return vjsTechVideo.volume;
      },
      playbackRate: function(rate) {
        if (rate !== undefined) {
          vjsTechVideo.playbackRate = rate;
          return vjsTechVideo.playbackRate;
        }
        return vjsTechVideo.playbackRate;
      },
      src: function(src) {
        if (src !== undefined) {
          vjsTechVideo.src = src;
          return vjsTechVideo.src;
        }
        return vjsTechVideo.src || vjsTechVideo.currentSrc;
      },
      // Element reference for direct manipulation
      el: vjsTechVideo,
      tech_: { el_: vjsTechVideo }, // Mimic VideoJS 7+ structure for compatibility
      tech: { el: vjsTechVideo }     // Alternative structure used in some versions
    };
  }
  
  // Method 5: Look for video inside the VideoJS player even if it doesn't have the vjs-tech class
  const videoJsWrapper = document.querySelector('.video-js');
  if (videoJsWrapper) {
    const videoInWrapper = videoJsWrapper.querySelector('video');
    if (videoInWrapper) {
      console.log('Found video element inside .video-js wrapper, creating basic API wrapper');
      return {
        play: function() { return videoInWrapper.play(); },
        pause: function() { videoInWrapper.pause(); },
        currentTime: function(time) {
          if (time !== undefined) {
            videoInWrapper.currentTime = time;
            return videoInWrapper.currentTime;
          }
          return videoInWrapper.currentTime;
        },
        el: videoInWrapper,
        tech_: { el_: videoInWrapper },
        tech: { el: videoInWrapper }
      };
    }
  }
  
  console.log('No VideoJS player instance found with any method');
  return null;
}

// Helper function to try clicking the VideoJS play button
function tryClickVideoJSPlayButton() {
  console.log('Trying to click VideoJS play button');
  const playButtons = [
    '.vjs-play-control:not(.vjs-playing)',
    '.vjs-big-play-button',
    '.vjs-play-button',
    '[aria-label="Play"]',
    '[title="Play"]',
    '.video-js .vjs-control-bar button:first-child',
    '.video-js button[class*="play"]'
  ];
  
  for (const selector of playButtons) {
    const button = document.querySelector(selector);
    if (button) {
      console.log(`Found play button with selector: ${selector}`);
      button.click();
      return true;
    }
  }
  
  console.log('No VideoJS play button found');
  return false;
}

// Helper function to try clicking the VideoJS pause button
function tryClickVideoJSPauseButton() {
  console.log('Trying to click VideoJS pause button');
  const pauseButtons = [
    '.vjs-play-control.vjs-playing',
    '.vjs-pause-button',
    '[aria-label="Pause"]',
    '[title="Pause"]',
    '.video-js.vjs-playing .vjs-control-bar button:first-child'
  ];
  
  for (const selector of pauseButtons) {
    const button = document.querySelector(selector);
    if (button) {
      console.log(`Found pause button with selector: ${selector}`);
      button.click();
      return true;
    }
  }
  
  console.log('No VideoJS pause button found');
  return false;
}

// Add this new function to help with debugging in the console
function debugVideoPlayer() {
  console.log('=== Video Player Debug Information ===');
  
  // Check if VideoJS is globally defined
  console.log('VideoJS global object:', typeof window.videojs !== 'undefined' ? 'Available' : 'Not available');
  
  // Check if Wistia is globally defined
  console.log('Wistia global object:', typeof window.Wistia !== 'undefined' ? 'Available' : 'Not available');
  
  // Get page information
  console.log('Page URL:', window.location.href);
  console.log('Page title:', document.title);
  console.log('Platform detected:', detectPlatform());
  
  // Check for Wistia elements
  const wistiaElements = document.querySelectorAll('.wistia_embed, .wistia_responsive_padding, [class*="wistia_"]');
  console.log('Wistia elements found:', wistiaElements.length);
  
  if (wistiaElements.length > 0) {
    console.log('Wistia elements:');
    wistiaElements.forEach((el, index) => {
      console.log(`  Wistia element #${index + 1}:`, {
        element: el,
        id: el.id,
        classes: el.className,
        containsVideo: el.querySelector('video') !== null
      });
    });
    
    // Check for Wistia API
    if (typeof window.Wistia !== 'undefined' && window.Wistia.api) {
      try {
        const wistiaVideos = window.Wistia.api.all();
        console.log('Videos found via Wistia API:', wistiaVideos.length);
        
        wistiaVideos.forEach((video, index) => {
          console.log(`  Wistia video #${index + 1}:`, {
            hashedId: video.hashedId(),
            name: video.name ? video.name() : 'Unknown',
            duration: video.duration ? video.duration() : 'Unknown',
            currentTime: video.time ? video.time() : 'Unknown',
            state: video.state ? video.state() : 'Unknown'
          });
        });
      } catch (e) {
        console.log('Error accessing Wistia API:', e);
      }
    } else {
      console.log('Wistia API not available');
    }
  }
  
  // Check for cloudfront and mygreatlearning HLS/DASH streaming requests
  if (window.performance && window.performance.getEntries) {
    const streamingRequests = window.performance.getEntries().filter(entry => 
      entry.name && (
        entry.name.includes('cloudfront.net') || 
        entry.name.includes('mygreatlearning.com/HLS') ||
        entry.name.includes('hls.mygreatlearning.com') ||
        entry.name.includes('.m3u8') || 
        entry.name.includes('.mpd') ||
        entry.name.includes('.ts')
      )
    );
    
    console.log('Potential streaming requests found:', streamingRequests.length);
    
    // Count different types of requests
    const hlsRequests = streamingRequests.filter(req => 
      req.name.includes('.m3u8') || req.name.includes('.ts')
    );
    const dashRequests = streamingRequests.filter(req => 
      req.name.includes('.mpd')
    );
    const myGreatLearningRequests = streamingRequests.filter(req => 
      req.name.includes('mygreatlearning.com')
    );
    
    console.log('HLS requests:', hlsRequests.length);
    console.log('DASH requests:', dashRequests.length);
    console.log('mygreatlearning requests:', myGreatLearningRequests.length);
    
    if (streamingRequests.length > 0) {
      console.log('First 5 streaming URLs:');
      streamingRequests.slice(0, 5).forEach((req, i) => {
        console.log(`  ${i + 1}. ${req.name}`);
      });
    }
    
    // Look for specific patterns in mygreatlearning requests
    const segments = myGreatLearningRequests.filter(req => req.name.includes('.ts'));
    if (segments.length > 0) {
      console.log('Found mygreatlearning HLS segments:', segments.length);
      console.log('Sample segment:', segments[0].name);
      
      // Try to extract video ID from HLS segment URL
      const hlsUrlMatch = segments[0].name.match(/output-([a-f0-9-]+)/);
      if (hlsUrlMatch && hlsUrlMatch[1]) {
        const videoId = hlsUrlMatch[1];
        console.log('Extracted video ID:', videoId);
      }
    }
  }
  
  // Check for transmuxer-related functions in the global scope
  const potentialTransmuxerObjects = [
    'transmuxer',
    'Transmuxer',
    'updateTransmuxerAndRequestSegment_',
    'loadSegment_',
    'fillBuffer_'
  ];
  
  console.log('Checking for transmuxer objects/functions:');
  for (const obj of potentialTransmuxerObjects) {
    if (window[obj]) {
      console.log(`  ${obj} found in global scope`);
    }
  }
  
  // Check for specific script includes
  const allScripts = document.querySelectorAll('script');
  const streamingRelatedScripts = Array.from(allScripts).filter(script => 
    script.src && (
      script.src.includes('main.a286f98b.js') || 
      script.src.includes('hls.js') || 
      script.src.includes('dash.js') || 
      script.src.includes('cloudfront.net')
    )
  );
  
  console.log('Streaming-related scripts found:', streamingRelatedScripts.length);
  streamingRelatedScripts.forEach((script, i) => {
    console.log(`  Script #${i + 1}:`, script.src);
  });
  
  // Find all video elements
  const videoElements = document.querySelectorAll('video');
  console.log('Video elements found:', videoElements.length);
  
  // List all video elements with their properties
  videoElements.forEach((video, index) => {
    console.log(`Video #${index + 1}:`, {
      element: video,
      classes: video.className,
      src: video.src || video.currentSrc,
      duration: video.duration,
      currentTime: video.currentTime,
      paused: video.paused,
      controls: video.controls,
      width: video.videoWidth,
      height: video.videoHeight,
      parent: video.parentElement?.tagName,
      parentClasses: video.parentElement?.className
    });
    
    // Check for blob URL specifically
    if (video.src && video.src.startsWith('blob:')) {
      console.log(`Video #${index + 1} has blob URL:`, video.src);
      
      // Log all source elements
      const sources = video.querySelectorAll('source');
      if (sources.length > 0) {
        console.log(`Video #${index + 1} has ${sources.length} source elements:`);
        Array.from(sources).forEach((source, i) => {
          console.log(`  Source #${i + 1}:`, source.src);
        });
      }
    }
  });
  
  // Look for VideoJS specific elements
  const vjsElements = document.querySelectorAll('.video-js, [data-vjs-player], .vjs-tech');
  console.log('VideoJS-related elements found:', vjsElements.length);
  
  vjsElements.forEach((el, index) => {
    console.log(`VideoJS element #${index + 1}:`, {
      element: el,
      id: el.id,
      classes: el.className,
      tagName: el.tagName,
      attributes: Array.from(el.attributes).map(attr => `${attr.name}="${attr.value}"`).join(', ')
    });
    
    // Try to get video from this element
    const videoInElement = el.querySelector('video');
    if (videoInElement) {
      console.log(`VideoJS element #${index + 1} contains video:`, {
        src: videoInElement.src || videoInElement.currentSrc,
        duration: videoInElement.duration,
        currentTime: videoInElement.currentTime
      });
    }
  });
  
  // Try to access any player API
  const playerInstance = getVideoJSInstance();
  console.log('Player instance found:', playerInstance ? 'Yes' : 'No');
  
  if (playerInstance) {
    console.log('Player methods available:', Object.keys(playerInstance).filter(key => typeof playerInstance[key] === 'function'));
    
    // Try to get more detailed information about the player
    try {
      if (typeof playerInstance.currentSrc === 'function') {
        console.log('Current source:', playerInstance.currentSrc());
      }
      if (typeof playerInstance.duration === 'function') {
        console.log('Duration:', playerInstance.duration());
      }
      if (typeof playerInstance.currentTime === 'function') {
        console.log('Current time:', playerInstance.currentTime());
      }
      if (typeof playerInstance.paused === 'function') {
        console.log('Paused:', playerInstance.paused());
      }
      
      // Check for tech info
      if (playerInstance.tech && playerInstance.tech()) {
        console.log('Tech name:', playerInstance.tech().name_);
        console.log('Tech element:', playerInstance.tech().el());
      }
    } catch (e) {
      console.log('Error getting detailed player info:', e);
    }
  }
  
  // Look for script tags with videojs
  const vjsScripts = Array.from(allScripts).filter(script => 
    script.src && (script.src.includes('video.js') || script.src.includes('videojs'))
  );
  
  console.log('VideoJS script tags found:', vjsScripts.length);
  vjsScripts.forEach((script, index) => {
    console.log(`Script #${index + 1}:`, script.src);
  });
  
  // Check if our observers are running
  console.log('Primary video element:', primaryVideoElement ? {
    tagName: primaryVideoElement.tagName,
    src: primaryVideoElement.src || primaryVideoElement.currentSrc,
    isOlympusPlayer: isOlympusPlayer
  } : 'None');
  console.log('Video observer active:', videoObserver ? 'Yes' : 'No');
  
  // Check for inline script that might initialize videojs
  const inlineScripts = Array.from(allScripts).filter(script => 
    !script.src && (script.textContent.includes('videojs') || script.textContent.includes('video.js'))
  );
  
  if (inlineScripts.length > 0) {
    console.log('Found inline scripts that might initialize VideoJS:', inlineScripts.length);
    inlineScripts.forEach((script, i) => {
      console.log(`Inline script #${i + 1} first 100 chars:`, script.textContent.substring(0, 100).replace(/\s+/g, ' '));
    });
  }
  
  // Check for our stored metadata
  console.log('Initial video metadata stored:', window._initialVideoMetadata ? 'Yes' : 'No');
  if (window._initialVideoMetadata) {
    console.log('Stored metadata:', window._initialVideoMetadata);
  }
  
  return 'Debug information logged to console';
}

// Function to try different play/pause approaches for debugging
function tryVideoControls() {
  console.log('=== Trying various video control methods ===');
  
  // Find all video elements
  const videos = document.querySelectorAll('video');
  console.log(`Found ${videos.length} video elements`);
  
  // Method 5: Try Wistia API specifically
  setTimeout(() => {
    console.log('5. Checking for Wistia-specific controls');
    
    if (typeof window.Wistia !== 'undefined' && window.Wistia.api) {
      console.log('  Found global Wistia API');
      
      try {
        const wistiaVideos = window.Wistia.api.all();
        console.log(`  Found ${wistiaVideos.length} videos via Wistia API`);
        
        if (wistiaVideos.length > 0) {
          const video = wistiaVideos[0];
          console.log(`  Testing controls on Wistia video: ${video.hashedId()}`);
          
          // Try play
          console.log('  Calling video.play()');
          video.play();
          
          // Wait and then try pause
          setTimeout(() => {
            console.log('  Calling video.pause()');
            video.pause();
            
            // Try seeking
            setTimeout(() => {
              if (video.duration && typeof video.duration === 'function') {
                const midpoint = video.duration() / 2;
                console.log(`  Seeking to midpoint: ${midpoint}s`);
                video.time(midpoint);
              }
            }, 1000);
          }, 2000);
        }
      } catch (e) {
        console.log('  Error using Wistia API:', e);
      }
    } else {
      console.log('  Wistia API not available');
      
      // Look for Wistia containers
      const wistiaContainers = document.querySelectorAll('.wistia_embed, [class*="wistia_"]');
      if (wistiaContainers.length > 0) {
        console.log(`  Found ${wistiaContainers.length} Wistia containers`);
        
        // Try to find play buttons
        const playButtons = document.querySelectorAll('.w-play-button, .w-css-play-button');
        if (playButtons.length > 0) {
          console.log('  Clicking Wistia play button');
          playButtons[0].click();
        } else {
          console.log('  No Wistia play button found');
        }
      }
    }
  }, 9000);
  
  if (videos.length > 0) {
    const mainVideo = videos[0];
    
    // Method 1: Direct API call
    try {
      console.log('1. Trying direct video.play()');
      mainVideo.play()
        .then(() => console.log('  Success! video.play() worked'))
        .catch(e => console.log('  Failed:', e));
      
      // Wait 1s then pause
      setTimeout(() => {
        console.log('1b. Trying direct video.pause()');
        mainVideo.pause();
        console.log('  video.pause() called');
      }, 1000);
    } catch (e) {
      console.log('  Failed to call play/pause directly:', e);
    }
    
    // Method 2: Try to find and click play buttons
    setTimeout(() => {
      console.log('2. Trying to find and click play buttons');
      const playButtons = [
        '.vjs-play-control',
        '.vjs-big-play-button',
        '[aria-label="Play"]',
        '.play-button',
        'button[title="Play"]'
      ];
      
      let buttonFound = false;
      for (const selector of playButtons) {
        const button = document.querySelector(selector);
        if (button) {
          console.log(`  Found button: ${selector}`);
          buttonFound = true;
          button.click();
          console.log(`  Clicked ${selector}`);
          break;
        }
      }
      
      if (!buttonFound) {
        console.log('  No play buttons found');
      }
    }, 3000);
    
    // Method 3: Try VideoJS API
    setTimeout(() => {
      console.log('3. Trying VideoJS API');
      const playerInstance = getVideoJSInstance();
      
      if (playerInstance) {
        console.log('  Found player instance');
        if (typeof playerInstance.play === 'function') {
          try {
            playerInstance.play();
            console.log('  Called playerInstance.play()');
          } catch (e) {
            console.log('  Error calling play:', e);
          }
        } else {
          console.log('  No play method found on player instance');
        }
      } else {
        console.log('  No VideoJS player instance found');
      }
    }, 5000);
    
    // Method 4: Try special handling for HLS videos
    setTimeout(() => {
      console.log('4. Checking for HLS-specific controls');
      
      // Look for HLS-specific objects in the page
      if (window.Hls) {
        console.log('  Found global Hls object');
        
        // Try to find any active HLS instances
        if (window._hlsInstances || window.hls || window._hls) {
          console.log('  Found potential HLS instance');
        }
      }
      
      // Check video element again
      const videos = document.querySelectorAll('video');
      if (videos.length > 0) {
        const video = videos[0];
        console.log('  Checking if video has HLS-related properties');
        
        // Some common properties added by HLS.js
        const hlsProps = ['hls', '_hls', 'vjs', '_vjs', 'tech'];
        for (const prop of hlsProps) {
          if (video[prop]) {
            console.log(`  Found video.${prop} property`);
          }
        }
      }
    }, 7000);
  } else {
    console.log('No video elements found to test');
  }
  
  return 'Control testing initiated, check console for results';
}

// Make the debug functions available in the global scope for console access
window.debugVideoPlayer = debugVideoPlayer;
window.tryVideoControls = tryVideoControls;

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Export functions for testing (will only be used in Node.js/test environment)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    findMainVideoElement,
    findOlympusPlayer,
    extractVideoMetadata,
    extractOlympusVideoMetadata,
    getNearbyHeadings,
    detectPlatform,
    handleMessage,
    sendVideoControl
  };
}

/**
 * Extract metadata from a YouTube video
 * 
 * @param {HTMLVideoElement} videoElement - The video element to extract metadata from
 * @returns {Object} The extracted metadata
 */
function extractYouTubeVideoMetadata(videoElement) {
  console.debug('Extracting YouTube video metadata');
  
  // Create basic metadata object
  const metadata = {
    platform: 'youtube',
    title: document.title.replace(' - YouTube', ''),
    src: window.location.href,
    currentTime: videoElement.currentTime || 0,
    duration: videoElement.duration || 0,
    paused: videoElement.paused,
  };
  
  // Try to get more accurate title
  try {
    const titleElement = document.querySelector('h1.title');
    if (titleElement && titleElement.textContent) {
      metadata.title = titleElement.textContent.trim();
    }
  } catch (e) {
    console.debug('Error getting title from DOM:', e);
  }
  
  // Try to get video ID from URL
  try {
    const urlParams = new URLSearchParams(window.location.search);
    metadata.videoId = urlParams.get('v');
  } catch (e) {
    console.debug('Error extracting video ID from URL:', e);
  }
  
  // Get channel info if available
  try {
    const channelElement = document.querySelector('div#owner-text a');
    if (channelElement) {
      metadata.channel = channelElement.textContent.trim();
    }
  } catch (e) {
    console.debug('Error getting channel info:', e);
  }
  
  return metadata;
}

/**
 * Get the current video element and metadata
 * @returns {Promise<{videoElement: HTMLVideoElement, metadata: Object}>} The video element and metadata
 */
function getCurrentVideo() {
  return new Promise((resolve, reject) => {
    try {
      // Get the current platform
      const platform = detectPlatform();
      console.debug(`Current platform: ${platform}`);
      
      let videoElement = null;
      let metadata = null;
      
      if (platform === 'olympus') {
        const player = findOlympusPlayer();
        if (player && player.videoElement) {
          videoElement = player.videoElement;
          metadata = extractOlympusVideoMetadata(player);
        } else {
          reject(new Error('No Olympus video player found'));
          return;
        }
      } else if (platform === 'youtube') {
        videoElement = findMainVideoElement();
        if (videoElement) {
          metadata = extractYouTubeVideoMetadata(videoElement);
        } else {
          reject(new Error('No YouTube video element found'));
          return;
        }
      } else {
        videoElement = findMainVideoElement();
        if (videoElement) {
          metadata = {
            platform: platform || 'unknown',
            title: document.title,
            src: videoElement.src || window.location.href,
            currentTime: videoElement.currentTime || 0,
            duration: videoElement.duration || 0,
            paused: videoElement.paused,
          };
        } else {
          reject(new Error('No video element found'));
          return;
        }
      }
      
      if (!videoElement) {
        reject(new Error('No video element found'));
        return;
      }
      
      resolve({
        videoElement,
        metadata
      });
    } catch (error) {
      console.error('Error in getCurrentVideo:', error);
      reject(error);
    }
  });
} 