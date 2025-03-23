# Olympus Video Integration

This document provides technical details on the integration between the Secure Video Summarizer extension and Olympus video platform.

## Overview

The Olympus integration enables users to capture, process, and summarize videos from the Olympus Learning Platform (mygreatlearning.com). This integration uses specialized handling for Olympus's VideoJS-based player and provides accurate video transcripts and summaries.

## 1. Installation

### Prerequisites
- Python 3.13+ for the backend server
- Node.js 18+ for building the extension
- Chrome browser (version 90+)
- Ollama installed and configured with the deepseek-r1:1.5b model

### Backend Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/secure-video-summarizer.git
cd secure-video-summarizer/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install yt-dlp for video downloading support
pip install yt-dlp
```

### Extension Installation
```bash
# Navigate to the extension directory
cd ../extension

# Install dependencies
npm install

# Build the extension
npm run build

# Load in Chrome:
# 1. Open chrome://extensions
# 2. Enable Developer Mode
# 3. Click "Load unpacked" and select the "build" directory
```

## 2. Setup and Configuration

### Backend Server Configuration

1. **Port Configuration**:
   - The server runs on port 8080 by default
   - Ensure this port is available or modify as needed in run_server.sh

2. **Environment Variables**:
   - Create a `.env` file in the backend directory with:
   ```
   FLASK_ENV=development
   DEBUG=True
   OLLAMA_API_URL=http://localhost:11434/api
   API_URL=http://localhost:8080
   EXTENSION_ID=your_extension_id
   ```

3. **Starting the Server**:
   ```bash
   cd /path/to/backend
   ./run_server.sh
   ```

### Chrome Extension Configuration

1. **API Configuration**:
   - The extension is pre-configured to connect to http://localhost:8080
   - If you changed the backend port, update in background.js:
   ```javascript
   const API_CONFIG = {
     baseUrl: 'http://localhost:8080',  // Change if needed
     maxRetries: 3,
     retryDelay: 1000,
     timeout: 30000
   };
   ```

2. **Extension Permissions**:
   - Ensure the extension has permissions for Olympus domains
   - Required domains are already included in manifest.json:
   ```json
   "host_permissions": [
     "http://*.mygreatlearning.com/*",
     "https://*.mygreatlearning.com/*"
   ]
   ```

## 3. Troubleshooting

### Common Issues

1. **Content Script Not Detected**:
   - **Error**: "Could not establish connection. Receiving end does not exist."
   - **Cause**: Content script not properly injected or video not detected
   - **Solution**: 
     - Ensure you're logged into Olympus and on a page with a video
     - Refresh the page with the extension already loaded
     - Check console logs for specific errors (F12 > Console)

2. **Port Conflicts**:
   - **Error**: "Address already in use. Port 8080 is in use by another program."
   - **Cause**: Another service is using port 8080
   - **Solution**: 
     - Stop the other service using port 8080
     - Or change the port in both the server and extension configuration

3. **Backend Connection Failures**:
   - **Error**: "Failed to connect to backend" or timeout errors
   - **Cause**: Server not running or CORS issues
   - **Solution**: 
     - Verify server is running (`ps aux | grep run_server`)
     - Check if Ollama is running on port 11434
     - Verify CORS configuration includes extension origins

4. **Video Detection Issues**:
   - **Error**: "No video found on this page"
   - **Cause**: VideoJS player not properly detected
   - **Solution**:
     - Ensure video is actually playing on the page
     - Check if the page uses a supported VideoJS version
     - Try refreshing after the video starts playing

### Debugging Steps

1. **Enable Verbose Logging**:
   - Run tests with the `--verbose` flag:
   ```bash
   python test_olympus_video.py --test all --verbose
   ```
   - Add `console.debug()` statements in content.js

2. **Check Extension Logs**:
   - Open Chrome DevTools (F12)
   - Navigate to the Console tab
   - Filter for messages containing "Olympus"

3. **Verify Server Status**:
   - Test the status endpoint directly:
   ```bash
   curl http://localhost:8080/api/olympus/status
   ```

4. **Testing with Mock Data**:
   - Use the `--mock-download` flag to test without actual video downloads:
   ```bash
   python test_olympus_video.py --test process --mock-download
   ```

## 4. Under the Hood

### System Architecture

The Olympus integration uses a multi-component architecture:

1. **Content Script** (JavaScript):
   - Runs in the context of Olympus web pages
   - Detects VideoJS players and extracts metadata
   - Communicates with popup and background scripts

2. **Background Script** (JavaScript):
   - Manages communication with the backend server
   - Handles API requests and retries
   - Maintains state between sessions

3. **Backend Server** (Python Flask):
   - Processes video data via API endpoints
   - Generates transcripts and summaries
   - Manages authentication and session data

### Key Files

| File | Purpose |
|------|---------|
| `extension/content.js` | VideoJS detection, metadata extraction |
| `extension/background.js` | API communication, request management |
| `backend/app/api/olympus_routes.py` | API endpoints for Olympus integration |
| `backend/test_olympus_video.py` | Integration tests |

### Video Detection Algorithm

The extension uses a multi-step approach to detect Olympus videos:

1. **URL Pattern Matching**:
   ```javascript
   function detectPlatform() {
     const url = window.location.href.toLowerCase();
     if (url.includes('olympus-learning.com') || 
         url.includes('olympus.learning') || 
         url.includes('mygreatlearning.com')) {
       return 'olympus';
     }
     // Further detection...
   }
   ```

2. **VideoJS Player Detection**:
   ```javascript
   function findOlympusPlayer() {
     // Method 1: videojs.getPlayers()
     if (typeof videojs.getPlayers === 'function') {
       players = videojs.getPlayers();
       if (Object.keys(players).length > 0) {
         player = players[Object.keys(players)[0]];
       }
     }
     
     // Method 2: videojs.getAllPlayers()
     // Method 3: DOM-based detection
     // ...
   }
   ```

3. **Metadata Extraction**:
   - Pulls video title, duration, URL, and player state
   - Creates virtual video elements when necessary
   - Extracts transcript data if available

### API Flow

1. **Status Check**:
   - Client calls `GET /api/olympus/status`
   - Server returns capabilities and readiness

2. **Transcript Capture**:
   - Client submits transcript via `POST /api/olympus/capture`
   - Server processes transcript and generates summary
   - Response includes session ID and summary

3. **URL Processing**:
   - Client submits video URL via `POST /api/olympus/process-url`
   - Server attempts to download video (or uses mock data)
   - Response includes transcript, summary, and session ID

### Data Processing Flow

1. **Video Detection**: Content script identifies Olympus video
2. **Metadata Extraction**: Player details captured
3. **Transcript Capture**: Manual or automated
4. **Backend Processing**: AI-based summarization
5. **Response Handling**: UI updates with results

## Testing

Run the comprehensive test suite to verify the Olympus integration:

```bash
cd /path/to/backend
python test_olympus_video.py --test all --verbose --mock-download
```

Individual tests can be run with:
```bash
python test_olympus_video.py --test status
python test_olympus_video.py --test capture
python test_olympus_video.py --test process --mock-download
```

## IDE Integration

When working with the Olympus integration in the Cursor IDE:

1. **Debugging with Console.log**: 
   - Add `console.debug('Olympus debug:', variable)` statements in content.js
   - Check the Chrome DevTools console with the extension open

2. **Backend Route Inspection**:
   - Use Cursor's split-view to compare olympus_routes.py with test_olympus_video.py
   - Jump between definition and references using Cursor's code navigation

3. **Test Workflow**:
   - Run the tests from the Cursor terminal
   - Set breakpoints in the test code using the Cursor debugger
   - Check the test logs in olympus_test.log

4. **Code Completion**:
   - Use Cursor's AI assistance for VideoJS API completion
   - Get context-aware suggestions for Olympus-specific code 