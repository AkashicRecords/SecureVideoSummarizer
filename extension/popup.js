// API Base URL
const API_BASE_URL = 'http://localhost:8081';

// DOM Elements
const elements = {
  // Status messages
  loading: document.getElementById('loading'),
  noVideo: document.getElementById('no-video'),
  extensionError: document.getElementById('extension-error'),
  errorMessage: document.getElementById('error-message-text'),
  videoDetected: document.getElementById('video-detected'),
  
  // Video info
  videoInfo: document.getElementById('video-info'),
  videoTitle: document.getElementById('video-title'),
  videoDuration: document.getElementById('video-duration'),
  videoWarning: document.getElementById('video-warning'),
  
  // Playback controls
  playbackControls: document.getElementById('playback-controls'),
  basicControls: document.querySelector('.basic-controls'),
  advancedControls: document.querySelector('.advanced-controls'),
  playBtn: document.getElementById('play-btn'),
  pauseBtn: document.getElementById('pause-btn'),
  seekBackBtn: document.getElementById('seek-back-btn'),
  seekForwardBtn: document.getElementById('seek-forward-btn'),
  decreaseRateBtn: document.getElementById('decrease-rate-btn'),
  increaseRateBtn: document.getElementById('increase-rate-btn'),
  playbackRateElem: document.getElementById('playback-rate'),
  
  // Options
  lengthSelect: document.getElementById('summary-length'),
  formatSelect: document.getElementById('format'),
  focusKeyPoints: document.getElementById('focus-key-points'),
  focusDetails: document.getElementById('focus-details'),
  
  // Summarize buttons
  youtubeSummarizeBtn: document.getElementById('youtube-summarize-btn'),
  olympusSummarizeBtn: document.getElementById('olympus-summarize-btn'),
  
  // Processing indicator
  processingText: document.getElementById('processing-text'),
  
  // Result section
  summaryResult: document.getElementById('summary-result'),
  
  // Utility buttons
  retryConnectionBtn: document.getElementById('retry-connection'),
  refreshContentScriptBtn: document.getElementById('refresh-content-script'),
  
  // Summary display
  summaryContent: document.getElementById('summary-content'),
  copySummaryBtn: document.getElementById('copy-summary'),
  saveSummaryBtn: document.getElementById('save-summary'),
  closeSummaryBtn: document.getElementById('close-summary'),
  summaryLength: document.getElementById('summary-length'),
};

// Application state
const currentState = {
  backendConnected: false,
  backendUrl: null,
  videoData: null,
  summaryResult: null,
  summaryOptions: {
    length: 'medium',
    format: 'paragraph',
    focusKeyPoints: true,
    focusDetails: false
  },
  popupOpen: true
};

// Initialize elements after DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('Popup DOM content loaded');
  
  // Initialize popup UI
  initializePopup();
  
  // Check if we're on an Olympus page or YouTube
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    const currentTab = tabs[0];
    const url = currentTab.url || '';
    
    // Display platform-specific UI
    if (url.includes('youtube.com')) {
      document.getElementById('platform-icon').src = 'icons/youtube.png';
      document.getElementById('platform-name').textContent = 'YouTube';
      document.getElementById('platform-specific-section').style.display = 'block';
      document.getElementById('youtube-options').style.display = 'block';
      document.getElementById('olympus-options').style.display = 'none';
      
      // Add YouTube-specific initialization
      document.getElementById('youtube-summarize-btn').addEventListener('click', function() {
        generateSummary('youtube');
      });
    } else if (url.includes('olympus') || url.match(/mygreatlearning\.com/i)) {
      document.getElementById('platform-icon').src = 'icons/olympus.png';
      document.getElementById('platform-name').textContent = 'Olympus Learning';
      document.getElementById('platform-specific-section').style.display = 'block';
      document.getElementById('youtube-options').style.display = 'none';
      document.getElementById('olympus-options').style.display = 'block';
      
      // Check if Olympus API is available
      fetch(API_BASE_URL + '/api/olympus/status')
        .then(response => response.json())
        .then(data => {
          if (data.available) {
            document.getElementById('olympus-api-status').textContent = 'Connected';
            document.getElementById('olympus-api-status').className = 'status-connected';
            // Enable Olympus-specific features
            document.getElementById('olympus-features').style.display = 'block';
          } else {
            document.getElementById('olympus-api-status').textContent = 'Disconnected';
            document.getElementById('olympus-api-status').className = 'status-error';
          }
        })
        .catch(error => {
          console.error('Error checking Olympus API:', error);
          document.getElementById('olympus-api-status').textContent = 'Error';
          document.getElementById('olympus-api-status').className = 'status-error';
        });
        
      // Add Olympus-specific initialization
      document.getElementById('olympus-summarize-btn').addEventListener('click', function() {
        generateSummary('olympus');
      });
    } else {
      // Generic video site
      document.getElementById('platform-icon').src = 'icons/video.png';
      document.getElementById('platform-name').textContent = 'Video';
      document.getElementById('platform-specific-section').style.display = 'none';
    }
  });
  
  // Add handlers for Olympus-specific buttons
  document.getElementById('capture-olympus-transcript').addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const currentTab = tabs[0];
      
      // Send message to content script to capture current video
      chrome.tabs.sendMessage(currentTab.id, {action: "getCurrentVideo"}, function(response) {
        if (response && response.success && response.platform === 'olympus') {
          // Extract transcript from the video metadata
          const transcriptData = {
            text: response.transcript || "No transcript available",
            title: response.title || "Olympus Video",
            video_id: response.videoId || response.id || "unknown",
            options: {
              max_length: parseInt(document.getElementById('summary-length').value) || 150,
              min_length: 30
            }
          };
          
          // Send to API for processing
          fetch(API_BASE_URL + '/api/olympus/capture', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(transcriptData)
          })
          .then(response => response.json())
          .then(data => {
            if (data.summary) {
              displayResults(data);
            } else {
              showError("Failed to process transcript");
            }
          })
          .catch(error => {
            console.error('Error capturing Olympus transcript:', error);
            showError("API error: " + error.message);
          });
        } else {
          showError("No Olympus video found or video not ready");
        }
      });
    });
  });
});

