# Secure Video Summarizer

<div align="center">
  <img src="Assets/SVS.jpg" alt="Secure Video Summarizer Logo" width="200"/>
</div>

[![Tests Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml)
[![Release Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml)

A privacy-focused video summarization application that extracts key points from video content while keeping all processing secure and local.

## Repository Structure

This repository contains three main components:

- **[Backend](backend/)**: The core Flask application that handles video processing, transcription, and summarization
- **[Frontend](frontend/)**: React-based user interface for the application
- **[Extension](extension/)**: Browser extension for integrating with the Olympus Learning Platform

## Project Overview

The Secure Video Summarizer is a comprehensive solution for generating concise summaries of video content. It places a strong emphasis on privacy and security, ensuring that all video processing happens locally without sending sensitive content to third-party services.

### Key Features

- **Privacy-Focused Video Processing**: Process videos locally with no data sent to external services
- **LLM Integration**: Utilize local LLM models via Ollama for high-quality summarization
- **Google OAuth Authentication**: Secure user authentication
- **Browser Extension Integration**: Capture and summarize videos from the Olympus Learning Platform
- **Customizable Summarization**: Control the length, format, and focus of summaries
- **Cross-Platform Support**: Available for macOS and Windows

## Getting Started

Each component has its own README with detailed setup instructions:

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Extension README](extension/README.md)

## Development Status

The project is actively developed with automated CI/CD pipelines to ensure code quality and streamlined releases:

- **Automated Testing**: All code changes are tested automatically
- **Continuous Integration**: Pull requests are verified before merging
- **Release Management**: Automated creation of platform-specific packages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Features

### Security Features
- **Google OAuth Authentication**: Secure user authentication using Google SSO
- **Rate Limiting**: Protection against brute force and DoS attacks
- **CSRF Protection**: State parameter validation in OAuth flow
- **Secure Session Management**: Signed, HTTP-only cookies with proper expiration
- **Security Headers**: Implementation of recommended security headers
- **Input Validation**: Thorough validation of all user inputs
- **Privacy-Focused**: Videos processed locally without sending to third-party services
- **Comprehensive Logging**: Detailed logging of all operations with rotating file handlers
- **Robust Error Handling**: Centralized error handling with custom API error responses

### Video Processing Features
- **Video Upload**: Secure upload and storage of video files
- **Audio Extraction**: Automatic extraction of audio from video files
- **Transcription**: Conversion of speech to text
- **Summarization**: AI-powered summarization of video content
- **Secure Storage**: Encrypted storage of videos and summaries
- **Browser Integration**: Summarize videos directly from learning platforms

## Browser Integration

The application includes a browser extension that allows you to summarize videos from learning platforms like Olympus:

### Installation

1. Navigate to the `extension` directory
2. Install the extension in Chrome:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension` directory

### Native Messaging Host Setup
1. Edit `extension/com.securevideosum.app.json` to update the path to your native messaging host
2. Install the native messaging host:
   - **Linux/macOS**: Copy the JSON manifest to `~/.config/google-chrome/NativeMessagingHosts/`
   - **Windows**: Add registry key pointing to the manifest file

### Configuration
1. Get your extension ID from Chrome's extension page
2. Update your `.env` file with:
   ```
   BROWSER_EXTENSION_ID=your-extension-id-here
   ALLOWED_ORIGINS=https://olympus.mygreatlearning.com
   ```

### Usage

1. Navigate to a video on your learning platform
2. Click the extension icon in your browser toolbar
3. Click "Summarize Current Video"
4. The application will:
   - Capture the audio from the video
   - Transcribe the speech to text
   - Generate a concise summary
   - Display the summary in the application window

### Privacy Considerations

- All processing happens locally on your machine
- No video content is sent to external servers
- Your login session is used only to access videos you already have permission to view

## Setup

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` with your configuration:
   ```
   cp .env.example .env
   # Edit .env with your settings
   ```

5. Set up Google OAuth:
   - Create a project in the [Google Developer Console](https://console.developers.google.com/)
   - Enable the Google+ API
   - Create OAuth credentials (Web application type)
   - Download the client secrets JSON file and save it as `client_secret.json` in the backend directory
   - Set the redirect URI to `http://localhost:5000/auth/callback`

6. Run the application:
   ```
   python app/main.py
   ```

### Configuration Options

The application can be configured using environment variables in the `.env` file:

#### Flask Configuration
- `FLASK_ENV`: Environment mode (`development`, `testing`, or `production`)
- `SECRET_KEY`: Secret key for session encryption (must be secure in production)
- `FLASK_DEBUG`: Enable debug mode (set to 0 in production)

#### Google OAuth Configuration
- `GOOGLE_CLIENT_SECRETS_FILE`: Path to Google OAuth client secrets JSON file
- `FRONTEND_URL`: URL of the frontend application for redirects after authentication

#### Session Configuration
- `SESSION_TYPE`: Session storage type (filesystem, redis, etc.)
- `SESSION_FILE_DIR`: Directory to store session files
- `SESSION_PERMANENT`: Whether sessions should be permanent
- `SESSION_USE_SIGNER`: Sign the session cookie for added security
- `PERMANENT_SESSION_LIFETIME`: Session lifetime in seconds

#### Paths Configuration
- `VIDEOS_DIR`: Directory to store uploaded videos
- `SUMMARIES_DIR`: Directory to store generated summaries
- `LOGS_DIR`: Directory to store application logs

#### Rate Limiting (Optional)
- `RATELIMIT_STORAGE_URL`: Storage for rate limiting (memory, redis, etc.)
- `RATELIMIT_DEFAULT`: Default rate limit for all endpoints
- `RATELIMIT_AUTH_LIMIT`: Rate limit for authentication endpoints

#### Logging Configuration
- Log files are stored in the `LOGS_DIR` directory
- `app.log`: Contains all application logs
- `error.log`: Contains only error-level logs
- Logs include timestamps, IP addresses, request methods, and URLs

### Additional Dependencies

#### System Dependencies

- **FFmpeg**: Required for audio extraction from videos
  - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - On macOS: `brew install ffmpeg`
  - On Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

- **libmagic**: Required for file type detection
  - On Ubuntu/Debian: `sudo apt-get install libmagic1`
  - On macOS: `brew install libmagic`
  - On Windows: No additional installation is required as the python-magic-bin package includes the necessary DLLs.

#### Python Dependencies

The application uses several Python libraries:
- Flask: Web framework
- Flask-Session: Server-side session management
- Flask-Limiter: Rate limiting for API endpoints
- Google Auth: Authentication with Google OAuth
- SpeechRecognition: For transcribing audio to text
- Transformers: For text summarization using pre-trained models
- PyTorch: Required by Transformers
- FFmpeg-Python: Python bindings for FFmpeg

## API Endpoints

### Authentication Endpoints
- `GET /auth/login`: Initiates Google OAuth login flow
- `GET /auth/callback`: Handles OAuth callback from Google
- `POST /auth/logout`: Logs out the current user
- `GET /auth/user`: Returns information about the current user
- `POST /auth/refresh-token`: Refreshes the access token

### Video Endpoints
- `POST /video/upload`: Uploads a video file
- `GET /video/<video_id>`: Retrieves a video file