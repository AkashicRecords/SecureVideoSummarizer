# Secure Video Summarizer - Browser Extension

<div align="center">
  <img src="../Assets/SVS.jpg" alt="Secure Video Summarizer Logo" width="200"/>
</div>

[![Tests Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml)
[![Build Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml)
[![Release Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml)

## Overview

This browser extension integrates with the Secure Video Summarizer backend to summarize videos from the Olympus Learning Platform. It enables users to generate concise summaries of educational videos without leaving the browser.

## Current Status and Known Issues

### Active Issues

1. **Popup Display Issues**:
   - The popup may not display correctly in some browser configurations
   - Current workaround: Clear browser cache and reload extension
   - Fixed in latest version with updated CSS styling

2. **Video Player Integration**:
   - Limited control functionality with Olympus VideoJS player
   - Some playback controls may not work consistently
   - Working on improved integration with VideoJS API

3. **Backend Connection**:
   - Intermittent connection issues with backend service
   - Connection status may not update immediately
   - Added retry mechanism and better error handling

### Recent Fixes

1. **Popup Layout**:
   - Fixed popup dimensions (400x600px)
   - Improved scrolling behavior
   - Enhanced UI element spacing
   - Better handling of overflow content

2. **Video Detection**:
   - Improved detection of Olympus video player
   - Better handling of iframe videos
   - Enhanced metadata extraction

3. **UI Improvements**:
   - Added platform badges
   - Improved warning messages
   - Enhanced button states and feedback

## Features

- **Direct Video Capture**: Extract audio from Olympus Learning Platform videos
- **Secure Processing**: All data handling follows strict security and privacy protocols
- **Native Messaging Integration**: Communicates with the desktop application
- **Custom Summary Options**: Configure summary length, format, and focus
- **Playback Speed Control**: Adjust video playback speed from 0.5x to 3x for faster learning
- **Video Controls**: Play, pause, and seek through videos directly from the extension
- **History Tracking**: Keep track of previously summarized videos

## Setup

### Prerequisites

- Chrome (v88+), Firefox (v78+), or Edge (v88+) browser
- Backend application installed and running (See [Backend README](../backend/README.md))
- Node.js v16+ and npm v7+ for development

### Quick Start

1. **Install Backend**:
   ```bash
   # Clone repository
   git clone https://github.com/AkashicRecords/SecureVideoSummarizer.git
   cd SecureVideoSummarizer/backend
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start backend server
   python app.py
   ```

2. **Install Extension**:
   - Download latest release from [Releases page](https://github.com/AkashicRecords/SecureVideoSummarizer/releases)
   - Extract ZIP file
   - Load unpacked extension in browser

3. **Configure Native Messaging**:

   #### macOS:
   ```bash
   mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts
   cp com.securevideosum.app.json ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
   chmod +x backend/native_messaging_host.py
   ```

   #### Linux:
   ```bash
   mkdir -p ~/.config/google-chrome/NativeMessagingHosts
   cp com.securevideosum.app.json ~/.config/google-chrome/NativeMessagingHosts/
   chmod +x backend/native_messaging_host.py
   ```

   #### Windows:
   ```powershell
   # Run as Administrator
   $manifestPath = (Resolve-Path ".\com.securevideosum.app.json").Path
   $regPath = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.securevideosum.app"
   New-Item -Path $regPath -Force
   Set-ItemProperty -Path $regPath -Name "(Default)" -Value $manifestPath
   ```

## Troubleshooting Guide

### Popup Issues

1. **Popup Not Displaying**:
   - Clear browser cache and cookies
   - Disable other extensions temporarily
   - Check console for CSS/JS errors
   - Verify popup dimensions in browser inspector

2. **Layout Problems**:
   - Check browser zoom level (should be 100%)
   - Verify no CSS conflicts with page styles
   - Check for proper loading of popup.css
   - Inspect element hierarchy in dev tools

3. **Content Overflow**:
   - Verify proper scrolling behavior
   - Check container dimensions
   - Inspect padding and margins
   - Test with different content lengths

### Video Detection Issues

1. **No Video Detected**:
   - Refresh the page
   - Check if video is in iframe
   - Verify video player type (VideoJS)
   - Check console for detection errors

2. **Playback Control Issues**:
   - Verify VideoJS API availability
   - Check player state (ready/loaded)
   - Test individual control functions
   - Look for player-specific errors

### Backend Connection Issues

1. **Connection Failed**:
   - Verify backend is running
   - Check port availability
   - Test CORS configuration
   - Review backend logs

2. **Native Messaging Problems**:
   - Verify manifest installation
   - Check file permissions
   - Test host script execution
   - Review browser extension logs

## Development Guide

### Local Development

1. **Setup Development Environment**:
   ```bash
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

2. **Testing**:
   ```bash
   # Run unit tests
   npm test
   
   # Run integration tests
   npm run test:integration
   ```

3. **Building**:
   ```bash
   # Build extension
   npm run build
   
   # Pack extension
   npm run pack
   ```

### Debugging Tips

1. **Console Logging**:
   - Enable verbose logging in background.js
   - Check popup.js console messages
   - Monitor content script interactions

2. **Network Inspection**:
   - Use browser dev tools network tab
   - Monitor WebSocket connections
   - Check API request/response cycles

3. **Performance Profiling**:
   - Use Chrome Performance tab
   - Monitor memory usage
   - Check for memory leaks

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Usage

1. Navigate to a video on the Olympus Learning Platform
2. Click the extension icon in the browser toolbar
3. Configure your summarization preferences
4. Adjust video playback speed if desired
5. Use the video controls to play, pause, or seek through the video
6. Click "Summarize This Video"
7. View the generated summary

### Using Playback Speed Control

The extension provides playback speed control to enhance your learning experience:

1. **Adjusting Speed**: Use the dropdown menu to select a playback speed from 0.5x (slow) to 3x (fast)
2. **Optimal Speeds**:
   - 0.5x - 0.75x: Good for complex or technical content where you need more time to process
   - 1x: Normal speed
   - 1.25x - 1.5x: Comfortable speed increase for most educational content
   - 1.75x - 2x: Good for familiar content or review
   - 2.5x - 3x: For quick scanning or review of very familiar material

3. **Performance Impact**: Higher playback speeds can improve learning efficiency by up to 40% without significant comprehension loss for most educational content.

4. **AI Processing**: The extension automatically adjusts for playback speed when processing audio, ensuring accurate transcription and summarization regardless of the speed you choose.

## Development

### Files Overview

- `background.js`: Background service worker for the extension
- `popup.html/js/css`: User interface for the extension popup
- `content.js`: Content script that interacts with the Olympus video player
- `com.securevideosum.app.json`: Native messaging host manifest

### API Endpoints

The extension interacts with the backend through the following API endpoints:

1. **GET `/api/extension/status`**: Verifies the connection between the extension and backend.
   - Used when the popup is opened to check if the backend is running.
   - Returns connection status, version, and allowed origins.

2. **GET `/api/extension/summary_status`**: Polls for the status of the current summarization process.
   - Used to check if a summary is idle, processing, completed, or has an error.
   - Returns the generated summary when completed.

3. **POST `/api/extension/save_summary`**: Saves a generated summary to the backend.
   - Sends the summary text and video metadata to be stored.
   - Returns success or error status.

For detailed API documentation, including request/response formats and error handling, see the [API Reference Documentation](../backend/docs/api_reference.md#extension-api-endpoints).

### Testing the Extension

1. Load the extension in development mode
2. Open the browser console to view logs (Chrome: Ctrl+Shift+J or Cmd+Opt+J)
3. Navigate to an Olympus video page
4. Test the extension functionality
5. Check the console for any errors or debug messages

## Building for Production

For production distribution:

1. Remove any debug console logs
2. Update version in `manifest.json`
3. Zip the extension directory for upload to browser extension stores