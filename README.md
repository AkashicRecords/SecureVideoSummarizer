# Secure Video Summarizer

A Chrome extension and backend service to securely summarize video content using local AI processing.

## Features

- Chrome extension for detecting and processing videos from various platforms
- Secure summarization of video content using local AI
- Support for YouTube and Olympus LMS video platforms
- Transcript generation and summarization
- Self-hosted backend for enhanced privacy
- Real-time job progress tracking in dashboard
- Cross-platform compatibility (Linux, macOS, Windows)

## Documentation

The project documentation is split into two main sections:

1. [Logical Data Flow](docs/Logical_Data_Flow.md) - Detailed technical documentation of the system's data flow and component interactions
2. [Architecture Diagrams](docs/architecture_diagrams.md) - Visual representations of the system architecture and data flow

## Installation Options

### Option 1: Easy Install Script

```bash
# Clone the repository
git clone https://github.com/yourusername/secure-video-summarizer.git
cd secure-video-summarizer

# Run the installation script
chmod +x install.sh
./install.sh
```

### Option 2: Docker Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/secure-video-summarizer.git
cd secure-video-summarizer

# Build and start the Docker containers
docker-compose up -d
```

### Option 3: Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/secure-video-summarizer.git
cd secure-video-summarizer

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup the Chrome extension
cd extension
npm install
npm run build
cd ..

# Start the backend service
cd backend
flask run --port=8081 --debug
```

## Usage

1. Start the application using one of the startup scripts:
   
   **Shell script (Linux/macOS)**:
   ```
   ./start_svs_application.sh
   ```
   
   **Python script (Cross-platform)**:
   ```
   python start_svs_application.py
   ```
   
   The startup script provides multiple startup modes and configuration options. For more details, see the [SVS_STARTUP_GUIDE.md](SVS_STARTUP_GUIDE.md).

2. Open your browser and navigate to:
   - Dashboard: `http://localhost:8080/dashboard`
   - API Server: `http://localhost:8081`

3. Use the dashboard to upload videos, create summaries, and track job progress.

4. When you're done, stop the application using one of the shutdown scripts:
   
   **Shell script (Linux/macOS)**:
   ```
   ./stop_svs_application.sh
   ```
   
   **Python script (Cross-platform)**:
   ```
   python stop_svs_application.py
   ```
   
   For shutdown details, see the [SVS_SHUTDOWN_GUIDE.md](SVS_SHUTDOWN_GUIDE.md).

## Configuration

The application can be configured using environment variables in a `.env` file:

```
SECRET_KEY=your_secret_key
FLASK_ENV=production
OLLAMA_API_URL=http://localhost:11434/api
```

## Cross-Platform Compatibility

SVS now includes Python scripts for cross-platform compatibility:

- `start_svs_application.py`: Main startup script (replaces shell script)
- `stop_svs_application.py`: Clean shutdown script
- `backend/run_backend.py`: Backend server launcher
- `backend/run_dashboard.py`: Dashboard server launcher

These scripts provide identical functionality to the original shell scripts but work on all platforms including Windows. Key features include:

- OS detection for platform-specific behavior
- Proper Python virtual environment management
- Process handling using Python's subprocess module
- Support for online and offline installation modes
- Comprehensive logging for troubleshooting

To install the Python dependencies for these scripts:

```bash
pip install -r requirements-system.txt
```

## Job Progress Tracking

The application includes a robust job progress tracking system that allows you to:

- Monitor the status of video summarization jobs in real-time
- See detailed progress for each processing stage (audio extraction, transcription, summarization)
- View completion status and results through the dashboard interface

To test the progress tracking functionality:

```bash
# Generate a test video and run the summarization with progress tracking
chmod +x test_progress_tracking.sh
./test_progress_tracking.sh
```

For more details, see [README-progress-tracking.md](README-progress-tracking.md).

## Startup and Shutdown

The SVS application includes intelligent startup and shutdown scripts for managing the application lifecycle:

- Shell scripts (Linux/macOS):
  - `start_svs_application.sh`: Interactive startup with multiple modes
  - `stop_svs_application.sh`: Clean shutdown and cleanup

- Python scripts (Cross-platform including Windows):
  - `start_svs_application.py`: Cross-platform interactive startup
  - `stop_svs_application.py`: Cross-platform clean shutdown
  - `backend/run_backend.py`: Backend server launcher
  - `backend/run_dashboard.py`: Dashboard server launcher

All scripts provide:
- Automatic dependency installation
- Progress tracking
- Multiple startup modes
- Offline installation support

For comprehensive startup instructions, see the [SVS_STARTUP_GUIDE.md](SVS_STARTUP_GUIDE.md).
For shutdown instructions, see the [SVS_SHUTDOWN_GUIDE.md](SVS_SHUTDOWN_GUIDE.md).

## Offline Installation

SVS supports offline installation for environments without internet access:

1. On a machine with internet, run:
   ```
   ./package_dependencies.sh
   ```
   This packages all dependencies with exact versions locked to those in requirements.lock.

2. Transfer the entire directory to the target machine

3. On the target machine, use one of these methods:
   - Run `./install_offline.sh`
   - Run `python start_svs_application.py --offline`
   - Or select "Offline installation" option when running the interactive script

All dependencies are installed with strict version control to prevent conflicts. For complete offline installation instructions, see the [SVS_OFFLINE_INSTALL_GUIDE.md](SVS_OFFLINE_INSTALL_GUIDE.md).

## Automatic Updates

SVS includes an automatic update checking system:

1. During Cold Start, the application checks for approved updates from the official repository
2. Requires internet connection (gracefully handles offline situations with a countdown)
3. Only applies updates that have been tested and approved by the SVS team
4. Provides detailed information about what will be updated before applying changes

You can configure the update source by setting these environment variables:
```bash
# Set these before running the startup script
export SVS_REPO_URL="https://raw.githubusercontent.com/secure-video-summarizer/SVS"
export SVS_BRANCH="main"
export SVS_REQ_PATH="backend/requirements.lock"
```

This ensures your installation stays up-to-date with the latest security patches and bug fixes while maintaining stability.

## Supported Platforms

- YouTube
- Olympus LMS

## License

MIT License
