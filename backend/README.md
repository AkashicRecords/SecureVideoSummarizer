# Secure Video Summarizer - Backend

A secure backend application for summarizing video content with privacy-focused features.

[![Tests](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/run-tests.yml)
[![Build Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/build-packages.yml)
[![Release Status](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml/badge.svg)](https://github.com/AkashicRecords/SecureVideoSummarizer/actions/workflows/create-release.yml)

## Features

### Security Features

* **Google OAuth Authentication**: Secure user authentication using Google SSO
* **Rate Limiting**: Protection against brute force and DoS attacks
* **CSRF Protection**: State parameter validation in OAuth flow
* **Secure Session Management**: Signed, HTTP-only cookies with proper expiration
* **Security Headers**: Implementation of recommended security headers
* **Input Validation**: Thorough validation of all user inputs
* **Privacy-Focused**: Videos processed locally without sending to third-party services
* **Comprehensive Logging**: Detailed logging of all operations with rotating file handlers
* **Robust Error Handling**: Centralized error handling with custom API error responses

### Video Processing Features

* **Enhanced Audio Extraction**: Improved audio quality for better transcription results
* **Multi-Service Transcription**: Uses multiple transcription services for better accuracy
* **Audio Validation**: Validates audio files to ensure they're suitable for transcription
* **Audio Normalization**: Automatically adjusts volume levels for better transcription
* **Customizable Summarization**: Options for summary length, format, and focus areas
* **Multiple Summary Formats**: Support for paragraph, bullet points, numbered lists, and key points formats

### Olympus Learning Platform Integration

* **Browser Extension**: Chrome/Firefox extension to summarize videos from Olympus
* **Direct Video Player Integration**: Works with Olympus learning platform video player
* **Real-time Transcription**: Captures and transcribes video content during playback
* **Playback Speed Control**: Adjusts video playback speed for more efficient processing
* **Summary History**: Keeps track of previously summarized videos for quick reference

## Project Status and Roadmap

### Secure Video Summarizer: Status Report and Implementation Roadmap

#### Executive Summary

The Secure Video Summarizer project consists of a Flask-based backend application and a browser extension that work together to provide automated video summarization capabilities. The system has been enhanced with playback speed control functionality, which allows users to adjust video playback rates while maintaining accurate transcription and summarization.

This section provides a comprehensive overview of the current implementation status, identifies critical next steps, and outlines recommended improvements for future development.

#### Current Implementation Status

##### Backend Application

| Component | Status | Notes |
|-----------|--------|-------|
| Core Flask Application | ✅ Complete | Well-structured with proper separation of concerns |
| API Routes | ✅ Complete | Includes extension endpoints and video processing routes |
| Authentication | ✅ Complete | Google OAuth integration with proper session management |
| Video Processing | ✅ Complete | Supports various video formats and extraction methods |
| Transcription | ✅ Complete | Audio extraction and speech-to-text conversion |
| Summarization | ✅ Complete | Text summarization with configurable options |
| Error Handling | ✅ Complete | Comprehensive error handling with detailed logging |
| Logging | ✅ Complete | Rotating logs with request context and severity levels |
| Testing | ⚠️ Partial | Unit tests present but coverage is incomplete |
| CI/CD | ✅ Complete | GitHub Actions workflows for testing and deployment |
| Installation Scripts | ⚠️ Partial | Development setup scripts exist but no one-click installation |
| Uninstallation | ❌ Missing | No uninstallation script or cleanup process |

##### Browser Extension

| Component | Status | Notes |
|-----------|--------|-------|
| Manifest | ✅ Complete | Properly configured for Chrome/Firefox/Edge |
| Background Script | ✅ Complete | Handles audio capture and backend communication |
| Content Script | ✅ Complete | Detects and interacts with video elements |
| Popup UI | ✅ Complete | User interface for configuration and control |
| Playback Control | ✅ Complete | Recently added feature for speed adjustment |
| Error Handling | ⚠️ Partial | Basic error handling with limited user guidance |
| Testing | ⚠️ Partial | Unit tests for components but limited integration testing |
| Packaging | ⚠️ Partial | Build script exists but no automated distribution |

#### Critical Next Steps

The following items represent the highest priority tasks that should be addressed immediately:

1. **Installation and Deployment**
   - Create a unified installation script for one-click setup
   - Develop a proper uninstallation script with cleanup logging
   - Add desktop integration for easier access

2. **Security Enhancements**
   - Fix session management inconsistencies
   - Implement proper HTTPS enforcement for all communication
   - Enhance file upload validation with content verification
   - Improve secret key management for production environments

3. **Error Handling and User Experience**
   - Enhance error messages with troubleshooting steps
   - Improve network failure handling in the extension
   - Add progress indicators for long-running operations

4. **Testing and Quality Assurance**
   - Increase test coverage to at least 90%
   - Add integration tests for the complete workflow
   - Implement automated security scanning in CI/CD

#### Recommended Improvements

1. **Performance Optimizations**
   - Implement parallel processing for transcription and summarization
   - Add caching for frequently accessed resources
   - Optimize audio processing for different playback rates
   - Consider implementing a job queue for background processing

2. **Architecture Improvements**
   - Refactor for horizontal scaling
   - Implement proper load balancing
   - Add distributed caching
   - Further separate concerns for easier maintenance
   - Create pluggable architecture for different summarization models

3. **User Experience Enhancements**
   - Redesign extension UI for better usability and accessibility
   - Add more options for summary format and style
   - Implement user preferences for default settings
   - Add summary editing capabilities
   - Implement collaborative features for shared summaries

## Documentation

Comprehensive documentation is available in the `docs` directory:

* [API Reference](docs/api_reference.md): Detailed documentation of all API endpoints
* [Browser Extension](docs/browser_extension.md): Architecture and implementation of the browser extension
* [LLM Integration](docs/llm_integration.md): Documentation for Ollama and DeepSeek models integration

## Installation

### Standard Installation (Single-Click Launcher)

SecureVideoSummarizer is packaged as a self-contained application that includes all dependencies. This is the recommended method for most users.

#### macOS Installation:

1. Download the latest release package `SecureVideoSummarizer-macOS.zip` from our releases page
2. Extract the zip file
3. Move the `SecureVideoSummarizer.app` application to your Applications folder
4. Double-click the application icon to launch the application
5. On first launch, you may need to right-click the app and select "Open" to bypass macOS security

#### Windows Installation:

1. Download the latest release package `SecureVideoSummarizer-Windows.zip` from our releases page
2. Extract the zip file to a location of your choice (e.g., `C:\Program Files\SecureVideoSummarizer`)
3. Right-click on `SecureVideoSummarizer.exe` and select "Create shortcut"
4. Move the shortcut to your desktop or Start menu
5. Double-click the shortcut to launch the application

### Configuration

The application will automatically create a configuration file during first launch. You can modify these settings through the application's interface:

1. Launch the application
2. Click on "Settings" in the main menu
3. Configure your Google OAuth credentials and other settings
4. Click "Save" to apply changes

## Usage

### Starting the Application

Simply double-click the application icon (macOS) or shortcut (Windows) to launch the application. The application will:

1. Initialize the virtual environment automatically
2. Start the backend server
3. Open the browser interface (if configured to do so)
4. Connect to Ollama (if installed)

### Processing Local Videos

1. From the main interface, click "Upload Video"
2. Select a video file from your computer
3. Choose summarization options (length, format, focus)
4. Click "Process" to generate a summary
5. View, save, or export the generated summary

### Using with Olympus Learning Platform

1. Install the browser extension from the Chrome Web Store or Firefox Add-ons
2. Navigate to your Olympus learning video
3. Click the SecureVideoSummarizer extension icon
4. Select your summarization preferences
5. Click "Summarize This Video"
6. View the summary in the extension popup or in the main application

## Developer Installation

For developers who want to work on the codebase, follow these instructions:

### Prerequisites

- Python 3.9+ (preferably Python 3.11+)
- Ollama (optional, for advanced LLM features)
- Git

### Setting Up Development Environment

#### On macOS/Linux:

```bash
# Clone the repository
git clone https://github.com/yourusername/SecureVideoSummarizer.git
cd SecureVideoSummarizer/backend

# Run the development setup script
./setup_dev_env.sh

# Activate the virtual environment
source venv/bin/activate

# Run the application in development mode
python -m app.main
```

#### On Windows:

```powershell
# Clone the repository
git clone https://github.com/yourusername/SecureVideoSummarizer.git
cd SecureVideoSummarizer\backend

# Run the development setup script
.\setup_dev_env.bat

# Activate the virtual environment
venv\Scripts\activate

# Run the application in development mode
python -m app.main
```

## API Endpoints

For a complete reference of all API endpoints, see the [API Reference](docs/api_reference.md) documentation.

### Authentication Endpoints

* `GET /auth/login`: Initiates Google OAuth login flow
* `GET /auth/callback`: Handles OAuth callback from Google
* `POST /auth/logout`: Logs out the current user
* `GET /auth/user`: Returns information about the current user

### Video Endpoints

* `POST /video/upload`: Uploads a video file
* `GET /video/<video_id>`: Retrieves a video file
* `DELETE /video/<video_id>`: Deletes a video file

### Summarizer Endpoints

* `POST /summarizer/summarize/<video_id>`: Generates a summary for a video
* `GET /summarizer/summary/<summary_id>`: Retrieves a generated summary

### API Endpoints

* `GET /api/extension/status`: Checks if the extension is properly connected to the backend
* `POST /api/transcribe`: Transcribes and summarizes audio from the React UI

## Summarization Options

The summarization process can be customized with the following options:

### Length Options

* `short`: Generates a concise summary (30-100 words)
* `medium`: Generates a medium-length summary (50-150 words) - default
* `long`: Generates a detailed summary (100-250 words)

### Format Options

* `paragraph`: Returns the summary as a continuous paragraph - default
* `bullets`: Returns the summary as bullet points
* `numbered`: Returns the summary as a numbered list
* `key_points`: Returns the summary as a "KEY POINTS" section with bullet points

### Focus Options

* `key_points`: Focuses on extracting the most important points
* `detailed`: Provides more comprehensive coverage of the content

Example request body for summarization:

```json
{
  "options": {
    "length": "medium",
    "format": "bullets",
    "focus": ["key_points"]
  }
}
```

## LLM Integration

The application supports multiple LLM integration options for summarization:

1. **Ollama**: Local LLM inference using the Ollama framework
2. **Direct Transformers**: HuggingFace Transformers library for local model loading
3. **Extractive Fallback**: Simple extractive summarization when LLMs are unavailable

For detailed configuration and best practices, see the [LLM Integration](docs/llm_integration.md) documentation.

## Testing

For developers, to run the test suite:

```bash
# Make sure you're in the backend directory with the virtual environment activated
./run_tests.py
```

The test suite includes:

* **Unit Tests**: Tests for individual components
* **Integration Tests**: Tests for the complete workflow

## Packaging the Application

### Creating Installation Packages

To create installation packages for distribution:

#### macOS Package:

```bash
# From the project root
./scripts/package_macos.sh
```

This creates a `dist/SecureVideoSummarizer-macOS.zip` file containing the application bundle.

#### Windows Package:

```bash
# From the project root
.\scripts\package_windows.bat
```

This creates a `dist\SecureVideoSummarizer-Windows.zip` file containing the executable and dependencies.

## Browser Extension Integration

The application includes a browser extension for integration with the Olympus Learning Platform. For detailed information on the extension architecture and implementation, see the [Browser Extension](docs/browser_extension.md) documentation.

## Troubleshooting

### Common Installation Issues

1. **Application Won't Start (macOS)**
   - Check if you're running the latest macOS version
   - Try right-clicking the app and selecting "Open" to bypass Gatekeeper
   - Check the logs in `~/Library/Logs/SecureVideoSummarizer/`

2. **Application Won't Start (Windows)**
   - Ensure you have the latest Microsoft Visual C++ Redistributable installed
   - Run the application as administrator for the first launch
   - Check the logs in `%APPDATA%\SecureVideoSummarizer\Logs\`

3. **Ollama Integration Issues**
   - Ensure Ollama is installed: Download from [ollama.ai](https://ollama.ai)
   - Start Ollama manually: `ollama serve`
   - Pull the required model: `ollama pull llama2:7b`

### Getting Support

If you encounter issues not covered in this documentation, please:

1. Check the detailed logs in the application's log directory
2. Visit our support forum at [forum.securevideosummarizer.com](https://forum.securevideosummarizer.com)
3. Open an issue on our GitHub repository

## License

This project is licensed under the MIT License - see the LICENSE file for details. 