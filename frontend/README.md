# Secure Video Summarizer - Frontend

<div align="center">
  <img src="../Assets/SVS.jpg" alt="Secure Video Summarizer Logo" width="200"/>
</div>

## Overview

This is the frontend application for the Secure Video Summarizer. It provides a user-friendly interface for video uploading, processing, and summarization.

## Features

- **Secure Authentication**: Integration with Google OAuth
- **Video Upload**: Easy drag-and-drop interface for video uploading
- **Summary Customization**: Control summary length, format, and focus
- **Real-time Progress Tracking**: Monitor transcription and summarization progress
- **Responsive Design**: Works on desktop and mobile devices

## Setup

### Prerequisites

- Node.js (v14 or later)
- npm or yarn
- Backend API running (See [Backend README](../backend/README.md))

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Create a `.env` file with the following content:

```
REACT_APP_API_URL=http://localhost:5000
```

3. Start the development server:

```bash
npm start
# or
yarn start
```

## Development

### Folder Structure

- `src/components`: React components
- `src/pages`: Page layouts
- `src/styles`: CSS and style definitions
- `src/utils`: Utility functions and API calls
- `public`: Static assets

### Technologies Used

- React
- React Router
- Axios for API calls
- React Bootstrap for UI components

## Build for Production

To create a production build:

```bash
npm run build
# or
yarn build
```

## Integration with the Backend

The frontend communicates with the backend API at the URL specified in the `.env` file. Make sure the backend server is running and accessible at that URL. 