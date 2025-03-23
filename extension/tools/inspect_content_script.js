/**
 * Utility script to be executed in Chrome DevTools console on a page with SVS extension
 * This helps inspect content script injection and video detection
 */

(function() {
  console.clear();
  console.log("%c 🔍 SVS Content Script Inspector 🔍", "font-size: 20px; font-weight: bold; color: #4285f4;");
  console.log("%c This utility helps debug the Secure Video Summarizer extension", "font-style: italic; color: #666;");
  
  // Check if content script is loaded by attempting to access a custom property
  // we'll add to the window object
  console.log("\n%c 1. Checking if content script is loaded...", "font-weight: bold; color: #0f9d58;");
  
  // Send a message to the extension content script
  function pingContentScript() {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
          const lastError = chrome.runtime.lastError;
          if (lastError) {
            console.log("%c ❌ Content script not detected: " + lastError.message, "color: #ea4335;");
            resolve(false);
          } else if (response && response.status === 'ok') {
            console.log("%c ✅ Content script is loaded and responding!", "color: #0f9d58;");
            resolve(true);
          } else {
            console.log("%c ❓ Received response but status is not 'ok'", "color: #ea4335;");
            console.log(response);
            resolve(false);
          }
        });
      } catch (e) {
        console.log("%c ❌ Error pinging content script: " + e.message, "color: #ea4335;");
        resolve(false);
      }
    });
  }
  
  // Get video information from the content script
  function getVideoInfo() {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage({ action: 'getCurrentVideo' }, (response) => {
          const lastError = chrome.runtime.lastError;
          if (lastError) {
            console.log("%c ❌ Failed to get video info: " + lastError.message, "color: #ea4335;");
            resolve(null);
          } else if (response && response.success && response.videoData) {
            console.log("%c ✅ Successfully retrieved video data!", "color: #0f9d58;");
            resolve(response.videoData);
          } else {
            console.log("%c ❓ No video data found or invalid response", "color: #ea4335;");
            console.log(response);
            resolve(null);
          }
        });
      } catch (e) {
        console.log("%c ❌ Error getting video info: " + e.message, "color: #ea4335;");
        resolve(null);
      }
    });
  }
  
  // Examine the page for video elements directly
  function examinePageForVideos() {
    console.log("\n%c 3. Examining page for video elements...", "font-weight: bold; color: #0f9d58;");
    
    // Get all video elements
    const videos = document.querySelectorAll('video');
    console.log(`Found ${videos.length} video element(s) on the page`);
    
    // Check each video element
    videos.forEach((video, index) => {
      console.log(`\n%c Video #${index + 1}:`, "font-weight: bold; color: #4285f4;");
      console.log(`  Source: ${video.currentSrc || video.src || 'No source'}`);
      console.log(`  Duration: ${video.duration || 'Unknown'} seconds`);
      console.log(`  Dimensions: ${video.videoWidth}x${video.videoHeight}`);
      console.log(`  In iframe: ${window !== window.top}`);
      console.log(`  Player type: ${getPlayerType(video)}`);
      console.log(`  Playback state: ${video.paused ? 'Paused' : 'Playing'} (${video.currentTime}s)`);
      
      // Try to find the title
      const possibleTitleElements = [
        // Common title elements
        document.querySelector('title'),
        document.querySelector('h1'),
        // VideoJS specific
        document.querySelector('.vjs-title'),
        // YouTube specific
        document.querySelector('.title'),
        document.querySelector('#title'),
        // Generic attempts
        video.closest('div')?.querySelector('h1, h2, h3, .title')
      ];
      
      const title = possibleTitleElements.find(el => el && el.textContent.trim())?.textContent.trim();
      console.log(`  Title: ${title || 'Unknown'}`);
      
      // Check if this appears to be VideoJS
      if (video.closest('.video-js') || video.classList.contains('vjs-tech')) {
        console.log("%c  VideoJS player detected!", "color: #fbbc04;");
      }
      
      // Log the video element for inspection
      console.log('  Element:', video);
    });
    
    // Check for iframes that might contain videos
    const iframes = document.querySelectorAll('iframe');
    console.log(`\nFound ${iframes.length} iframe(s) on the page`);
    iframes.forEach((iframe, index) => {
      console.log(`  Iframe #${index + 1}: ${iframe.src}`);
    });
    
    // Look for Olympus specific elements
    const olympusElements = document.querySelectorAll('[class*="olympus"], [id*="olympus"]');
    if (olympusElements.length > 0) {
      console.log("\n%c Olympus-specific elements found:", "font-weight: bold; color: #fbbc04;");
      olympusElements.forEach(el => {
        console.log(`  ${el.tagName} - class: ${el.className}, id: ${el.id}`);
      });
    }
  }
  
  // Determine the player type
  function getPlayerType(videoElement) {
    if (videoElement.classList.contains('vjs-tech') || videoElement.closest('.video-js')) {
      return 'VideoJS';
    } else if (location.host.includes('youtube') || videoElement.closest('[id^="movie_player"]')) {
      return 'YouTube';
    } else if (location.host.includes('vimeo') || videoElement.closest('.vimeo-player')) {
      return 'Vimeo';
    } else if (document.querySelector('[class*="olympus"], [id*="olympus"]')) {
      return 'Olympus';
    } else {
      return 'Generic HTML5 Video';
    }
  }
  
  // Run the checks
  async function runChecks() {
    const contentScriptActive = await pingContentScript();
    
    if (contentScriptActive) {
      console.log("\n%c 2. Requesting video data from content script...", "font-weight: bold; color: #0f9d58;");
      const videoData = await getVideoInfo();
      
      if (videoData) {
        console.log("%c Video data reported by content script:", "color: #4285f4;");
        console.table({
          "Title": videoData.title || 'Unknown',
          "Platform": videoData.platform || 'Unknown',
          "Duration": videoData.duration || 'Unknown',
          "Source": videoData.src || 'Unknown',
          "In iframe": videoData.inIframe || false,
          "Is VideoJS": videoData.isVideoJS || false,
          "Is Virtual": videoData.isVirtual || false,
          "Player Type": videoData.playerType || 'Unknown'
        });
      }
    } else {
      console.log("%c Content script is not active. DOM will be examined directly.", "color: #fbbc04;");
    }
    
    // Always examine the page directly to compare with content script findings
    examinePageForVideos();
    
    console.log("\n%c 4. Troubleshooting Recommendations:", "font-weight: bold; color: #0f9d58;");
    if (!contentScriptActive) {
      console.log("%c • Try clicking 'Refresh Content Script' in the extension popup", "color: #4285f4;");
      console.log("%c • Reload the page and reopen the extension", "color: #4285f4;");
      console.log("%c • Check if the content script is properly configured in manifest.json", "color: #4285f4;");
    } else if (!await getVideoInfo()) {
      console.log("%c • Current page may not have a supported video player", "color: #4285f4;");
      console.log("%c • Video might be in an iframe that the extension can't access", "color: #4285f4;");
      console.log("%c • Try refreshing the page and waiting a few seconds", "color: #4285f4;");
    }
    
    console.log("\n%c 5. Copy this command to check content script injection:", "font-weight: bold; color: #0f9d58;");
    console.log(`chrome.scripting.executeScript({ target: {tabId: <current-tab-id>}, files: ['content.js'] })`);
  }
  
  // Execute all checks
  runChecks();
})(); 