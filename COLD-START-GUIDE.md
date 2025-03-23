# SVS Cold Start Guide

This guide walks you through the process of starting the Secure Video Summarizer application from a cold start.

## Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- pip
- Node.js and npm (for the extension)
- Git
- ffmpeg (for video processing)

## Step 1: Clone the Repository (if needed)

```bash
git clone https://github.com/yourusername/secure-video-summarizer.git
cd secure-video-summarizer
```

## Step 2: Start the Backend Server

The backend server runs on port 8081 and handles the core video processing functionality.

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
flask run --port=8081 --debug
```

Keep this terminal window open. The backend server should now be running on http://localhost:8081.

## Step 3: Start the Dashboard Server

The dashboard server runs on port 8080 and provides a web interface for monitoring jobs and managing the application.

Open a new terminal window:

```bash
# Navigate to the project directory
cd /path/to/secure-video-summarizer

# Navigate to the backend directory
cd backend

# Run the dashboard with dependencies installation
./run_dashboard.sh --install-deps --update
```

This script will:
1. Create a virtual environment if needed
2. Install or update all required dependencies
3. Start the dashboard server on http://localhost:8080

The dashboard should now be accessible at:
- Main dashboard: http://localhost:8080/dashboard
- Jobs page: http://localhost:8080/dashboard/jobs

## Step 4: Install and Configure the Chrome Extension

```bash
# Navigate to the project directory
cd /path/to/secure-video-summarizer

# Navigate to the extension directory
cd extension

# Install dependencies
npm install

# Build the extension
npm run build
```

Now load the extension in Chrome:
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" using the toggle in the top-right corner
3. Click "Load unpacked" and select the `extension/dist` folder
4. The SVS extension icon should appear in your browser toolbar

## Step 5: Verify the Setup

### Check Backend Server
- Open a browser and navigate to http://localhost:8081/api/health
- You should see a JSON response indicating the server is healthy

### Check Dashboard
- Open a browser and navigate to http://localhost:8080/dashboard
- You should see the SVS dashboard interface

### Check Extension
1. Navigate to a supported video (YouTube or Olympus LMS)
2. Click the SVS extension icon in the browser toolbar
3. The extension popup should appear and recognize the video

## Step 6: Create a Test Summarization Job

To verify the entire workflow:

```bash
# Navigate to the project directory
cd /path/to/secure-video-summarizer

# Run the test script to create a sample video and summarization job
./test_progress_tracking.sh
```

This will:
1. Generate a test video
2. Upload it to the backend
3. Create a summarization job
4. Track the progress in the terminal

In parallel, you can:
- Open http://localhost:8080/dashboard/jobs to see the job progress in the dashboard

## Troubleshooting

### Missing Dependencies
If you encounter "module not found" errors:

```bash
# For backend dependencies
cd backend
source venv/bin/activate
pip install elevenlabs flask-cors flask-session flask-limiter python-magic

# For extension dependencies
cd extension
npm install
```

### Port Conflicts
If the ports are already in use:

```bash
# For backend server
cd backend
flask run --port=8082 --debug  # Use a different port

# For dashboard server
cd backend
./run_dashboard.sh --port 8083  # Use a different port
```

Remember to update extension configurations to point to the new ports.

### Extension Not Working
If the extension doesn't connect to the backend:
1. Check that both servers are running
2. Verify that the extension is configured to use the correct API endpoint
3. Check extension's developer console for error messages

## Shutting Down

To stop the application:
1. In both terminal windows (backend and dashboard), press Ctrl+C
2. Deactivate the virtual environments: `deactivate` 