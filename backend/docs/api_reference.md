# API Reference

This document provides comprehensive documentation for all APIs in the SecureVideoSummarizer application, including those for browser extension integration.

## Table of Contents

- [General API Information](#general-api-information)
- [Authentication](#authentication)
- [Extension API Endpoints](#extension-api-endpoints)
- [Video Processing Endpoints](#video-processing-endpoints)
- [Summarization Endpoints](#summarization-endpoints)
- [Olympus Learning Platform Integration](#olympus-learning-platform-integration)
- [Error Handling](#error-handling)

## General API Information

### Base URL

All API endpoints are relative to the base URL of your instance:

- **Development**: `http://localhost:5000`
- **Production**: Your deployed application URL

### Request Format

- All POST requests should use JSON in the request body, except for file uploads which use `multipart/form-data`
- All requests should include appropriate `Content-Type` headers

### Response Format

All API responses are returned in JSON format with the following general structure:

```json
{
  "success": true|false,
  "data": {}, // Response data if successful
  "error": "", // Error message if unsuccessful
  "details": {} // Additional error details if applicable
}
```

## Authentication

### Overview

The API uses Google OAuth for authentication. Most API endpoints require authentication.

### Headers

For authenticated requests, include the session cookie that is set during the Google OAuth flow:

```
Cookie: session=<session_token>
```

### Endpoints

#### GET /auth/login

Initiates the Google OAuth login flow.

#### GET /auth/callback

Handles the callback from Google OAuth.

#### POST /auth/logout

Logs out the current user.

#### GET /auth/user

Returns information about the currently authenticated user.

## Extension API Endpoints

### GET /api/extension/status

Check if the browser extension is properly connected to the backend.

**Response:**

```json
{
  "status": "connected",
  "version": "1.0.0",
  "allowed_origins": ["http://localhost:3000"]
}
```

### POST /api/transcribe

Transcribe and summarize audio received from the frontend or browser extension.

**Request Body (multipart/form-data):**

```
audio: [audio file in webm format]
```

**Response:**

```json
{
  "success": true,
  "transcription": "The transcribed text content...",
  "summary": "A summary of the transcribed content...",
  "processing_time": "3.25s"
}
```

## Video Processing Endpoints

### POST /video/upload

Upload a video file for processing.

**Request Body (multipart/form-data):**

```
video: [video file]
```

**Response:**

```json
{
  "success": true,
  "video_id": "unique-video-id",
  "filename": "original-filename.mp4",
  "size": 1024000
}
```

### GET /video/{video_id}

Retrieve a previously uploaded video.

**Response:**

The video file is returned directly.

### DELETE /video/{video_id}

Delete a previously uploaded video.

**Response:**

```json
{
  "success": true,
  "video_id": "unique-video-id"
}
```

## Summarization Endpoints

### POST /api/summarize/video/{video_id}

Generate a summary for a previously uploaded video.

**Request Body:**

```json
{
  "options": {
    "length": "medium",  // short, medium, long
    "format": "bullets", // paragraph, bullets, numbered, key_points
    "focus": ["key_points"], // key_points, detailed
    "min_length": 50,
    "max_length": 150
  }
}
```

**Response:**

```json
{
  "success": true,
  "video_id": "unique-video-id",
  "transcript": "The complete transcript...",
  "summary": "A summary of the video content...",
  "processing_time": "10.50s"
}
```

## Olympus Learning Platform Integration

The following endpoints are specifically designed for integration with the Olympus Learning Platform video player.

### POST /api/olympus/capture [PLANNED]

Process a video capture from the Olympus Learning Platform via the browser extension.

**Request Body:**

```json
{
  "transcript": "The transcribed text from the video...",
  "video_metadata": {
    "title": "Video Title",
    "course": "Course Name",
    "lecture": "Lecture Name",
    "url": "https://olympus.mygreatlearning.com/courses/..."
  },
  "options": {
    "length": "medium",
    "format": "bullets",
    "focus": ["key_points"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "summary": "A summary of the video content...",
  "processing_time": "2.15s",
  "metadata": {
    "title": "Video Title",
    "course": "Course Name"
  }
}
```

### GET /api/olympus/history [PLANNED]

Retrieve a history of Olympus videos that have been processed by the extension.

**Response:**

```json
{
  "success": true,
  "history": [
    {
      "id": "unique-id",
      "title": "Video Title",
      "course": "Course Name",
      "url": "https://olympus.mygreatlearning.com/courses/...",
      "processed_at": "2025-03-16T08:30:00Z",
      "summary_available": true
    },
    // Additional items...
  ]
}
```

### GET /api/olympus/summary/{id} [PLANNED]

Retrieve a specific summary for a previously processed Olympus video.

**Response:**

```json
{
  "success": true,
  "id": "unique-id",
  "title": "Video Title",
  "course": "Course Name",
  "url": "https://olympus.mygreatlearning.com/courses/...",
  "summary": "A summary of the video content...",
  "processed_at": "2025-03-16T08:30:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was malformed or missing required parameters
- `401 Unauthorized`: Authentication is required
- `403 Forbidden`: The authenticated user does not have permission to access the resource
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An unexpected error occurred on the server

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "details": {} // Optional additional details
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- Default: 200 requests per day, 50 per hour
- Authentication endpoints: 10 requests per minute

When a rate limit is exceeded, the API returns a `429 Too Many Requests` status code with an appropriate error message. 