// Error handling utilities
const ErrorMessages = {
  NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
  TIMEOUT_ERROR: 'The request timed out. Please try again.',
  API_ERROR: 'The server encountered an error. Please try again later.',
  AUTH_ERROR: 'Authentication failed. Please check your credentials.',
  DEFAULT: 'An unexpected error occurred. Please try again.'
};

function getErrorMessage(error) {
  if (!error) return ErrorMessages.DEFAULT;
  
  if (error.type && ErrorMessages[error.type]) {
    return `${ErrorMessages[error.type]}\n${error.message || ''}`;
  }
  
  return error.message || ErrorMessages.DEFAULT;
}

// Hide summary view
function closeSummaryView() {
  console.log('Closing summary view');
  
  if (elements.summaryResult) {
    elements.summaryResult.classList.add('hidden');
  }
}

// Show/hide loading indicator
function showLoading(show = false) {
  console.log(`${show ? 'Showing' : 'Hiding'} loading indicator`);
  
  if (elements.loading) {
    elements.loading.classList.toggle('hidden', !show);
  }
  
  // When showing loading, hide other status elements
  if (show) {
    if (elements.noVideo) {
      elements.noVideo.classList.add('hidden');
    }
    
    if (elements.extensionError) {
      elements.extensionError.classList.add('hidden');
    }
  }
}

// Show/hide error message
function showError(show = false, message = null) {
  console.log(`${show ? 'Showing' : 'Hiding'} error message: ${message || 'No message'}`);
  
  if (!elements.extensionError) return;
  
  if (show) {
    elements.extensionError.classList.remove('hidden');
    
    // Update error message if provided
    if (message && elements.errorMessage) {
      if (typeof message === 'string') {
        elements.errorMessage.textContent = message;
      } else if (message.message) {
        elements.errorMessage.textContent = message.message;
      }
    }
    
    // Disable summarize button when there's an error
    if (elements.youtubeSummarizeBtn) {
      elements.youtubeSummarizeBtn.disabled = true;
    }
    if (elements.olympusSummarizeBtn) {
      elements.olympusSummarizeBtn.disabled = true;
    }
  } else {
    elements.extensionError.classList.add('hidden');
  }
}

// Show/hide no video message
function showNoVideo(show = true) {
  console.log(`${show ? 'Showing' : 'Hiding'} no video message`);
  
  if (elements.noVideo) {
    elements.noVideo.style.display = show ? 'block' : 'none';
  }
  
  // Toggle video detected UI (inverse of no video)
  if (elements.videoDetected) {
    elements.videoDetected.style.display = show ? 'none' : 'block';
  }
  
  // Hide playback controls when no video
  if (elements.playbackControls) {
    elements.playbackControls.style.display = show ? 'none' : 'block';
  }
  
  // Disable summarize button when no video
  if (elements.youtubeSummarizeBtn) {
    elements.youtubeSummarizeBtn.disabled = show;
  }
  if (elements.olympusSummarizeBtn) {
    elements.olympusSummarizeBtn.disabled = show;
  }
}

function showVideoDetected(show = true, hasWarnings = false) {
  console.log(`${show ? 'Showing' : 'Hiding'} video detected UI, hasWarnings: ${hasWarnings}`);
  
  // Toggle video detected container
  if (elements.videoDetected) {
    elements.videoDetected.style.display = show ? 'block' : 'none';
  }
  
  // Toggle no video message (inverse of video detected)
  if (elements.noVideo) {
    elements.noVideo.style.display = show ? 'none' : 'block';
  }
  
  // Toggle playback controls
  if (elements.playbackControls) {
    elements.playbackControls.style.display = show ? 'block' : 'none';
  }
  
  // Enable or disable the summarize button based on video presence
  if (elements.youtubeSummarizeBtn) {
    // Always enable the summarize button if a video is detected,
    // even if it has warnings (like being VideoJS or in an iframe)
    elements.youtubeSummarizeBtn.disabled = !show;
  }
  if (elements.olympusSummarizeBtn) {
    elements.olympusSummarizeBtn.disabled = !show;
  }
  
  // Show warning if video has limitations
  if (show && hasWarnings && elements.videoWarning) {
    elements.videoWarning.style.display = 'block';
  }
}

