# YouTube Integration

## Overview

The YouTube integration enables the Secure Video Summarizer to detect, capture, and process videos from YouTube.com. This integration allows users to generate transcripts and summaries of YouTube videos while maintaining privacy and security. The system works directly within the user's browser via the Chrome extension, with processing handled by the local backend server.

## Installation

### Prerequisites

- Secure Video Summarizer backend server installed and running
- Chrome browser (version 88 or higher)
- Chrome extension installed
- Python 3.8+ with required packages:
  - `yt-dlp` for video downloading capabilities
  - `ffmpeg` for audio extraction

### Installation Steps

1. Install required Python packages:
   ```bash
   pip install yt-dlp
   ```

2. Install ffmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. Verify the installation:
   ```bash
   python -c "import yt_dlp; print('yt-dlp installed successfully')"
   ffmpeg -version
   ```

## Setup & Configuration

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `YOUTUBE_DOWNLOAD_LOCATION` | `./temp` | Directory where YouTube videos are temporarily stored |
| `YOUTUBE_VIDEO_FORMAT` | `best[height<=720]` | Format specification for video downloads |
| `YOUTUBE_TIMEOUT` | `120` | Timeout in seconds for download operations |
| `YOUTUBE_MAX_FILESIZE` | `500MB` | Maximum allowed file size for downloads |

### Environment Setup

Add the following to your `.env` file:

```
# YouTube configuration
YOUTUBE_DOWNLOAD_LOCATION=./temp
YOUTUBE_VIDEO_FORMAT=best[height<=720]
YOUTUBE_TIMEOUT=120
YOUTUBE_MAX_FILESIZE=500MB
```

### Getting Started

1. Ensure the backend server is running:
   ```bash
   cd backend
   python app.py
   ```

2. Navigate to any YouTube video in Chrome
3. Click the Secure Video Summarizer extension icon
4. Select "Generate Summary" to process the video

## Troubleshooting

### Common Issues

#### Issue: Video Cannot Be Downloaded

**Symptoms:**
- Error message: "Failed to download video"
- 500 error in extension response

**Causes:**
- Video might be age-restricted or private
- Network connectivity issues
- Missing or outdated yt-dlp

**Solutions:**
- Update yt-dlp: `pip install -U yt-dlp`
- Check network connectivity
- Verify the video is publicly accessible
- Check logs at `backend/logs/app.log` for specific error details

#### Issue: Audio Extraction Fails

**Symptoms:**
- Error message: "Could not extract audio"
- Processing stops after download completes

**Causes:**
- Missing or incorrectly installed ffmpeg
- Corrupted video download
- Unsupported video format

**Solutions:**
- Reinstall ffmpeg and ensure it's in PATH
- Clear the temp directory: `rm -rf ./temp/*`
- Try with a different video to verify the issue
- Check logs for ffmpeg-specific errors

### Logging

Enable verbose logging for YouTube operations:

1. Edit `backend/config.py` to set:
   ```python
   YOUTUBE_DEBUG = True
   LOG_LEVEL = "DEBUG"
   ```

2. Check logs at `backend/logs/app.log` for detailed information

## Under the Hood

### Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌────────────────┐
│ Chrome Extension│──────▶ Backend Server  │──────▶ YouTubeHandler │
└─────────────────┘      └─────────────────┘      └────────────────┘
                                                          │
                                                          ▼
                                                  ┌────────────────┐
                                                  │  yt-dlp API    │
                                                  └────────────────┘
                                                          │
                                                          ▼
                                                  ┌────────────────┐
                                                  │  Video/Audio   │
                                                  │  Processing    │
                                                  └────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/app/api/youtube_routes.py` | API endpoints for YouTube operations |
| `backend/app/services/youtube_service.py` | Service layer for YouTube processing |
| `backend/app/utils/youtube_downloader.py` | Handles YouTube video downloading |
| `extension/src/services/youtube-detector.js` | Detects YouTube videos in the browser |

### API Reference

#### Endpoint: `/api/youtube/process`

**Method:** POST

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `video_url` | string | Yes | URL of the YouTube video |
| `start_time` | integer | No | Start time in seconds (default: 0) |
| `end_time` | integer | No | End time in seconds (default: end of video) |

**Response:**

```json
{
  "status": "success",
  "session_id": "youtube-12345",
  "transcript": "Full video transcript...",
  "summary": "Video summary...",
  "metadata": {
    "title": "Video Title",
    "duration": 300,
    "channel": "Channel Name"
  }
}
```

### Data Flow

1. **Video Detection**:
   - Extension detects YouTube video on page
   - Extension extracts video URL and metadata

2. **Processing Request**:
   - Extension sends video URL to backend
   - Backend validates the URL

3. **Video Download**:
   - YouTube downloader fetches video
   - Video stored temporarily in configured location

4. **Audio Extraction**:
   - ffmpeg extracts audio from video
   - Audio converted to appropriate format

5. **Transcription & Summarization**:
   - Audio sent to transcription service
   - Transcript processed for summary
   - Results returned to extension

### Integration Points

- **Browser Extension**: Detects YouTube videos and sends URLs to backend
- **Transcription Service**: Receives audio data from YouTube handler
- **LLM Service**: Processes transcript for summarization
- **Session Manager**: Stores processing results and history

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial YouTube integration |
| 1.1.0 | 2025-02-10 | Added support for age-restricted videos |
| 1.2.0 | 2025-03-05 | Improved error handling and logging | 