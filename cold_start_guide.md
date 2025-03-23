# Secure Video Summarizer (SVS) - Cold Start Guide

This guide provides step-by-step instructions for setting up and running the Secure Video Summarizer application from scratch. Follow these steps in order to ensure a successful setup.

## Prerequisites

- Python 3.9+ installed
- `pip` package manager
- `ffmpeg` installed for audio extraction
- `git` for cloning the repository (if applicable)
- `lsof` command available for checking port usage

## Setup and Installation

### Step 1: Clone the Repository (if applicable)

```bash
git clone <repository-url>
cd SVS
```

### Step 2: Set up the Environment

The SVS application consists of two main components:
- Backend server (Flask-based API)
- Dashboard server (for monitoring and management)

Both components have their own virtual environments and dependencies.

#### 2.1 Backend Environment Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies
pip install elevenlabs flask-cors flask-session flask-limiter python-magic

# Deactivate when done
deactivate
```

#### 2.2 Dashboard Environment Setup

```bash
# While in the backend directory
# Create a separate virtual environment for the dashboard
python3 -m venv dashboard_venv

# The dashboard setup is handled by the run_dashboard.sh script
chmod +x run_dashboard.sh
```

## Running the Application

### Using the Automated Scripts

We provide two scripts for easy management of the application:

#### Starting the Application

```bash
# Make the script executable
chmod +x start_svs_application.sh

# Run the script
./start_svs_application.sh
```

This script:
1. Shuts down any existing instances of the application
2. Sets up and activates the backend virtual environment
3. Installs all required dependencies
4. Starts the backend server on port 8081
5. Starts the dashboard server on port 8080
6. Verifies that all services are running
7. Provides access information

#### Stopping the Application

```bash
# Make the script executable
chmod +x stop_svs_application.sh

# Run the script
./stop_svs_application.sh
```

This script:
1. Deactivates any active virtual environments
2. Stops the backend server
3. Stops the dashboard server
4. Verifies that all services have stopped

### Manual Startup Process

If you prefer to start the application manually, follow these steps:

#### Step 1: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Activate the virtual environment
source venv/bin/activate

# Start the Flask server
flask run --port=8081 --debug
```

#### Step 2: Start the Dashboard Server

In a new terminal:

```bash
# Navigate to the backend directory
cd backend

# Run the dashboard script
./run_dashboard.sh --install-deps --update
```

## Access Information

After starting the application, you can access:

- Backend server: http://localhost:8081
- Dashboard: http://localhost:8080/dashboard
- Jobs page: http://localhost:8080/dashboard/jobs

## Testing Job Progress Tracking

To test the job progress tracking functionality:

```bash
# Make the test script executable
chmod +x test_progress_tracking.sh

# Run the test script
./test_progress_tracking.sh
```

## Troubleshooting

### Port Already in Use

If you encounter an error about ports being in use:

```bash
# Check what's using the port (replace PORT with 8080 or 8081)
lsof -i :PORT

# Kill the process (replace PID with the process ID)
kill -9 PID
```

### Virtual Environment Issues

If you encounter issues with the virtual environment:

```bash
# Remove the existing environments
rm -rf backend/venv backend/dashboard_venv

# Recreate them following steps 2.1 and 2.2
```

### Dependencies Issues

If dependencies fail to install:

```bash
# Make sure pip is up to date
pip install --upgrade pip

# Try reinstalling the dependencies
pip install -r requirements.txt
```

## System Architecture

The Secure Video Summarizer consists of:

1. **Backend Server (Port 8081)**
   - Handles video uploads
   - Processes videos through extraction, transcription, and summarization
   - Manages job tracking and progress updates
   - Provides API endpoints for the frontend

2. **Dashboard Server (Port 8080)**
   - Provides a web interface for monitoring
   - Displays job statuses and progress
   - Allows access to logs and system information

## Next Steps

After successfully setting up the application, you can:

1. Upload videos through the API
2. Monitor job progress in the dashboard
3. Retrieve video summaries
4. Check logs for any issues

For more detailed information, refer to the API documentation available at: http://localhost:8080/dashboard/docs 