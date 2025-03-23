# Olympus Video Integration

This document provides technical details on the integration between the Secure Video Summarizer extension and Olympus video platform.

## Overview

The Olympus integration enables users to capture, process, and summarize videos from the Olympus Learning Platform (mygreatlearning.com). This integration is built with specialized handling for Olympus's VideoJS-based player.

## System Components

### Backend Server (Python Flask)

- **Port Configuration**: Runs on port 8080
- **Dependencies**: 
  - Ollama for AI processing (deepseek-r1:1.5b model)
  - Python 3.13.2

### Chrome Extension

- **Content Script**: JavaScript that detects and interacts with Olympus videos
- **Background Script**: Handles communication with the backend server
- **Popup Interface**: User-facing controls for the extension

## Configuration Requirements

### Port Configuration

The system is configured to use specific ports for communication:

```javascript
// Extension (background.js)
const API_CONFIG = {
  baseUrl: 'http://localhost:8080',
  maxRetries: 3,
  retryDelay: 1000,
  timeout: 30000
};
```

```python
# Backend CORS configuration
CORS configured with origins: [
  'http://localhost:8080', 
  'chrome-extension://*', 
  'chrome-extension://kcjiaoepaghehlmnbpkimmidpnpkmllk', 
  'chrome-extension://*'
]
```

> **Important**: The port numbers must match between the extension and backend server.

## Olympus-Specific Implementation

### Video Detection

The extension implements specialized detection for Olympus video players:

1. **URL Pattern Detection**:
   ```javascript
   // Domain detection for Olympus
   if (url.includes('olympus-learning.com') || 
       url.includes('olympus.learning') || 
       url.includes('mygreatlearning.com')) {
     return 'olympus';
   }
   ```

2. **VideoJS Player Detection**:
   ```javascript
   // Enhanced detection for VideoJS players on Olympus
   function findOlympusPlayer() {
     // Try multiple methods to find VideoJS players
     // 1. videojs.getPlayers()
     // 2. videojs.getAllPlayers()
     // 3. document.querySelectorAll('.video-js')
   }
   ```

### Backend API Endpoints

The backend exposes three primary endpoints for Olympus integration:

1. **Status Endpoint**: 
   - `GET /api/olympus/status`
   - Returns readiness status and supported features

2. **Capture Endpoint**:
   - `POST /api/olympus/capture`
   - Processes transcript data and generates summaries

3. **Process URL Endpoint**:
   - `POST /api/olympus/process-url`
   - Processes Olympus video URLs directly

## Authentication Requirements

- Users must be logged into the Olympus platform to access video content
- The extension must be active on the authenticated page
- Video access is tied to the user's Olympus credentials

## Troubleshooting

### Common Issues

1. **Content Script Not Detected**:
   - Error: "Could not establish connection. Receiving end does not exist."
   - Resolution: Ensure you're on a page with an Olympus video and reload the extension.

2. **Port Conflicts**:
   - Error: "Address already in use. Port 8080 is in use by another program."
   - Resolution: Stop other services using port 8080 or modify configuration.

3. **Backend Connection Failures**:
   - Check if Ollama is running on port 11434
   - Verify CORS configuration includes extension origins

### Debugging Steps

1. Check extension console logs (F12 > Console)
2. Verify backend server is running (check logs)
3. Confirm user is logged into Olympus platform
4. Test with the `--verbose` flag for detailed logs

## Testing

Run the test suite to verify the Olympus integration:

```bash
cd /Users/lightspeedtooblivion/Documents/SVS/backend
python test_olympus_video.py --test all --verbose --mock-download
```

Individual tests can be run with:
```bash
python test_olympus_video.py --test status
python test_olympus_video.py --test capture
python test_olympus_video.py --test process --mock-download
```

## Dependencies

- VideoJS detection requires the Olympus platform to use VideoJS
- Backend summarization requires Ollama with the deepseek-r1:1.5b model
- Video download features require yt-dlp 