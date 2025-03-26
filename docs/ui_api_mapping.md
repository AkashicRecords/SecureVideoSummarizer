# UI Elements to API Routes Mapping

## Main Container Elements

### Header Section
- **Element**: `#popup-container`
- **Purpose**: Main container for the extension popup
- **API Interaction**: None (UI only)

### Platform Detection
- **Element**: `#platform-specific-section`
- **Purpose**: Shows platform-specific UI elements
- **API Routes**:
  - `/api/status` - Initial platform detection
  - `/api/{platform}/status` - Platform-specific status check
- **States**:
  - Hidden: No platform detected
  - Visible: Platform detected

## Status Messages

### Loading State
- **Element**: `#loading`
- **Purpose**: Shows processing status
- **API Routes**:
  - All API calls show this state
- **States**:
  - Hidden: No active processing
  - Visible: Processing in progress

### No Video State
- **Element**: `#no-video`
- **Purpose**: Indicates no video detected
- **API Routes**: None (Content script detection)
- **States**:
  - Hidden: Video detected
  - Visible: No video found

### Error State
- **Element**: `#extension-error`
- **Purpose**: Shows connection/processing errors
- **API Routes**:
  - `/api/status` - Connection errors
  - All API calls - Processing errors
- **Actions**:
  - `#retry-connection` - Retries backend connection
  - `#refresh-content-script` - Reloads content script

### Video Detection
- **Element**: `#video-detected`
- **Purpose**: Shows detected video information
- **API Routes**: None (Content script detection)
- **Sub-elements**:
  - `#video-title`: Video title
  - `#video-duration`: Video duration
  - `#video-warning`: Warning messages

## Options Section

### Summary Length
- **Element**: `#summary-length`
- **Purpose**: Controls summary length
- **API Routes**:
  - `/api/{platform}/capture` - Length parameter
- **Options**:
  - Short (30-100 words)
  - Medium (50-150 words)
  - Long (100-250 words)

### Format Selection
- **Element**: `#format`
- **Purpose**: Controls summary format
- **API Routes**:
  - `/api/{platform}/capture` - Format parameter
- **Options**:
  - Paragraph
  - Bullet Points
  - Numbered List
  - Key Points

### Focus Options
- **Elements**:
  - `#focus-key-points`
  - `#focus-details`
- **Purpose**: Controls summary focus
- **API Routes**:
  - `/api/{platform}/capture` - Focus parameters

## Platform-Specific Elements

### YouTube Options
- **Element**: `#youtube-options`
- **Purpose**: YouTube-specific controls
- **API Routes**:
  - `/api/youtube/status` - Status check
  - `/api/youtube/capture` - Video capture
- **Actions**:
  - `#youtube-summarize-btn` - Initiates YouTube capture

### Olympus Options
- **Element**: `#olympus-options`
- **Purpose**: Olympus-specific controls
- **API Routes**:
  - `/api/olympus/status` - Status check
  - `/api/olympus/capture` - Video capture
- **Sub-elements**:
  - `#olympus-api-status` - Shows API status

## Summary Display

### Summary Container
- **Element**: `#summary-container`
- **Purpose**: Displays generated summary
- **API Routes**:
  - All capture endpoints return summary data
- **States**:
  - Hidden: No summary available
  - Visible: Summary ready

### Summary Content
- **Element**: `#summary-content`
- **Purpose**: Contains summary text
- **API Routes**: None (displays API response)

## Error Handling

### Network Errors
- **Element**: `#extension-error`
- **Purpose**: Shows network-related errors
- **API Routes**: All routes
- **Error Types**:
  - NETWORK_ERROR
  - TIMEOUT_ERROR
  - API_ERROR
  - AUTH_ERROR

### Platform-Specific Errors
- **Element**: `#video-warning`
- **Purpose**: Shows platform-specific issues
- **API Routes**: Platform-specific endpoints
- **Error Types**:
  - Video not found
  - Unsupported format
  - Processing errors

## State Management

### Loading States
- **Elements**: Various loading indicators
- **Purpose**: Show processing status
- **API Routes**: All routes
- **States**:
  - Initializing
  - Processing
  - Complete
  - Error

### Platform States
- **Elements**: Platform-specific sections
- **Purpose**: Show platform detection
- **API Routes**: Status endpoints
- **States**:
  - Detected
  - Not detected
  - Error 