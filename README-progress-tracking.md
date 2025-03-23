# Video Summarization Job Progress Tracking

This document outlines the implementation of job progress tracking for video summarization tasks in the SVS application.

## Overview

The system now tracks the progress of video processing jobs, allowing users to monitor the status of their video summarization requests in real-time through the dashboard.

## Components

### Backend Implementation

1. **Job Management (backend/app/api/admin_routes.py)**
   - In-memory storage for active and completed jobs
   - Functions for registering, updating, and completing jobs
   - REST API endpoints for job management:
     - `/api/admin/jobs` - List all jobs
     - `/api/admin/jobs/<job_id>` - Get specific job details
     - `/api/admin/jobs/<job_id>/progress` - Update job progress

2. **Video Processing (backend/app/summarizer/routes.py)**
   - Job creation with unique IDs for each summarization request
   - Background thread processing with progress callback
   - Stage-based progress reporting (audio extraction, transcription, summarization)

3. **Progress Callback (backend/app/summarizer/processor.py)**
   - The `process_video` method accepts a progress callback function
   - Different stages report progress individually

### Frontend Implementation

1. **Dashboard UI (backend/app/static/js/dashboard.js)**
   - Jobs page displaying active and completed jobs
   - Real-time progress bars for active jobs
   - Auto-refresh with configurable intervals (3 seconds for jobs, 30 seconds for other pages)

## Testing

A test script is provided to demonstrate the progress tracking functionality:

```bash
# Run the test script with a video file
python backend/test_summarize_with_progress.py --video path/to/video.mp4
```

The script will:
1. Check if the API is running
2. Create a summarization job
3. Poll for progress updates
4. Display the final summary when complete

## Progress Stages

The video processing is divided into stages, each with weighted progress contributions:

1. **Audio Extraction (20%)**: Converting video to audio
2. **Transcription (50%)**: Converting audio to text
3. **Summarization (30%)**: Generating the summary from text

## Implementation Notes

- Progress updates are pushed to the dashboard in real-time
- Failed jobs are properly marked and tracked
- Job history is maintained for completed jobs (up to 20 most recent jobs)
- Progress is normalized to a 0-100% scale for consistency 