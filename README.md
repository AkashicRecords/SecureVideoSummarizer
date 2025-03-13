# Secure Video Summarizer

A secure application for summarizing video content with privacy-focused features.

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

4. Run the application:
   ```
   python app/main.py
   ```

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
- SpeechRecognition: For transcribing audio to text
- Transformers: For text summarization using pre-trained models
- PyTorch: Required by Transformers
- FFmpeg-Python: Python bindings for FFmpeg

## Testing

To test the summarization functionality:

1. Upload a video using the `/video/upload` endpoint
2. Use the returned video ID to request a summary via `/summarizer/summarize/<video_id>`
3. Retrieve the summary using the returned summary ID via `/summarizer/summary/<summary_id>` 