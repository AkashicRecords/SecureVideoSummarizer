# Secure Video Summarizer - Browser Extension

<div align="center">
  <img src="../Assets/SVS.jpg" alt="Secure Video Summarizer Logo" width="200"/>
</div>

[![Tests Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml)
[![Build Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml)
[![Release Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml)

## Overview

This browser extension integrates with the Secure Video Summarizer backend to summarize videos from the Olympus Learning Platform. It enables users to generate concise summaries of educational videos without leaving the browser.

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

- Chrome, Firefox, or Edge browser
- Backend application installed and running (See [Backend README](../backend/README.md))

### Installation for End Users

#### Option 1: Install from Browser Extension Store (Recommended)

1. **Chrome Web Store**:
   - Navigate to the [Chrome Web Store](https://chrome.google.com/webstore/category/extensions)
   - Search for "Secure Video Summarizer"
   - Click "Add to Chrome" and confirm the installation
   - The extension icon will appear in your browser toolbar

2. **Firefox Add-ons**:
   - Navigate to [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/)
   - Search for "Secure Video Summarizer"
   - Click "Add to Firefox" and confirm the installation
   - The extension icon will appear in your browser toolbar

3. **Edge Add-ons**:
   - Navigate to [Edge Add-ons](https://microsoftedge.microsoft.com/addons)
   - Search for "Secure Video Summarizer"
   - Click "Get" and confirm the installation
   - The extension icon will appear in your browser toolbar

#### Option 2: Manual Installation

If the extension is not yet available in the browser stores, you can install it manually:

1. **Download the Extension**:
   - Download the latest release ZIP file from the [Releases page](https://github.com/AkashicRecords/SecureVideoSummarizer/releases)
   - Extract the ZIP file to a location on your computer

2. **Install in Chrome/Edge**:
   - Open Chrome or Edge and navigate to the extensions page:
     - Chrome: `chrome://extensions/`
     - Edge: `edge://extensions/`
   - Enable "Developer mode" using the toggle in the top-right corner
   - Click "Load unpacked" and select the extracted extension directory
   - The extension icon will appear in your browser toolbar

3. **Install in Firefox**:
   - Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on"
   - Navigate to the extracted extension directory and select any file
   - The extension icon will appear in your browser toolbar
   - Note: In Firefox, temporary add-ons are removed when you close the browser

4. **Configure the Backend Connection**:
   - Make sure the backend application is running
   - Click the extension icon and check for a successful connection message
   - If prompted, enter the backend URL (default: `http://localhost:5000`)

### Installation for Development

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/AkashicRecords/SecureVideoSummarizer.git
   cd SecureVideoSummarizer
   ```

2. **Enable Developer Mode** in your browser:
   - Chrome: Go to `chrome://extensions/` and toggle "Developer mode"
   - Firefox: Go to `about:debugging#/runtime/this-firefox`
   - Edge: Go to `edge://extensions/` and toggle "Developer mode"

3. **Load the unpacked extension**:
   - Chrome/Edge: Click "Load unpacked" and select the `extension` directory
   - Firefox: Click "Load Temporary Add-on" and select any file in the extension directory

4. **Configure Native Messaging Host**:

#### On macOS/Linux:
```bash
mkdir -p ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts
cp com.securevideosum.app.json ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/
```

#### On Windows:
```powershell
# Run this in PowerShell as Admin
$manifestPath = (Resolve-Path ".\com.securevideosum.app.json").Path
$regPath = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.securevideosum.app"
New-Item -Path $regPath -Force
Set-ItemProperty -Path $regPath -Name "(Default)" -Value $manifestPath
```

5. **Update extension configuration**:
   - Get your extension ID from the extensions page:
     - Chrome/Edge: It's displayed in the extension details
     - Firefox: It's shown in the `about:debugging` page
   - Add it to the backend `.env` file as `BROWSER_EXTENSION_ID`
   - Update the `com.securevideosum.app.json` file to include your extension ID in the `allowed_origins` field

6. **Start the Backend**:
   - Follow the instructions in the [Backend README](../backend/README.md) to start the backend server
   - Ensure it's running on the default port (5000) or update the extension's configuration accordingly

### Troubleshooting Installation Issues

#### Connection Issues

1. **Backend Not Running**:
   - **Symptom**: "Failed to connect to backend" error in the extension
   - **Solution**: 
     - Ensure the backend server is running
     - Check if it's accessible at `http://localhost:5000`
     - Verify there are no firewall rules blocking the connection

2. **CORS Errors**:
   - **Symptom**: Console errors about CORS policy
   - **Solution**:
     - Verify your extension ID is correctly set in the backend's `.env` file
     - Restart the backend server after making changes
     - Check the backend logs for any CORS-related errors

3. **Native Messaging Host Not Found**:
   - **Symptom**: "Failed to connect to native messaging host" error
   - **Solution**:
     - Verify the manifest file is correctly installed
     - Check that the path in the manifest points to the correct location of the native messaging host script
     - Ensure the script has executable permissions

#### Installation Issues

1. **Extension Not Loading**:
   - **Symptom**: Extension doesn't appear in the browser toolbar
   - **Solution**:
     - Check the browser's extension page for any error messages
     - Verify all required files are present in the extension directory
     - Try disabling and re-enabling the extension

2. **Manifest Error**:
   - **Symptom**: "Manifest file is invalid" error
   - **Solution**:
     - Check the `manifest.json` file for syntax errors
     - Ensure it complies with the Manifest V3 specification
     - Validate the JSON format using an online validator

3. **Permission Issues**:
   - **Symptom**: Features not working due to missing permissions
   - **Solution**:
     - Check that all required permissions are granted to the extension
     - Some permissions require explicit user approval; check for permission prompts
     - Try reinstalling the extension to trigger permission prompts again

#### Browser-Specific Issues

1. **Chrome/Edge**:
   - **Issue**: Extension disappears after browser restart
   - **Solution**: Make sure you've installed it properly, not just loaded it temporarily

2. **Firefox**:
   - **Issue**: Temporary add-on disappears after browser close
   - **Solution**: This is expected behavior; use a signed extension for permanent installation

3. **Extension ID Changes**:
   - **Issue**: Extension ID changes after reloading unpacked extension
   - **Solution**: 
     - In Chrome, use a packed extension with a consistent ID
     - In development, update the backend configuration when the ID changes

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