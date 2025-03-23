# Secure Video Summarizer Usage Guide

This guide covers how to use the Secure Video Summarizer application, including different running modes, basic operations, and common workflows.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Running Modes](#running-modes)
  - [Debug Mode](#debug-mode)
  - [Production Mode](#production-mode)
  - [Command-Line Mode](#command-line-mode)
- [Working with Videos](#working-with-videos)
- [Managing Summaries](#managing-summaries)
- [Configuration Options](#configuration-options)
- [Tips and Best Practices](#tips-and-best-practices)

## Basic Usage

1. **Start the backend server** (see [Running Modes](#running-modes) below)
2. **Open the browser extension**:
   - Click the Secure Video Summarizer icon in your browser toolbar
   - The extension will automatically detect videos on supported platforms

3. **Process a video**:
   - When viewing a supported video, click the "Summarize" button in the extension popup
   - Wait for the processing to complete
   - View the generated transcript and summary

4. **Export or save results**:
   - Use the "Export" button to save summaries in different formats
   - Summaries are also stored in history for later reference

## Running Modes

The Secure Video Summarizer can be run in multiple modes depending on your needs.

### Debug Mode

Debug mode provides verbose output, detailed error messages, and enables hot-reloading for development purposes.

**When to use**: During development, testing, or when troubleshooting issues.

**Starting the Backend in Debug Mode**:

```bash
cd backend
python main.py --debug
```

Or with environment variables:

```bash
cd backend
DEBUG=true python main.py
```

**Features of Debug Mode**:
- Detailed logging (INFO and DEBUG level messages)
- Automatic reloading when code changes
- Enhanced error reporting with tracebacks
- Disabled API rate limiting
- Test endpoints available
- Memory profiling enabled

### Production Mode

Production mode optimizes for performance, security, and stability with reduced logging verbosity.

**When to use**: For daily use, deployed environments, or when performance is critical.

**Starting the Backend in Production Mode**:

```bash
cd backend
python main.py --production
```

Or using the production server script:

```bash
cd backend
./scripts/start_production_server.sh
```

**Using a WSGI Server (Recommended for Production)**:

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:8080 "app:create_app()"
```

**Features of Production Mode**:
- Optimized for performance
- Minimized logging (WARNING and ERROR only)
- API rate limiting enabled
- Test endpoints disabled
- Security features fully enabled
- Redis caching for improved response times (if configured)

### Command-Line Mode

The command-line mode enables processing videos without running the full web server or using the browser extension.

**When to use**: For batch processing, automation, or when working without a GUI.

**Processing a Single Video**:

```bash
cd backend
python cli.py process-video --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output summary.txt
```

**Batch Processing Multiple Videos**:

```bash
cd backend
python cli.py batch-process --input urls.txt --output-dir ./summaries
```

**Available Command-Line Arguments**:
- `--url`: Video URL to process
- `--output`: File to save the summary
- `--transcript`: Also save the transcript
- `--format`: Output format (text, json, markdown)
- `--no-cache`: Disable caching
- `--verbose`: Enable verbose output

## Working with Videos

### Supported Platforms

The Secure Video Summarizer currently supports:
- YouTube videos
- Olympus Learning Platform (mygreatlearning.com)

### Processing a YouTube Video

1. Navigate to any YouTube video in your Chrome browser
2. Click the Secure Video Summarizer extension icon
3. Click "Summarize This Video"
4. Wait for processing to complete
5. View the transcript and summary in the extension popup

### Processing an Olympus Video

1. Navigate to a video on the Olympus Learning Platform
2. Click the Secure Video Summarizer extension icon
3. Click "Summarize This Video"
4. The extension will handle the authentication and processing
5. View the transcript and summary in the extension popup

## Managing Summaries

### Viewing History

1. Click the Secure Video Summarizer extension icon
2. Select the "History" tab
3. Browse previously processed videos

### Exporting Summaries

1. After processing a video or from the history view
2. Click the "Export" button
3. Choose your preferred format (Text, Markdown, JSON)
4. Select a location to save the file

### Customizing Summary Length

1. Click the Secure Video Summarizer extension icon
2. Go to "Settings"
3. Adjust the "Summary Length" slider
4. Process a new video to apply the setting

## Configuration Options

The application can be configured using environment variables or the settings UI:

| Option | Description | Where to Set |
|--------|-------------|--------------|
| Summary Length | Controls how detailed summaries are | Extension Settings |
| Language | Default language for UI and summaries | Extension Settings |
| Server URL | Backend server location | Extension Settings |
| Debug Mode | Enables detailed logging | Command Line / Environment |
| Port | Server port number | Command Line / Environment |
| Cache Settings | Controls result caching | Command Line / Environment |

## Tips and Best Practices

- **For best performance**: Use Production mode for regular use
- **When developing**: Use Debug mode for detailed logs
- **For batch processing**: Use Command-line mode with a text file of URLs
- **To conserve resources**: Close the server when not in use
- **For troubleshooting**: Check logs in the `logs/` directory
- **For optimal summaries**: Ensure the video has clear audio

For more technical details about running modes, refer to the [detailed documentation on environment variables and configuration](configuration.md). 