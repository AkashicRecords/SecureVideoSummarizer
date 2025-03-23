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
  
  // Action buttons
  summarizeBtn: document.getElementById('summarize-btn'),
  openAppBtn: document.getElementById('open-app-btn'),
  retryConnectionBtn: document.getElementById('retry-connection'),
  
  // Summary display
  summaryResult: document.getElementById('summary-result'),
  summaryContent: document.getElementById('summary-content'),
  copySummaryBtn: document.getElementById('copy-summary'),
  saveSummaryBtn: document.getElementById('save-summary'),
  closeSummaryBtn: document.getElementById('close-summary'),
  summaryLength: document.getElementById('summary-length'),
};

// Add event listeners for platform-specific buttons
document.getElementById('youtube-summarize-btn').addEventListener('click', function() {
  // Handle YouTube summarization
  console.log('YouTube summarize button clicked');
  startSummarizing();
}); 