// Initialize the popup UI
function initializePopup() {
  console.log('Initializing popup UI');
  
  // Reset UI state
  resetUIState();
  
  // Set the default state for buttons
  if (elements.youtubeSummarizeBtn) {
    elements.youtubeSummarizeBtn.disabled = true;
  }
  if (elements.olympusSummarizeBtn) {
    elements.olympusSummarizeBtn.disabled = true;
  }
  
  // Show loading initially
  showLoading(true);
  
  // First check backend connection to ensure server is running
  checkBackendConnection()
    .then(() => {
      console.log('Backend connection successful, checking for video');
      // Hide any previous error messages
      showError(false);
      
      // Check for video on the current page
      return checkForVideo();
    })
    .catch(error => {
      console.error('Error during initialization:', error);
      showLoading(false);
      showError(true, error.message);
    });
    
  // Setup event listeners
  setupEventListeners();
  
  console.log('Popup initialization complete');
}

// Reset the UI state before checking conditions
function resetUIState() {
  console.log('Resetting UI state');
  
  // Reset all status messages
  showLoading(false);
  showNoVideo(false);
  showError(false);
  
  // Hide any existing warnings
  if (elements.videoWarning) {
    elements.videoWarning.style.display = 'none';
    elements.videoWarning.textContent = '';
  }
  
  // Reset video detected state
  if (elements.videoDetected) {
    elements.videoDetected.style.display = 'none';
  }
  
  // Clear video information
  if (elements.videoTitle) {
    elements.videoTitle.textContent = 'Video detected';
  }
  
  if (elements.videoDuration) {
    elements.videoDuration.textContent = 'Unknown';
  }
  
  // Remove any platform badges
  const platformBadges = document.querySelectorAll('.platform-badge');
  platformBadges.forEach(badge => badge.remove());
  
  // Remove any info text elements added dynamically
  const infoTexts = document.querySelectorAll('.info-text');
  infoTexts.forEach(info => info.remove());
  
  // Hide summary result
  if (elements.summaryResult) {
    elements.summaryResult.classList.add('hidden');
  }
  
  // Reset playback controls visibility
  if (elements.playbackControls) {
    elements.playbackControls.style.display = 'none';
  }
  
  if (elements.basicControls) {
    elements.basicControls.style.display = 'flex';
  }
  
  if (elements.advancedControls) {
    elements.advancedControls.style.display = 'flex';
  }
  
  // Reset current state
  currentState.videoData = null;
  currentState.summaryResult = null;
  
  console.log('UI state reset complete');
}

// Check backend connection
function checkBackendConnection() {
  console.log('Checking backend connection');
  
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: 'checkConnection' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error checking backend connection:', chrome.runtime.lastError);
        currentState.backendConnected = false;
        showError(true, 'Failed to connect to extension backend');
        reject(new Error('Failed to connect to extension backend'));
        return;
      }
      
      if (!response) {
        console.error('Empty response from background script');
        currentState.backendConnected = false;
        showError(true, 'No response from extension backend');
        reject(new Error('No response from extension backend'));
        return;
      }
      
      console.log('Backend connection response:', response);
      
      if (response.connected) {
        console.log('Backend connection successful');
        currentState.backendConnected = true;
        currentState.backendUrl = API_BASE_URL;
        
        // Hide error message if it was showing
        showError(false);
        
        resolve(true);
      } else {
        console.error('Backend connection failed:', response.error);
        currentState.backendConnected = false;
        
        // Show error with specific message
        const errorMessage = response.error || 'Unable to connect to backend service';
        showError(true, errorMessage);
        
        reject(new Error(errorMessage));
      }
    });
  });
}

// Get current active tab
function getCurrentTab() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (chrome.runtime.lastError) {
        console.error('Error getting current tab:', chrome.runtime.lastError);
        reject(new Error('Failed to get current tab'));
        return;
      }
      
      if (!tabs || tabs.length === 0) {
        console.error('No active tab found');
        reject(new Error('No active tab found'));
        return;
      }
      
      resolve(tabs[0]);
    });
  });
}

// Check for video in the current tab
async function checkForVideo() {
  console.log('Checking for video on current page');
  
  return getCurrentTab()
    .then(tab => {
      return new Promise((resolve, reject) => {
        // First try to inject the content script if needed
        injectContentScriptIfNeeded(tab)
          .then(() => {
            // Send message to content script
            chrome.tabs.sendMessage(tab.id, { action: 'getCurrentVideo' }, (response) => {
              if (chrome.runtime.lastError) {
                console.error('Error getting video:', chrome.runtime.lastError.message);
                showLoading(false);
                showNoVideo(true);
                reject(new Error(`Content script communication error: ${chrome.runtime.lastError.message}`));
                return;
              }
              
              console.log('Video check response:', response);
              
              if (!response) {
                console.error('Empty response from content script');
                showLoading(false);
                showNoVideo(true);
                reject(new Error('No response from content script'));
                return;
              }
              
              // Hide loading indicator
              showLoading(false);
              
              if (response.success && response.videoData) {
                // Store video data
                currentState.videoData = response.videoData;
                
                // Check if response includes warnings
                const hasWarnings = response.warning || 
                                  response.videoData.isVideoJS || 
                                  response.videoData.isVirtual || 
                                  response.videoData.inIframe;
                
                // Show video detected UI
                showVideoDetected(true, hasWarnings);
                
                // Update video info in UI
                updateVideoInfo(response.videoData);
                
                resolve(response.videoData);
              } else {
                showNoVideo(true);
                
                // Disable summarize button
                if (elements.youtubeSummarizeBtn) {
                  elements.youtubeSummarizeBtn.disabled = true;
                }
                if (elements.olympusSummarizeBtn) {
                  elements.olympusSummarizeBtn.disabled = true;
                }
                
                reject(new Error(response.error || 'No video found on page'));
              }
            });
          })
          .catch(error => {
            console.error('Error injecting content script:', error);
            showLoading(false);
            showNoVideo(true);
            reject(error);
          });
      });
    });
}

