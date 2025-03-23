# SVS Application Startup Guide

This guide explains how to start and configure the Secure Video Summarizer (SVS) application.

## Quick Start

For a standard startup with default settings:

```bash
./start_svs_application.sh
```

This will:
1. Clean up any existing instances of the application
2. Start both the backend server (port 8081) and dashboard (port 8080)
3. Install necessary dependencies

## Startup Options

The startup script provides both interactive and command-line options:

### Interactive Menu

When run without parameters, the script displays an interactive menu:

```
======= SVS STARTUP OPTIONS =======

Please select a startup mode:
  1) Standard startup (backend + dashboard)
  2) Backend server only
  3) Dashboard server only
  4) Cold start (clean install with dependencies)
  5) Development mode (with debug options)
  6) Custom configuration
  7) Exit
```

Select the appropriate option by entering its number.

### Auto-Continue with Previous Configuration

After a successful startup, the script saves your configuration. On the next run, it will:
- Display your last successful configuration
- Automatically continue with this configuration after a 5-second countdown
- Allow you to press any key during the countdown to see the full menu instead

This feature helps you quickly restart with your preferred settings without manual selection each time.

### Command-Line Options

For automated deployments or specific configurations, you can use command-line options:

```bash
./start_svs_application.sh [options]
```

Available options:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--skip-deps` | Skip dependency installation |
| `--force-update-deps` | Force update dependencies |
| `--backend-only` | Start only the backend server |
| `--dashboard-only` | Start only the dashboard server |
| `--backend-port PORT` | Set custom backend port (default: 8081) |
| `--dashboard-port PORT` | Set custom dashboard port (default: 8080) |
| `--debug` | Run in debug mode |

### Examples

```bash
# Start everything with default settings
./start_svs_application.sh

# Start only the backend server
./start_svs_application.sh --backend-only

# Force update all dependencies
./start_svs_application.sh --force-update-deps

# Run backend on custom port
./start_svs_application.sh --backend-port 8000

# Cold start with debugging enabled
./start_svs_application.sh --force-update-deps --debug
```

## Custom Configuration

When selecting "Custom configuration" from the interactive menu, you can:

1. Enable/disable backend server
2. Set custom backend port
3. Enable/disable dashboard server
4. Set custom dashboard port
5. Control dependency installation/updates
6. Enable/disable debug mode

## Startup Process

The startup script performs the following steps:

### Preliminary Steps
- Deactivates any active virtual environments
- Runs the shutdown script to clean up existing instances
- Verifies all ports are clear and the environment is clean

### Backend Server Setup
- Creates/activates backend virtual environment if needed
- Installs required dependencies 
- Starts the backend Flask server on the configured port

### Dashboard Server Setup
- Runs the dashboard startup script with appropriate options
- Configures the dashboard port as needed

### Verification
- Checks that services are properly running
- Displays access URLs for the backend and dashboard
- Saves successful configuration for future startups

## Stopping the Application

To stop the application, use the shutdown script:

```bash
./stop_svs_application.sh
```

For stubborn processes, use the force option:

```bash
./stop_svs_application.sh --force
```

## Troubleshooting

### Virtual Environment Issues
If the script can't deactivate virtual environments automatically, you'll see:
```
Deactivating virtual environment.......Failed!
```
In this case, manually run `deactivate` and try again.

### Port Already in Use
If ports are already in use, the script will try to free them. If unsuccessful:
```
CRITICAL ERROR: Could not clear ports after 3 attempts.
```
Manually check and kill processes on the required ports:
```bash
lsof -i :8080 -i :8081
kill -9 <PID>
```

### Backend Failed to Start
If the backend server won't start, check:
1. Python dependencies are correctly installed
2. Required environment variables are set
3. No conflicting processes are using port 8081

### Dashboard Failed to Start
If the dashboard won't start, check:
1. Backend server is running (dashboard requires the backend)
2. Required Node.js modules are installed
3. No conflicting processes are using port 8080

## Job Progress Tracking Testing

After startup, test the job progress tracking with:

```bash
./test_progress_tracking.sh
```

This will upload a test video, create a summary job, and display the progress.

### Cold Start Mode

The **Cold Start** option provides a complete clean installation with all dependencies. This is useful for:

- First-time setup
- Resolving dependency issues
- Ensuring all components are up-to-date
- Starting fresh after system changes

When you select Cold Start, the following actions are performed:

1. **Update Check**: The system checks for approved application updates from the official GitHub repository
   - Internet connection is required for this step
   - If no connection is available, the system will continue without updates after a 5-second countdown
   - If connection is available but no updates are found, it displays "No new updates found"
   - If updates are available, it displays a list of changes and asks for confirmation
   - You can press Ctrl+C during the countdown to abort startup and check your network connection
   - Updates are only downloaded if approved by the SVS team
   - You can configure the update source with these environment variables:
     ```bash
     export SVS_REPO_URL="https://raw.githubusercontent.com/secure-video-summarizer/SVS"
     export SVS_BRANCH="main"
     export SVS_REQ_PATH="backend/requirements.lock"
     ```

2. **Clean Environment**: Any existing virtual environments are deactivated

3. **Dependency Installation**: All required dependencies are installed fresh

4. **Full Configuration**: Both backend and dashboard services are configured

The Cold Start option is the safest way to update dependencies as it ensures a clean installation without conflicts from existing packages. 