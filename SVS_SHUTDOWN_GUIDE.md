# SVS Application Shutdown Guide

This guide explains how to safely shut down the Secure Video Summarizer (SVS) application.

## Quick Shutdown

For a standard shutdown with default settings:

```bash
./stop_svs_application.sh
```

This will:
1. Deactivate any active virtual environments
2. Stop the backend server running on port 8081
3. Stop the dashboard server running on port 8080
4. Verify all services have been properly terminated

## Shutdown Options

The shutdown script provides the following command-line options:

```bash
./stop_svs_application.sh [options]
```

Available options:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--force` | Use aggressive methods to terminate processes |

### Examples

```bash
# Standard shutdown procedure
./stop_svs_application.sh

# Force termination of all processes
./stop_svs_application.sh --force
```

## Shutdown Process

The shutdown script performs the following steps:

### Step 1: Clean Environment
- Checks for active virtual environments
- Safely deactivates any active Python environments

### Step 2: Stop Backend Server
- Checks for backend process using the saved PID file
- Terminates the backend process if running
- Ensures port 8081 is free by killing any process using it

### Step 3: Stop Dashboard Server
- Checks for dashboard process using the saved PID file
- Terminates the dashboard process if running
- Ensures port 8080 is free by killing any process using it

### Step 4: Verification
- Verifies all ports are free
- Checks for any residual Flask or dashboard processes
- Reports the final status of the environment cleanup

## Force Mode

When standard termination methods fail, you can use force mode:

```bash
./stop_svs_application.sh --force
```

In force mode, the script:
- Skips gentle termination signals (SIGTERM)
- Uses aggressive termination signals (SIGKILL) immediately
- Attempts additional system-specific force quit methods
- Provides more detailed error messages for manual intervention

## Troubleshooting

### Processes Won't Terminate

If processes refuse to terminate even with the force option:

1. Identify the processes:
   ```bash
   ps aux | grep flask
   ps aux | grep python
   lsof -i :8080 -i :8081
   ```

2. Manually terminate them:
   ```bash
   kill -9 <PID>
   ```

3. For macOS, you can also use:
   ```bash
   pkill -9 -f "flask run"
   pkill -9 -f "run_dashboard.sh"
   ```

### Virtual Environment Won't Deactivate

If the virtual environment won't deactivate automatically:

1. Manually run:
   ```bash
   deactivate
   ```

2. If that doesn't work, start a new terminal session before running the shutdown script again.

### PID Files Missing

If the script reports "No PID file found" but services are still running:

1. The application might have been started outside the standard scripts
2. Use port-based termination:
   ```bash
   lsof -ti :8080 :8081 | xargs kill -9
   ```

## Verifying Complete Shutdown

After running the shutdown script, verify everything is stopped:

```bash
# Check if ports are still in use
lsof -i :8080 -i :8081

# Check for any related processes
ps aux | grep flask
ps aux | grep "run_dashboard"

# Verify no Python processes related to SVS are running
ps aux | grep python | grep -v grep
```

If no output appears from these commands, the shutdown was successful.

## Automatic Cleanup Before Starting

Note that the `start_svs_application.sh` script automatically runs the shutdown procedure before starting, so in many cases, you don't need to manually run the shutdown script unless you specifically want to stop the application without restarting it. 