// Function to inject the content script if it's not already loaded
async function injectContentScriptIfNeeded(tab, forceReinject = false) {
  return new Promise(async (resolve, reject) => {
    try {
      // If force reinject is true, skip the ping and inject directly
      if (!forceReinject) {
        // First try to ping the content script to see if it's already loaded
        try {
          const response = await chrome.tabs.sendMessage(tab.id, { action: 'ping' });
          if (response && response.status === 'ok') {
            console.log('Content script is already loaded');
            return resolve(); // Content script is already loaded
          }
        } catch (error) {
          console.log('Content script ping failed, will try to inject:', error);
          // Continue with injection if ping fails
        }
      }
      
      // Inject the content script
      console.log('Injecting content script...');
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
      
      console.log('Content script injected, waiting for it to initialize...');
      
      // Give the content script a moment to initialize
      setTimeout(async () => {
        try {
          const response = await chrome.tabs.sendMessage(tab.id, { action: 'ping' });
          if (response && response.status === 'ok') {
            console.log('Content script is now active');
            resolve();
          } else {
            reject(new Error('Content script did not respond correctly after injection'));
          }
        } catch (error) {
          reject(new Error('Content script failed to initialize: ' + error.message));
        }
      }, 500);
      
    } catch (error) {
      reject(new Error('Failed to inject content script: ' + error.message));
    }
  });
}

// Update video information in the UI
function updateVideoInfo(videoData) {
  if (!videoData || !elements.videoTitle || !elements.videoDuration || !elements.videoWarning) return;
  
  console.log('Updating video info with data:', videoData);
  
  // Set title (truncate if too long)
  const title = videoData.title || 'Untitled Video';
  elements.videoTitle.textContent = title.length > 30 ? title.substring(0, 27) + '...' : title;
  
  // Set duration
  const duration = videoData.duration || 0;
  const minutes = Math.floor(duration / 60);
  const seconds = Math.floor(duration % 60);
  elements.videoDuration.textContent = duration ? `${minutes}:${seconds < 10 ? '0' : ''}${seconds}` : 'Unknown';
  
  // Remove any existing platform badges
  const existingBadge = document.querySelector('.platform-badge');
  if (existingBadge) {
    existingBadge.remove();
  }
  
  // Reset any special styling
  elements.videoTitle.classList.remove('olympus-title');
  
  // Get platform-specific option containers
  const youtubeOptions = document.getElementById('youtube-options');
  const olympusOptions = document.getElementById('olympus-options');
  
  // Show the correct platform options
  if (videoData.platform === 'youtube') {
    if (youtubeOptions) youtubeOptions.style.display = 'block';
    if (olympusOptions) olympusOptions.style.display = 'none';
    
    // Add YouTube platform badge
    const badge = document.createElement('span');
    badge.className = 'platform-badge youtube-badge';
    badge.textContent = 'YouTube';
    elements.videoInfo.insertBefore(badge, elements.videoTitle);
  } 
  else if (videoData.isVideoJS || videoData.platform === 'olympus') {
    // Show Olympus options, hide YouTube options
    if (youtubeOptions) youtubeOptions.style.display = 'none';
    if (olympusOptions) olympusOptions.style.display = 'block';
    
    // Add Olympus platform badge
    const badge = document.createElement('span');
    badge.className = 'platform-badge olympus-badge';
    badge.textContent = 'Olympus';
    elements.videoInfo.insertBefore(badge, elements.videoTitle);
    
    // Add special styling for Olympus
    elements.videoTitle.classList.add('olympus-title');
    
    // Add warning for VideoJS limited controls
    elements.videoWarning.textContent = 'Olympus VideoJS player detected. Limited playback control available.';
    elements.videoWarning.className = 'warning-text olympus-warning';
    elements.videoWarning.style.display = 'block';
    
    // Add info message about summarizing
    if (!document.querySelector('.info-text')) {
      const infoText = document.createElement('div');
      infoText.className = 'info-text';
      infoText.textContent = 'Summary can still be generated even with limited controls.';
      elements.videoInfo.appendChild(infoText);
    }
    
    // Show Olympus features if available
    const olympusFeatures = document.getElementById('olympus-features');
    if (olympusFeatures) {
      olympusFeatures.style.display = 'block';
    }
    
    // Enable only basic controls for VideoJS
    if (elements.playBtn) elements.playBtn.disabled = false;
    if (elements.pauseBtn) elements.pauseBtn.disabled = false;
    if (elements.seekBackBtn) elements.seekBackBtn.disabled = true;
    if (elements.seekForwardBtn) elements.seekForwardBtn.disabled = true;
    if (elements.decreaseRateBtn) elements.decreaseRateBtn.disabled = true;
    if (elements.increaseRateBtn) elements.increaseRateBtn.disabled = true;
  }
  // Generic/other video sources
  else {
    // For other video platforms, default to YouTube options
    if (youtubeOptions) youtubeOptions.style.display = 'block';
    if (olympusOptions) olympusOptions.style.display = 'none';
    
    // Add generic platform badge
    const badge = document.createElement('span');
    badge.className = 'platform-badge';
    badge.textContent = videoData.platform || 'Video';
    elements.videoInfo.insertBefore(badge, elements.videoTitle);
  }
  
  // Check if video is in iframe or is a virtual video
  if (videoData.inIframe) {
    elements.videoWarning.textContent = 'Video is in an iframe. Limited playback control available.';
    elements.videoWarning.className = 'warning-text';
    elements.videoWarning.style.display = 'block';
    disablePlaybackControls();
  } else if (videoData.isVirtualVideo || videoData.isVirtual) {
    elements.videoWarning.textContent = 'This is a direct video source. Limited playback control available.';
    elements.videoWarning.className = 'warning-text';
    elements.videoWarning.style.display = 'block';
    disablePlaybackControls();
  } else if (!videoData.isVideoJS && videoData.platform !== 'olympus') {
    // Standard video - clear warnings and enable controls
    elements.videoWarning.style.display = 'none';
    enablePlaybackControls();
  }
  
  // Update playback rate display
  if (elements.playbackRateElem) {
    const rate = videoData.playbackRate || 1;
    elements.playbackRateElem.textContent = `${rate.toFixed(1)}x`;
  }
  
  // Always show playback controls container when video is detected
  if (elements.playbackControls) {
    elements.playbackControls.style.display = 'block';
  }
  
  // Toggle visibility of specific controls based on player type
  toggleVideoControlsVisibility(videoData);
}

