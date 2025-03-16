// Listen for messages from the webpage or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getCurrentVideo") {
    // Get the current video element from the page
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
}); 