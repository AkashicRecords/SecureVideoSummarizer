# Secure Video Summarizer

A secure application for summarizing video content with privacy-focused features.

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
- `DELETE /video/<video_id>`: Deletes a video file

### Summarizer Endpoints
- `POST /summarizer/summarize/<video_id>`: Generates a summary for a video
- `GET /summarizer/summary/<summary_id>`: Retrieves a generated summary

## Error Handling

The application uses a centralized error handling system:

- **Custom APIError Class**: For consistent error responses
- **Global Error Handlers**: Registered for common HTTP error codes (400, 404, 405, 500)
- **Structured Error Responses**: All errors return JSON with error message and status code
- **Detailed Logging**: All errors are logged with context information

Example error response:
```json
{
  "error": "Invalid video format",
  "status_code": 400
}
```

## Testing

To test the summarization functionality:

1. Upload a video using the `/video/upload` endpoint
2. Use the returned video ID to request a summary via `/summarizer/summarize/<video_id>`
3. Retrieve the summary using the returned summary ID via `/summarizer/summary/<summary_id>`

## Security Considerations

- Always use HTTPS in production
- Regularly rotate the SECRET_KEY
- Set appropriate file permissions for sensitive files
- Keep dependencies updated to patch security vulnerabilities
- Use a production-grade web server (e.g., Gunicorn) with a reverse proxy (e.g., Nginx)
- Consider using a secrets manager for production deployments

## Development Plan

### Set Up the Project Structure:
- Create the main project directory and subdirectories for the backend and frontend.
- Initialize a Git repository.

### Create the .gitignore File:
- Add entries to ignore unnecessary files and directories.

### Initialize the Backend:
- Set up a virtual environment for the Python backend.
- Install necessary dependencies (e.g., Flask, PyInstaller, etc.).
- Create the initial backend files and directories.

### Implement the Backend Functionality:
- Develop the authentication module using Google SSO.
- Implement video access and summarization features.
- Set up logging and error handling.

### Initialize the Frontend:
- Create a new React application using Create React App.
- Set up the project structure for components and assets.

### Implement the Frontend Functionality:
- Develop components for user authentication, video input, and summary display.
- Integrate the frontend with the backend API.

### Set Up Testing Frameworks:
- Install and configure testing libraries for both backend and frontend.
- Write unit tests and integration tests.

### Set Up CI/CD with GitHub Actions:
- Create workflows for testing and deployment.
- Ensure that the workflows include steps for removing test artifacts and optimizing the application.

### Documentation:
- Write the README.md file with project details, installation instructions, and CI/CD badges.
- Document the Llama installation process and integration.

### Final Testing and Deployment:
- Test the application thoroughly on both Windows and macOS.
- Deploy the application using the CI/CD pipeline.

### Iterate and Improve:
- Gather user feedback and make necessary improvements.