// Helper function to show/hide certain controls based on player capabilities
function toggleVideoControlsVisibility(videoData) {
  const isLimitedPlayer = videoData.isVideoJS || videoData.isVirtual || videoData.inIframe || videoData.platform === 'olympus';
  
  // Get container for advanced controls (seek and rate)
  const advancedControls = document.querySelector('.advanced-controls');
  if (advancedControls) {
    advancedControls.style.display = isLimitedPlayer ? 'none' : 'flex';
  }
  
  // Always keep basic controls visible
  const basicControls = document.querySelector('.basic-controls');
  if (basicControls) {
    basicControls.style.display = 'flex';
  }
}

function disablePlaybackControls() {
  if (!elements.playBtn || !elements.pauseBtn || !elements.seekBackBtn || 
      !elements.seekForwardBtn || !elements.decreaseRateBtn || !elements.increaseRateBtn) return;
  
  elements.playBtn.disabled = true;
  elements.pauseBtn.disabled = true;
  elements.seekBackBtn.disabled = true;
  elements.seekForwardBtn.disabled = true;
  elements.decreaseRateBtn.disabled = true;
  elements.increaseRateBtn.disabled = true;
}

function enablePlaybackControls() {
  if (!elements.playBtn || !elements.pauseBtn || !elements.seekBackBtn || 
      !elements.seekForwardBtn || !elements.decreaseRateBtn || !elements.increaseRateBtn) return;
  
  elements.playBtn.disabled = false;
  elements.pauseBtn.disabled = false;
  elements.seekBackBtn.disabled = false;
  elements.seekForwardBtn.disabled = false;
  elements.decreaseRateBtn.disabled = false;
  elements.increaseRateBtn.disabled = false;
}

// Video control functions
function sendVideoControl(action, value = null) {
  if (!currentState.videoData) {
    console.error('No video data available, cannot send control');
    return;
  }
  
  // Disable control buttons while action is in progress
  const controlButtons = document.querySelectorAll('.control-btn');
  controlButtons.forEach(btn => {
    btn.disabled = true;
  });
  
  getCurrentTab().then(tab => {
    const message = { action: 'controlVideo', control: action };
    if (value !== null) {
      if (action === 'seek') {
        message.time = value;
      } else if (action === 'setPlaybackRate') {
        message.rate = value;
      }
    }
    
    chrome.tabs.sendMessage(tab.id, message, (response) => {
      // Re-enable buttons
      controlButtons.forEach(btn => {
        btn.disabled = false;
      });
      
      if (chrome.runtime.lastError) {
        console.error('Error sending video control:', chrome.runtime.lastError);
        showErrorMessage('Failed to control video playback. Try refreshing the page.');
        return;
      }
      
      if (!response) {
        console.error('Empty response from content script');
        showErrorMessage('No response from content script. Try refreshing the page.');
        return;
      }
      
      console.log('Video control response:', response);
      
      if (response.success) {
        // Update UI with the new video data
        if (response.videoData) {
          currentState.videoData = response.videoData;
          updateVideoInfo(response.videoData);
        }
        
        // Check for warnings specific to VideoJS/Olympus player
        if (response.warning) {
          console.warn('Control warning:', response.warning);
          // Show the warning if not already visible
          if (elements.videoWarning && elements.videoWarning.style.display !== 'block') {
            elements.videoWarning.textContent = response.warning;
            elements.videoWarning.style.display = 'block';
          }
        }
      } else {
        // Handle errors
        console.error('Video control error:', response.error);
        
        // Check if this is a VideoJS control error
        if (response.videoData && (response.videoData.isVideoJS || response.videoData.platform === 'olympus')) {
          // For VideoJS errors, show a more specific error message
          showErrorMessage('Limited control available for this video player.', 3000);
          
          // Still update the video data if we have it
          currentState.videoData = response.videoData;
          updateVideoInfo(response.videoData);
        } else {
          // Generic error
          showErrorMessage(response.error || 'Failed to control video', 3000);
        }
      }
    });
  }).catch(error => {
    console.error('Error getting current tab:', error);
    showErrorMessage('Failed to connect to current tab');
    
    // Re-enable buttons
    controlButtons.forEach(btn => {
      btn.disabled = false;
    });
  });
}

