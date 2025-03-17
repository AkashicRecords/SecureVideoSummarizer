// Listen for messages from the webpage or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background script received message:', request.action);
  
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
    // Store video data and options
    const videoData = request.videoData;
    const options = request.options || {};
    const playbackRate = videoData.playbackRate || 1.0;
    
    console.log('Video data:', videoData);
    console.log('Options:', options);
    console.log('Playback rate:', playbackRate);
    
    // Get the active tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const activeTab = tabs[0];
      
      // Request tab audio capture permission
      chrome.tabCapture.capture({
        audio: true,
        video: false,
        audioConstraints: {
          mandatory: {
            chromeMediaSource: 'tab'
          }
        }
      }, function(stream) {
        if (!stream) {
          console.error('Error starting tab capture:', chrome.runtime.lastError);
          sendResponse({success: false, error: 'Failed to capture tab audio'});
          return;
        }
        
        console.log('Tab audio capture started');
        
        // Process the audio stream
        processAudioStream(stream, videoData, options, playbackRate)
          .then(result => {
            console.log('Audio processing completed:', result);
            sendResponse({success: true, result: result});
          })
          .catch(error => {
            console.error('Error processing audio:', error);
            sendResponse({success: false, error: error.message || 'Unknown error'});
          });
      });
    });
    
    return true; // Required for async sendResponse
  }
});

// Process audio stream and send to backend
async function processAudioStream(stream, videoData, options, playbackRate) {
  try {
    // Create a MediaRecorder to record the stream
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm'
    });
    
    const audioChunks = [];
    
    // Listen for data available event
    mediaRecorder.addEventListener('dataavailable', event => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    });
    
    // Start recording
    mediaRecorder.start();
    
    // Record for a set duration (adjust based on video length)
    const recordingDuration = calculateRecordingDuration(videoData.duration, playbackRate);
    console.log(`Recording for ${recordingDuration / 1000} seconds at ${playbackRate}x speed`);
    
    // Wait for recording to complete
    await new Promise(resolve => {
      setTimeout(() => {
        mediaRecorder.stop();
        stream.getTracks().forEach(track => track.stop());
        resolve();
      }, recordingDuration);
    });
    
    // Wait for all data to be available
    await new Promise(resolve => {
      mediaRecorder.addEventListener('stop', () => resolve());
    });
    
    // Create a Blob from the recorded chunks
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    // Send to backend for processing
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('video_data', JSON.stringify(videoData));
    formData.append('options', JSON.stringify(options));
    formData.append('playback_rate', playbackRate.toString());
    
    // Send to backend
    const response = await fetch('http://localhost:5000/api/transcribe', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in processAudioStream:', error);
    throw error;
  }
}

// Calculate recording duration based on video length and playback rate
function calculateRecordingDuration(videoDuration, playbackRate) {
  // Default to 30 seconds if duration is unknown
  if (!videoDuration || videoDuration <= 0) {
    return 30000; // 30 seconds in milliseconds
  }
  
  // Calculate how long to record based on playback rate
  // For example, at 2x speed, we need to record for half the time
  const durationInMs = (videoDuration / playbackRate) * 1000;
  
  // Cap at a reasonable maximum (e.g., 2 minutes)
  return Math.min(durationInMs, 120000);
} 