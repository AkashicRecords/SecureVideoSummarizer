# Secure Video Summarizer Quick Start Guide

This guide provides essential commands to quickly get started with the Secure Video Summarizer in various modes.

## Installation

```bash
# Clone repository
git clone https://github.com/AkashicRecords/SecureVideoSummarizer.git
cd SecureVideoSummarizer

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set up logs folder
./scripts/setup_logs_folder.sh

# Install the browser extension (in developer mode)
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the "extension" folder from this repository
```

## Starting the Application

### Debug Mode (Development)

```bash
# Start the backend server in debug mode
cd backend
python main.py --debug
```

Debug mode features:
- Detailed logging
- Auto-reload on code changes
- Enhanced error reporting
- Test endpoints available

### Production Mode

```bash
# Start the backend server in production mode
cd backend
python main.py --production

# Alternative (recommended for actual production):
cd backend
gunicorn -w 4 -b 0.0.0.0:8080 "app:create_app()"
```

Production mode features:
- Optimized performance
- Reduced logging
- Enhanced security
- API rate limiting

### Command-Line Mode

Process videos directly from the command line:

```bash
# Process a single video
cd backend
python cli.py process-video --url "https://www.youtube.com/watch?v=example" --output summary.txt

# Batch process multiple videos
cd backend
python cli.py batch-process --input urls.txt --output-dir ./summaries
```

## Testing

```bash
# Run all tests
cd backend
python -m pytest

# Test specific components
cd backend
python test_olympus_video.py --test all --verbose
python test_youtube_video.py --test all --verbose

# Mock testing (without actual video download)
cd backend
python test_olympus_video.py --test process --mock-download
```

## Checking Status

```bash
# Check if the server is running
curl http://localhost:8080/api/status

# View logs in real-time
tail -f logs/server_$(date +%Y-%m-%d).log

# Check for processes using the port
lsof -i :8080
```

## Common Commands

```bash
# Restart the server
cd backend
pkill -f "python main.py" && python main.py --debug

# Clear logs
rm logs/*.log

# Update dependencies
pip install -r backend/requirements.txt
```

## Where to Find Help

- Complete documentation: See [Running Modes](running_modes.md)
- Troubleshooting: See [Common Issues](running_modes.md#common-issues)
- Issue tracker: [GitHub Issues](https://github.com/AkashicRecords/SecureVideoSummarizer/issues)

For detailed information about each running mode, refer to the [Running Modes documentation](running_modes.md). 