// Open main application
function openMainApplication() {
  chrome.tabs.create({ url: 'http://localhost:8080/' });
}

// Prevent popup from closing when clicking inside it
document.addEventListener('click', (e) => {
  e.stopPropagation();
});

// Handle popup window focus
window.addEventListener('focus', () => {
  currentState.popupOpen = true;
  console.log('Popup window focused');
});

window.addEventListener('blur', () => {
  if (!currentState.summarizing) {
    currentState.popupOpen = false;
    console.log('Popup window blurred');
  }
});

// Function to control video playback
async function controlVideo(action, value = null) {
  if (!currentState.videoData) {
    console.error('No video data available for control');
    return false;
  }
  
  try {
    const tab = await getCurrentTab();
    if (!tab) {
      console.error('No active tab found');
      return false;
    }
    
    return new Promise((resolve) => {
      chrome.tabs.sendMessage(tab.id, { 
        action: 'controlVideo',
        control: action,
        value: value
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending control command:', chrome.runtime.lastError);
          resolve(false);
          return;
        }
        
        if (response && response.success) {
          if (response.videoData) {
            currentState.videoData = response.videoData;
            updateVideoInfo(response.videoData);
          }
          resolve(true);
        } else {
          console.error('Video control failed:', response?.error || 'Unknown error');
          resolve(false);
        }
      });
    });
  } catch (error) {
    console.error('Error controlling video:', error);
    return false;
  }
}

// Export functions for testing (will only be used in Node.js/test environment)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    checkBackendConnection,
    showVideoDetected,
    showNoVideo,
    showError,
    closeSummaryView,
    showLoading,
    updateVideoInfo,
    getCurrentTab,
    checkForVideo,
    controlVideo,
    summarizeVideo,
    checkSummaryStatus,
    saveSummary,
    initializePopup
  };
}

