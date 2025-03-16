# Browser Extension for Olympus Learning Platform

This document outlines the architecture and implementation details for the SecureVideoSummarizer browser extension, specifically designed to work with the Olympus Learning Platform video player.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Implementation Details](#implementation-details)
- [Integration with Backend](#integration-with-backend)
- [Installation and Setup](#installation-and-setup)
- [Development Guide](#development-guide)
- [Privacy and Security Considerations](#privacy-and-security-considerations)

## Overview

The SecureVideoSummarizer browser extension enables users to generate summaries of videos played on the Olympus Learning Platform (`olympus.mygreatlearning.com`). It captures transcripts from videos, sends them to our backend for processing, and displays concise summaries to enhance the learning experience.

### Key Features

- Direct integration with Olympus video player
- Real-time transcription of video content
- Customizable summary generation (length, format, focus)
- Playback speed controls for more efficient processing
- History of previously summarized videos
- Privacy-focused design (processes content locally when possible)

## Architecture

The browser extension follows a modular architecture:

1. **Content Scripts**: JavaScript that runs in the context of the Olympus video pages to interact with the video player
2. **Background Service Worker**: Manages state and communication with the backend API
3. **Popup UI**: User interface for controlling the extension and viewing summaries
4. **Options Page**: Configuration settings for the extension

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│ Browser Extension                                   │
│                                                     │
│  ┌─────────────┐     ┌───────────────────────┐      │
│  │ Popup UI    │     │ Background Service    │      │
│  │             │◄───►│                       │      │
│  └─────────────┘     └───────────┬───────────┘      │
│         ▲                        │                  │
│         │                        │                  │
│         ▼                        ▼                  │
│  ┌─────────────┐     ┌───────────────────────┐      │
│  │ Options     │     │ Content Scripts       │      │
│  │             │     │ (Olympus Integration) │      │
│  └─────────────┘     └───────────────────────┘      │
└────────────────────────────┬────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│ SecureVideoSummarizer Backend                      │
└────────────────────────────────────────────────────┘
```

## Implementation Details

### Content Scripts

The content scripts interact with the Olympus video player to:

1. Detect when a video is playing on the platform
2. Insert UI controls in the video player interface
3. Capture audio from the video player
4. Perform real-time transcription using the Web Speech API
5. Send transcribed text to the background service worker

**Key Files:**
- `content.js`: Main content script that injects into Olympus pages
- `olympus-player.js`: Specific logic to interact with the Olympus video player
- `transcription.js`: Speech recognition implementation

### Video Player Integration

Our extension detects and integrates with the Olympus video player by:

```javascript
// Example detection code
function detectOlympusPlayer() {
  // Look for common Olympus player elements
  const playerElement = document.querySelector('.gl-video') || 
                        document.querySelector('.video-js') ||
                        document.querySelector('.wistia_embed');
  
  if (playerElement) {
    initializePlayerControls(playerElement);
  }
}
```

### Background Service Worker

The background service worker:

1. Maintains extension state across browser sessions
2. Communicates with the backend API
3. Manages authentication
4. Stores user preferences and history

**Key Files:**
- `background.js`: Main service worker file
- `api-client.js`: Client for backend API communication
- `storage.js`: Manages local storage for the extension

### Popup UI

The popup UI provides a user-friendly interface for:

1. Starting/stopping summarization
2. Selecting summarization options (length, format, focus)
3. Viewing generated summaries
4. Accessing summarization history
5. Adjusting playback speed

**Key Files:**
- `popup.html`: HTML structure for the popup
- `popup.js`: Interactive functionality
- `styles.css`: Visual styling

## Integration with Backend

The extension communicates with the SecureVideoSummarizer backend using the following endpoints:

- `GET /api/extension/status`: Verify connection and authentication
- `POST /api/olympus/capture`: Submit transcripts for summarization
- `GET /api/olympus/history`: Retrieve history of summarized videos
- `GET /api/olympus/summary/{id}`: Retrieve a specific summary

See the [API Reference](api_reference.md) for complete details.

### Communication Flow

1. User initiates summarization in the extension
2. Extension captures and transcribes the video content
3. Transcription is sent to the backend via `/api/olympus/capture`
4. Backend processes the transcript using LLM technology
5. Summary is returned to the extension and displayed to the user

## Installation and Setup

### Prerequisites

- Chrome, Firefox, or Edge browser
- SecureVideoSummarizer backend server running

### Development Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/SecureVideoSummarizer.git
   ```
2. Navigate to the extension directory:
   ```
   cd SecureVideoSummarizer/extension
   ```
3. Install dependencies:
   ```
   npm install
   ```
4. Build the extension:
   ```
   npm run build
   ```
5. Load the unpacked extension in your browser:
   - Chrome: Open `chrome://extensions/`, enable Developer mode, click "Load unpacked", select the `dist` folder
   - Firefox: Open `about:debugging#/runtime/this-firefox`, click "Load Temporary Add-on", select any file in the `dist` folder

### Production Installation

The extension will be available on the Chrome Web Store and Firefox Add-ons store once released.

## Development Guide

### Setting Up for Development

1. Configure your backend URL in `config.js`
2. Set up browser for extension debugging
3. Use the provided development tools:
   - `npm run dev`: Build in development mode with auto-reload
   - `npm run lint`: Run linting checks
   - `npm run test`: Run tests

### Adding New Features

Follow these guidelines when adding new features:

1. Create modular components for each feature
2. Follow the existing architecture pattern
3. Add appropriate tests
4. Document API changes or new functionality

## Privacy and Security Considerations

### Data Handling

- Transcriptions are processed locally when possible to minimize data transfer
- User login credentials are never accessed or stored
- Video content is only processed with explicit user consent
- No personal data is stored permanently unless opted-in by the user

### Security Measures

- All communications with the backend use HTTPS
- Authentication is handled via secure tokens
- Content Security Policy (CSP) is implemented
- Extension permissions are limited to only what's necessary
- Regular security audits are conducted

### Olympus-Specific Considerations

The extension is designed to work within the constraints of the Olympus Learning Platform:

- No interference with normal platform functionality
- Respects cross-origin restrictions
- Does not attempt to bypass any platform security measures
- Operates only on publicly accessible elements of the video player

## Troubleshooting

### Common Issues

1. **Extension cannot detect video player**
   - Ensure you're on a valid Olympus video page
   - Try refreshing the page
   - Check console for specific errors

2. **Transcription fails to start**
   - Ensure your browser has microphone permissions enabled
   - Check that the video has audio
   - Try a different browser if issues persist

3. **Cannot connect to backend**
   - Verify backend URL in extension settings
   - Check that the backend server is running
   - Ensure network connectivity

### Getting Support

For support, please open an issue on our GitHub repository or contact the development team. 