# SVS Dashboard Setup and Usage

This document provides instructions for setting up and running the Secure Video Summarizer (SVS) Admin Dashboard.

## Overview

The SVS Admin Dashboard provides a web interface for:
- Monitoring job progress in real-time
- Viewing and managing video summaries
- Checking system health and logs
- Managing application settings

## Running the Dashboard

The dashboard runs on port 8080, separate from the main application server which runs on port 8081.

### Basic Usage

To start the dashboard with default settings:

```bash
cd backend
./run_dashboard.sh
```

This will:
1. Create a virtual environment (if needed)
2. Install required dependencies
3. Start the dashboard server on http://localhost:8080

### Command Line Parameters

The dashboard script accepts several parameters to customize its behavior:

```bash
./run_dashboard.sh [--install-deps] [--update] [--port PORT] [--no-debug]
```

#### Available Parameters

| Parameter | Description |
|-----------|-------------|
| `--install-deps` | Force installation of dependencies even if previously installed |
| `--update` | Update all packages to latest versions |
| `--port PORT` | Specify a custom port (default: 8080) |
| `--no-debug` | Run in production mode (no debug) |
| `--config CONFIG` | Specify configuration profile (development, production, testing) |

#### Examples

**Force reinstallation of dependencies:**
```bash
./run_dashboard.sh --install-deps
```

**Update all packages:**
```bash
./run_dashboard.sh --update
```

**Run on a custom port:**
```bash
./run_dashboard.sh --port 9090
```

**Run in production mode:**
```bash
./run_dashboard.sh --no-debug --config production
```

## Accessing the Dashboard

Once running, the dashboard is accessible at:

- Main dashboard: http://localhost:8080/dashboard
- Jobs page: http://localhost:8080/dashboard/jobs
- Logs view: http://localhost:8080/dashboard/logs
- System info: http://localhost:8080/dashboard/system

## Troubleshooting

### Missing Dependencies

If you encounter missing dependencies, you can install them directly:

```bash
cd backend
source venv/bin/activate
pip install elevenlabs flask-cors
```

### Port Conflicts

If port 8080 is already in use, you can specify a different port:

```bash
./run_dashboard.sh --port 9090
```

### Environment Issues

Make sure your environment variables are correctly set in the `.env` file in the backend directory. 
For development, you can copy the `.env.example` file to `.env` and adjust as needed.

## Notes on Port Configuration

- **Port 8080**: Used for the dashboard and extension communication
- **Port 8081**: Used for the main application server

Do not change these port assignments unless you update all corresponding references throughout the codebase. 