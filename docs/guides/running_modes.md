# Running the Secure Video Summarizer

This guide documents how to run the Secure Video Summarizer application in various modes (debug, production, command-line) and environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Debug Mode](#debug-mode)
- [Production Mode](#production-mode)
- [Command-Line Mode](#command-line-mode)
- [Environment Variables](#environment-variables)
- [Logging](#logging)
- [Common Issues](#common-issues)

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8 or higher
- Node.js 14.0 or higher (for the browser extension)
- yt-dlp (`pip install yt-dlp`)
- ffmpeg (system dependency)
- pip dependencies: `pip install -r backend/requirements.txt`

## Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/AkashicRecords/SecureVideoSummarizer.git
   cd SecureVideoSummarizer
   ```

2. Set up a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Set up the logs directory (optional but recommended):
   ```bash
   ./scripts/setup_logs_folder.sh
   ```

## Debug Mode

Debug mode provides verbose output, detailed error messages, and enables hot-reloading for development purposes.

### Starting the Backend in Debug Mode

```bash
cd backend
python main.py --debug
```

Or with environment variables:

```bash
cd backend
DEBUG=true python main.py
```

### Features of Debug Mode

- Detailed logging (INFO and DEBUG level messages)
- Automatic reloading when code changes
- Enhanced error reporting with tracebacks
- Disabled API rate limiting
- Test endpoints available
- Memory profiling enabled

### Testing in Debug Mode

Run test scripts with the verbose flag for detailed output:

```bash
cd backend
python test_olympus_video.py --test all --verbose
```

## Production Mode

Production mode optimizes for performance, security, and stability with reduced logging verbosity.

### Starting the Backend in Production Mode

```bash
cd backend
python main.py --production
```

Or using the production server script:

```bash
cd backend
./scripts/start_production_server.sh
```

### Using a WSGI Server (Recommended for Production)

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:8080 "app:create_app()"
```

### Features of Production Mode

- Optimized for performance
- Minimized logging (WARNING and ERROR only)
- API rate limiting enabled
- Test endpoints disabled
- Security features fully enabled
- Redis caching for improved response times (if configured)

## Command-Line Mode

The command-line mode enables processing videos without running the full web server.

### Processing a Video URL from Command Line

```bash
cd backend
python cli.py process-video --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output summary.txt
```

### Batch Processing Multiple Videos

```bash
cd backend
python cli.py batch-process --input urls.txt --output-dir ./summaries
```

### Available Command-Line Arguments

- `--url`: Video URL to process
- `--output`: File to save the summary
- `--transcript`: Also save the transcript
- `--format`: Output format (text, json, markdown)
- `--no-cache`: Disable caching
- `--verbose`: Enable verbose output

## Environment Variables

The application can be configured using environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DEBUG` | Enable debug mode | `false` |
| `PORT` | Server port | `8080` |
| `HOST` | Server host | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` (debug mode: `DEBUG`) |
| `API_KEY` | API key for external services | - |
| `ALLOWED_ORIGINS` | CORS allowed origins | `chrome-extension://` |
| `CACHE_ENABLED` | Enable response caching | `true` |
| `MAX_CONTENT_LENGTH` | Max request size in MB | `10` |

## Logging

Logs are stored in the `logs/` directory with the following naming convention:

- Server logs: `server_YYYY-MM-DD.log`
- Component logs: `component_YYYY-MM-DD.log`
- Test logs: `test_component_YYYY-MM-DD.log`
- Error logs: `error_YYYY-MM-DD.log`

View logs in real-time:

```bash
tail -f logs/server_$(date +%Y-%m-%d).log
```

## Common Issues

### Server Won't Start

- Ensure the port is not in use by another application
- Check if you have the correct permissions
- Verify all dependencies are installed

### Connection Errors

- Verify the server is running with `curl http://localhost:8080/api/status`
- Check firewall settings
- Ensure the extension has the correct server URL

### Processing Failures

- Verify yt-dlp and ffmpeg are installed
- Check if the video URL is accessible
- Ensure the API has sufficient permissions to access the content

## Troubleshooting Commands

Check server status:
```bash
curl http://localhost:8080/api/status
```

View running processes:
```bash
ps aux | grep python
```

Check for port usage:
```bash
lsof -i :8080
```

Test video processing:
```bash
python backend/test_olympus_video.py --test process --verbose
``` 