// Set up event listeners for UI interactions
function setupEventListeners() {
  console.log('Setting up event listeners');
  
  // Retry connection button
  if (elements.retryConnectionBtn) {
    elements.retryConnectionBtn.addEventListener('click', () => {
      console.log('Retrying backend connection');
      showLoading(true);
      showError(false);
      
      checkBackendConnection()
        .then(() => {
          console.log('Backend connection successful on retry');
          showError(false);
          return checkForVideo();
        })
        .catch(error => {
          console.error('Error on retry:', error);
          showLoading(false);
          showError(true, error.message);
        });
    });
  }
  
  // Settings link
  const settingsLink = document.getElementById('settings-link');
  if (settingsLink) {
    settingsLink.addEventListener('click', (e) => {
      e.preventDefault();
      console.log('Settings link clicked');
      
      // Create settings modal or open settings page
      const appUrl = currentState.backendUrl || 'http://localhost:8080';
      chrome.tabs.create({ url: `${appUrl}/settings` });
    });
  }
  
  // Summarize button
  if (elements.youtubeSummarizeBtn) {
    elements.youtubeSummarizeBtn.addEventListener('click', () => {
      if (!currentState.videoData) {
        console.error('No video data available');
        return;
      }
      
      console.log('Summarize button clicked');
      generateSummary('youtube');
    });
  }
  
  if (elements.olympusSummarizeBtn) {
    elements.olympusSummarizeBtn.addEventListener('click', () => {
      if (!currentState.videoData) {
        console.error('No video data available');
        return;
      }
      
      console.log('Summarize button clicked');
      generateSummary('olympus');
    });
  }
  
  // Open app button
  if (elements.openAppBtn) {
    elements.openAppBtn.addEventListener('click', () => {
      console.log('Open app button clicked');
      
      // Get the base URL from backend connection
      const appUrl = currentState.backendUrl || 'http://localhost:8080';
      chrome.tabs.create({ url: appUrl });
    });
  }
  
  // Video playback control buttons
  if (elements.playBtn) {
    elements.playBtn.addEventListener('click', () => {
      console.log('Play button clicked');
      sendVideoControl('play');
    });
  }
  
  if (elements.pauseBtn) {
    elements.pauseBtn.addEventListener('click', () => {
      console.log('Pause button clicked');
      sendVideoControl('pause');
    });
  }
  
  if (elements.seekBackBtn) {
    elements.seekBackBtn.addEventListener('click', () => {
      if (!currentState.videoData) return;
      
      console.log('Seek back button clicked');
      const currentTime = currentState.videoData.currentTime || 0;
      const newTime = Math.max(0, currentTime - 10);
      sendVideoControl('seek', newTime);
    });
  }
  
  if (elements.seekForwardBtn) {
    elements.seekForwardBtn.addEventListener('click', () => {
      if (!currentState.videoData) return;
      
      console.log('Seek forward button clicked');
      const currentTime = currentState.videoData.currentTime || 0;
      const duration = currentState.videoData.duration || 0;
      const newTime = Math.min(duration, currentTime + 10);
      sendVideoControl('seek', newTime);
    });
  }
  
  if (elements.decreaseRateBtn) {
    elements.decreaseRateBtn.addEventListener('click', () => {
      if (!currentState.videoData) return;
      
      console.log('Decrease rate button clicked');
      const currentRate = currentState.videoData.playbackRate || 1;
      const newRate = Math.max(0.5, currentRate - 0.25);
      sendVideoControl('setPlaybackRate', newRate);
    });
  }
  
  if (elements.increaseRateBtn) {
    elements.increaseRateBtn.addEventListener('click', () => {
      if (!currentState.videoData) return;
      
      console.log('Increase rate button clicked');
      const currentRate = currentState.videoData.playbackRate || 1;
      const newRate = Math.min(2, currentRate + 0.25);
      sendVideoControl('setPlaybackRate', newRate);
    });
  }
  
  // Summary result actions
  if (elements.copySummaryBtn) {
    elements.copySummaryBtn.addEventListener('click', () => {
      if (!currentState.summaryResult) return;
      
      console.log('Copy summary button clicked');
      navigator.clipboard.writeText(currentState.summaryResult)
        .then(() => {
          console.log('Summary copied to clipboard');
          
          // Provide feedback
          const originalText = elements.copySummaryBtn.textContent;
          elements.copySummaryBtn.textContent = 'Copied!';
          setTimeout(() => {
            elements.copySummaryBtn.textContent = originalText;
          }, 2000);
        })
        .catch(err => {
          console.error('Failed to copy text:', err);
        });
    });
  }
  
  if (elements.closeSummaryBtn) {
    elements.closeSummaryBtn.addEventListener('click', () => {
      console.log('Close summary button clicked');
      closeSummaryView();
    });
  }
  
  if (elements.saveSummaryBtn) {
    elements.saveSummaryBtn.addEventListener('click', () => {
      if (!currentState.summaryResult) return;
      
      console.log('Save summary button clicked');
      // Create a download link
      const blob = new Blob([currentState.summaryResult], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `summary-${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
    });
  }
  
  // Add event listener for refresh content script button
  elements.refreshContentScriptBtn.addEventListener('click', async () => {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const currentTab = tabs[0];
    
    setStatus('loading', 'Reinjecting content script...');
    
    try {
      await injectContentScriptIfNeeded(currentTab, true); // Force reinject
      console.log('Content script reinjected successfully');
      setStatus('success', 'Content script refreshed successfully');
      setTimeout(() => {
        checkForVideo(); // Try to detect video again
      }, 500);
    } catch (error) {
      console.error('Failed to reinject content script:', error);
      showError('Failed to refresh content script: ' + error.message);
    }
  });
  
  console.log('Event listeners setup complete');
}

// Generate summary for the current video
function generateSummary(platform = 'youtube') {
  if (!currentState.videoData) {
    console.error('No video data available');
    showError(true, 'No video data available. Try refreshing the content script.');
    return;
  }
  
  console.log('Generating summary for platform:', platform);
  
  // Get summary options
  const options = {
    length: elements.lengthSelect ? elements.lengthSelect.value : '150',
    format: elements.formatSelect ? elements.formatSelect.value : 'paragraph',
    focusKeyPoints: elements.focusKeyPoints ? elements.focusKeyPoints.checked : true,
    focusDetails: elements.focusDetails ? elements.focusDetails.checked : false,
    platform: platform // Include the platform in options
  };
  
  // Save the current options
  currentState.summaryOptions = options;
  
  // Show loading indicator with specific message
  showLoading(true);
  if (elements.processingText) {
    elements.processingText.textContent = `Processing ${platform} video...`;
  }
  
  // Create data for the summary request
  const summaryData = {
    videoData: currentState.videoData,
    options: options
  };
  
  console.log('Summary request data:', summaryData);
  
  // Make request to background script to generate summary
  chrome.runtime.sendMessage({
    type: 'generateSummary',
    data: summaryData
  }, (response) => {
    // Hide loading indicator
    showLoading(false);
    
    if (chrome.runtime.lastError) {
      console.error('Error generating summary:', chrome.runtime.lastError);
      showError(true, 'Error generating summary: ' + chrome.runtime.lastError.message);
      return;
    }
    
    console.log('Summary response:', response);
    
    if (!response) {
      showError(true, 'No response from background script');
      return;
    }
    
    if (response.error) {
      console.error('Summary generation error:', response.error);
      showError(true, response.error);
      return;
    }
    
    // Store the summary result
    currentState.summaryResult = response.summary;
    
    // Display the summary
    displaySummaryResult(response.summary);
  });
}

// Display the generated summary
function displaySummary(summary) {
  console.log('Displaying summary');
  
  if (!elements.summaryResult || !elements.summaryContent) return;
  
  // Format the summary text (replace newlines with <br> tags)
  const formattedSummary = summary.replace(/\n/g, '<br>');
  
  // Set the summary content
  elements.summaryContent.innerHTML = formattedSummary;
  
  // Show the summary container
  elements.summaryResult.classList.remove('hidden');
}

function displayResults(data) {
  // Hide loading indicators
  document.getElementById('loading-indicator').style.display = 'none';
  document.getElementById('processing-text').style.display = 'none';
  
  // Show results section
  const resultsSection = document.getElementById('results-section');
  resultsSection.style.display = 'block';
  
  // Display the summary
  const summaryElement = document.getElementById('summary-text');
  summaryElement.textContent = data.summary;
  
  // Display video title if available
  if (data.title) {
    document.getElementById('video-title').textContent = data.title;
    document.getElementById('video-title-section').style.display = 'block';
  }
  
  // Display source information
  let sourceText = 'Source: ';
  if (data.source === 'youtube') {
    sourceText += 'YouTube';
  } else if (data.source === 'olympus') {
    sourceText += 'Olympus Learning Platform';
  } else {
    sourceText += data.source || 'Unknown';
  }
  document.getElementById('source-info').textContent = sourceText;
  
  // Display timestamp
  if (data.timestamp) {
    const date = new Date(data.timestamp * 1000);
    document.getElementById('timestamp').textContent = 'Processed: ' + date.toLocaleString();
  }
  
  // Enable copy button
  document.getElementById('copy-summary').disabled = false;
}

// Add event listeners for platform-specific buttons
document.getElementById('youtube-summarize-btn').addEventListener('click', function() {
  // Handle YouTube summarization
  console.log('YouTube summarize button clicked');
  startSummarizing();
});

document.getElementById('capture-olympus-transcript').addEventListener('click', function() {
  // Handle Olympus summarization
  console.log('Olympus capture button clicked');
  startSummarizing();
});

// Function to get options for summarization
function getSummaryOptions() {
  const elements = initializeElements();
  return {
    length: elements.summaryLength.value,
    format: elements.format.value,
    focus: getFocusAreas()
  };
}

// Process Olympus video through specialized endpoint
function processOlympusVideo(videoData, options) {
  console.log('Processing Olympus video:', videoData);
  
  // Extract data needed for API
  const requestData = {
    title: videoData.title || "Olympus Video",
    video_id: videoData.videoId || videoData.id || "unknown",
    transcript: videoData.transcript || null,
    url: videoData.src || window.location.href,
    options: {
      max_length: parseInt(options.length) || 150,
      min_length: 30,
      focus_key_points: options.focusKeyPoints,
      focus_details: options.focusDetails,
      format: options.format
    }
  };
  
  // Send to Olympus API endpoint
  fetch(API_BASE_URL + '/api/olympus/capture', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestData)
  })
  .then(response => response.json())
  .then(data => {
    showLoading(false);
    
    if (data.summary) {
      // Store the summary result
      currentState.summaryResult = data.summary;
      
      // Display the summary
      displaySummary(data.summary);
    } else {
      showError(true, data.error || 'Failed to process Olympus video');
    }
  })
  .catch(error => {
    console.error('Error processing Olympus video:', error);
    showLoading(false);
    showError(true, "API error: " + error.message);
  });
}

// Process standard summary request via background script
function processSummaryRequest(videoData, options) {
  console.log('Processing standard summary request:', videoData);
  
  // Determine if we're dealing with a VideoJS player
  const isVideoJS = videoData.isVideoJS || 
                    videoData.platform === 'olympus';
  
  // Send request to background script
  chrome.runtime.sendMessage({
    action: 'generateSummary',
    videoData: videoData,
    options: options,
    isVideoJS: isVideoJS
  }, (response) => {
    // Hide loading indicator
    showLoading(false);
    
    if (chrome.runtime.lastError) {
      console.error('Error generating summary:', chrome.runtime.lastError);
      showError(true, 'Failed to generate summary. Please try again.');
      return;
    }
    
    if (!response) {
      console.error('Empty response from background script');
      showError(true, 'No response from server. Please try again.');
      return;
    }
    
    console.log('Summary response:', response);
    
    if (response.success && response.summary) {
      // Store the summary result
      currentState.summaryResult = response.summary;
      
      // Display the summary
      displaySummary(response.summary);
    } else {
      // Handle error
      showError(true, response.error || 'Failed to generate summary');
    }
  });
}

// Helper function to set various status states
function setStatus(state, message = null) {
  console.log(`Setting status to ${state}:`, message);
  
  // Reset all status elements first
  showLoading(false);
  showError(false);
  showNoVideo(false);
  
  switch (state) {
    case 'loading':
      showLoading(true);
      if (message && elements.processingText) {
        elements.processingText.textContent = message;
      }
      break;
    case 'error':
      showError(true, message);
      break;
    case 'no-video':
      showNoVideo(true);
      break;
    case 'success':
      if (message) {
        // Create a temporary success notification
        const notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove it after 3 seconds
        setTimeout(() => {
          notification.classList.add('fade-out');
          setTimeout(() => notification.remove(), 500);
        }, 3000);
      }
      break;
    default:
      console.warn('Unknown status state:', state);
  }
}
