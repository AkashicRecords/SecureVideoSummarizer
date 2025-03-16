# Secure Video Summarizer - Browser Extension

<div align="center">
  <img src="../Assets/SVS.jpg" alt="Secure Video Summarizer Logo" width="200"/>
</div>

## Overview

This browser extension integrates with the Secure Video Summarizer backend to summarize videos from the Olympus Learning Platform. It enables users to generate concise summaries of educational videos without leaving the browser.

## Features

- **Direct Video Capture**: Extract audio from Olympus Learning Platform videos
- **Secure Processing**: All data handling follows strict security and privacy protocols
- **Native Messaging Integration**: Communicates with the desktop application
- **Custom Summary Options**: Configure summary length, format, and focus
- **History Tracking**: Keep track of previously summarized videos

## Setup

### Prerequisites

- Chrome, Firefox, or Edge browser
- Backend application installed and running (See [Backend README](../backend/README.md))

### Installation for Development

1. **Enable Developer Mode** in your browser:
   - Chrome: Go to `chrome://extensions/` and toggle "Developer mode"
   - Firefox: Go to `about:debugging#/runtime/this-firefox`
   - Edge: Go to `edge://extensions/` and toggle "Developer mode"

2. **Load the unpacked extension**:
   - Chrome/Edge: Click "Load unpacked" and select the `extension` directory
   - Firefox: Click "Load Temporary Add-on" and select any file in the extension directory

3. **Configure Native Messaging Host**:

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

4. **Update extension configuration**:
   - Get your extension ID from the extensions page
   - Add it to the backend `.env` file as `BROWSER_EXTENSION_ID`

## Usage

1. Navigate to a video on the Olympus Learning Platform
2. Click the extension icon in the browser toolbar
3. Configure your summarization preferences
4. Click "Summarize This Video"
5. View the generated summary

## Development

### Files Overview

- `background.js`: Background service worker for the extension
- `popup.html/js/css`: User interface for the extension popup
- `content.js`: Content script that interacts with the Olympus video player
- `com.securevideosum.app.json`: Native messaging host manifest

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