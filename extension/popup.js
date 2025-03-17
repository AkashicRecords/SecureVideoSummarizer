// DOM elements
const elements = {
  loading: document.getElementById('loading'),
  noVideo: document.getElementById('no-video'),
  videoDetected: document.getElementById('video-detected'),
  extensionError: document.getElementById('extension-error'),
  videoTitle: document.getElementById('video-title'),
  videoDuration: document.getElementById('video-duration'),
  summaryResult: document.getElementById('summary-result'),
  summaryContent: document.getElementById('summary-content'),
  
  // Buttons
  summarizeBtn: document.getElementById('summarize-btn'),
  openAppBtn: document.getElementById('open-app-btn'),
  retryConnectionBtn: document.getElementById('retry-connection'),
  copySummaryBtn: document.getElementById('copy-summary'),
  saveSummaryBtn: document.getElementById('save-summary'),
  closeSummaryBtn: document.getElementById('close-summary'),
  settingsLink: document.getElementById('settings-link'),
  
  // Options
  lengthSelect: document.getElementById('length'),
  formatSelect: document.getElementById('format'),
  focusKeyPoints: document.getElementById('focus-key-points'),
  focusDetails: document.getElementById('focus-details'),
  
  // Playback controls
  playbackSpeed: document.getElementById('playback-speed'),
  playBtn: document.getElementById('play-btn'),
  pauseBtn: document.getElementById('pause-btn'),
  seekBackBtn: document.getElementById('seek-back-btn'),
  seekForwardBtn: document.getElementById('seek-forward-btn')
};

// State
let currentState = {
  backendConnected: false,
  videoData: null,
  summarizing: false,
  summary: null
};

// Check backend connection
async function checkBackendConnection() {
  try {
    showLoading(true);
    
    const response = await fetch('http://localhost:5000/api/extension/status', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      currentState.backendConnected = true;
      console.log('Backend connected:', data);
      return true;
    } else {
      throw new Error('Backend connection failed');
    }
  } catch (error) {
    console.error('Error connecting to backend:', error);
    currentState.backendConnected = false;
    showError(true);
    return false;
  } finally {
    showLoading(false);
  }
}

// Get current active tab
async function getCurrentTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

// Check for video on the current page
async function checkForVideo() {
  try {
    const tab = await getCurrentTab();
    
    // Send message to content script to get video data
    chrome.tabs.sendMessage(tab.id, { action: 'getCurrentVideo' }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script not injected yet, inject it
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }, () => {
          // Retry after injection
          setTimeout(() => checkForVideo(), 500);
        });
        return;
      }
      
      if (response && response.success && response.videoData) {
        currentState.videoData = response.videoData;
        showVideoDetected(true);
        updateVideoInfo(response.videoData);
      } else {
        showNoVideo(true);
      }
    });
  } catch (error) {
    console.error('Error checking for video:', error);
    showNoVideo(true);
  }
}

// Update video info in UI
function updateVideoInfo(videoData) {
  if (!videoData) return;
  
  // Set video title (truncate if too long)
  const title = videoData.title || 'Unnamed Video';
  elements.videoTitle.textContent = title.length > 30 
    ? title.substring(0, 27) + '...' 
    : title;
  
  // Format duration
  if (videoData.duration) {
    const minutes = Math.floor(videoData.duration / 60);
    const seconds = Math.floor(videoData.duration % 60);
    elements.videoDuration.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
  } else {
    elements.videoDuration.textContent = 'Unknown';
  }
}

// Start summarizing the video
async function summarizeVideo() {
  if (!currentState.videoData || !currentState.backendConnected) {
    return;
  }
  
  try {
    showLoading(true);
    currentState.summarizing = true;
    
    // Get selected options
    const options = {
      length: elements.lengthSelect.value,
      format: elements.formatSelect.value,
      focus: []
    };
    
    if (elements.focusKeyPoints.checked) options.focus.push('key_points');
    if (elements.focusDetails.checked) options.focus.push('detailed');
    
    // Send message to background script to capture audio
    chrome.runtime.sendMessage({ 
      action: 'captureAudioStream',
      videoData: currentState.videoData,
      options: options
    }, async (response) => {
      if (response && response.success) {
        // Poll for summary status
        await pollForSummary();
      } else {
        throw new Error('Failed to start audio capture');
      }
    });
    
  } catch (error) {
    console.error('Error summarizing video:', error);
    showError(true);
    currentState.summarizing = false;
  } finally {
    showLoading(false);
  }
}

// Poll for summary status
async function pollForSummary() {
  let attempts = 0;
  const maxAttempts = 30; // 30 * 2 seconds = 1 minute timeout
  
  const pollInterval = setInterval(async () => {
    try {
      attempts++;
      
      if (attempts > maxAttempts) {
        clearInterval(pollInterval);
        throw new Error('Summary timeout');
      }
      
      const response = await fetch('http://localhost:5000/api/extension/summary_status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'completed' && data.summary) {
          clearInterval(pollInterval);
          currentState.summary = data.summary;
          showSummaryResult(data.summary);
          currentState.summarizing = false;
        } else if (data.status === 'error') {
          clearInterval(pollInterval);
          throw new Error(data.message || 'Summary failed');
        }
        // Otherwise keep polling
      }
    } catch (error) {
      clearInterval(pollInterval);
      console.error('Error polling for summary:', error);
      showError(true);
      currentState.summarizing = false;
    }
  }, 2000); // Poll every 2 seconds
}

// Show summary result
function showSummaryResult(summary) {
  elements.summaryContent.innerHTML = summary;
  elements.summaryResult.classList.remove('hidden');
  elements.loading.classList.add('hidden');
}

