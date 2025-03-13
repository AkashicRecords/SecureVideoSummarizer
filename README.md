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

# Here is the step-by-step plan for developing the application:

## Set Up the Project Structure:

- Create the main project directory and subdirectories for the backend and frontend.
- Initialize a Git repository.

## Create the .gitignore File:

- Add entries to ignore unnecessary files and directories.

## Initialize the Backend:

- Set up a virtual environment for the Python backend.
- Install necessary dependencies (e.g., Flask, PyInstaller, etc.).
- Create the initial backend files and directories.

## Implement the Backend Functionality:

- Develop the authentication module using Google SSO.
- Implement video access and summarization features.
- Set up logging and error handling.

## Initialize the Frontend:

- Create a new React application using Create React App.
- Set up the project structure for components and assets.

## Implement the Frontend Functionality:

- Develop components for user authentication, video input, and summary display.
- Integrate the frontend with the backend API.

## Set Up Testing Frameworks:

- Install and configure testing libraries for both backend and frontend.
- Write unit tests and integration tests.

## Set Up CI/CD with GitHub Actions:

- Create workflows for testing and deployment.
- Ensure that the workflows include steps for removing test artifacts and optimizing the application.

## Documentation:

- Write the README.md file with project details, installation instructions, and CI/CD badges.
- Document the Llama installation process and integration.

## Final Testing and Deployment:

- Test the application thoroughly on both Windows and macOS.
- Deploy the application using the CI/CD pipeline.

## Iterate and Improve:

- Gather user feedback and make necessary improvements.