// Open main application
function openMainApplication() {
  chrome.tabs.create({ url: 'http://localhost:5000' });
}

// Copy summary to clipboard
function copySummaryToClipboard() {
  if (!currentState.summary) return;
  
  navigator.clipboard.writeText(currentState.summary)
    .then(() => {
      const originalText = elements.copySummaryBtn.textContent;
      elements.copySummaryBtn.textContent = 'Copied!';
      setTimeout(() => {
        elements.copySummaryBtn.textContent = originalText;
      }, 1500);
    })
    .catch(err => console.error('Failed to copy text:', err));
}

// Save summary
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
      const originalText = elements.saveSummaryBtn.textContent;
      elements.saveSummaryBtn.textContent = 'Saved!';
      setTimeout(() => {
        elements.saveSummaryBtn.textContent = originalText;
      }, 1500);
    } else {
      throw new Error('Failed to save summary');
    }
  } catch (error) {
    console.error('Error saving summary:', error);
    alert('Failed to save summary. Please try again.');
  }
}

// Close summary view
function closeSummaryView() {
  elements.summaryResult.classList.add('hidden');
}

// UI Helper functions
function showLoading(show) {
  elements.loading.classList.toggle('hidden', !show);
}

function showNoVideo(show) {
  elements.noVideo.classList.toggle('hidden', !show);
  elements.videoDetected.classList.toggle('hidden', show);
  elements.summarizeBtn.disabled = show;
}

function showError(show) {
  elements.extensionError.classList.toggle('hidden', !show);
}

function showVideoDetected(show) {
  elements.videoDetected.classList.toggle('hidden', !show);
  elements.noVideo.classList.toggle('hidden', show);
  elements.summarizeBtn.disabled = !show;
}

// Event Listeners
elements.summarizeBtn.addEventListener('click', summarizeVideo);
elements.openAppBtn.addEventListener('click', openMainApplication);
elements.retryConnectionBtn.addEventListener('click', checkBackendConnection);
elements.copySummaryBtn.addEventListener('click', copySummaryToClipboard);
elements.saveSummaryBtn.addEventListener('click', saveSummary);
elements.closeSummaryBtn.addEventListener('click', closeSummaryView);
elements.settingsLink.addEventListener('click', openMainApplication);

// Initialize popup
async function initializePopup() {
  const connected = await checkBackendConnection();
  if (connected) {
    await checkForVideo();
  }
}

// Start initialization when popup loads
document.addEventListener('DOMContentLoaded', initializePopup);

// Playback control functions
function changePlaybackSpeed() {
  const speed = elements.playbackSpeed.value;
  
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'controlVideo',
      control: 'setPlaybackRate',
      rate: speed
    }, function(response) {
      if (response && response.success) {
        console.log('Playback speed changed to', speed);
        // Update state if needed
        if (currentState.videoData) {
          currentState.videoData.playbackRate = parseFloat(speed);
        }
      } else {
        console.error('Failed to change playback speed:', response ? response.error : 'Unknown error');
        showError('Failed to change playback speed. Please try again.');
      }
    });
  });
}

function playVideo() {
  sendVideoControl('play');
}

function pauseVideo() {
  sendVideoControl('pause');
}

function seekVideo(seconds) {
  if (!currentState.videoData || typeof currentState.videoData.currentTime !== 'number') {
    showError('Cannot seek: video information not available');
    return;
  }
  
  const newTime = Math.max(0, currentState.videoData.currentTime + seconds);
  sendVideoControl('seek', { time: newTime });
}

function sendVideoControl(control, options = {}) {
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    const message = {
      action: 'controlVideo',
      control: control,
      ...options
    };
    
    chrome.tabs.sendMessage(tabs[0].id, message, function(response) {
      if (response && response.success) {
        console.log(`Video control '${control}' successful`);
        // Update state with new video data
        if (response.videoData) {
          currentState.videoData = response.videoData;
          
          // Update UI if needed
          if (control === 'seek') {
            const minutes = Math.floor(response.videoData.currentTime / 60);
            const seconds = Math.floor(response.videoData.currentTime % 60);
            console.log(`Current position: ${minutes}:${seconds.toString().padStart(2, '0')}`);
          }
        }
      } else {
        console.error(`Video control '${control}' failed:`, response ? response.error : 'Unknown error');
        showError(`Failed to ${control} video. Please try again.`);
      }
    });
  });
}

// Initialize UI elements
document.addEventListener('DOMContentLoaded', function() {
  // Check backend connection
  checkBackendConnection();
  
  // Check for video on the current page
  checkForVideo();
  
  // Set up event listeners for buttons
  document.getElementById('summarize-btn').addEventListener('click', summarizeVideo);
  document.getElementById('open-app-btn').addEventListener('click', openMainApplication);
  document.getElementById('retry-connection-btn').addEventListener('click', checkBackendConnection);
  document.getElementById('copy-summary').addEventListener('click', copySummaryToClipboard);
  document.getElementById('save-summary').addEventListener('click', saveSummary);
  document.getElementById('close-summary').addEventListener('click', closeSummaryView);
  
  // Set up playback control event listeners
  document.getElementById('playback-speed').addEventListener('change', changePlaybackSpeed);
  document.getElementById('play-btn').addEventListener('click', playVideo);
  document.getElementById('pause-btn').addEventListener('click', pauseVideo);
  document.getElementById('seek-back-btn').addEventListener('click', () => seekVideo(-10));
  document.getElementById('seek-forward-btn').addEventListener('click', () => seekVideo(10));
}); 