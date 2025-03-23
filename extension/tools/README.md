# SVS Extension Troubleshooting Tools

This directory contains tools to help troubleshoot the Secure Video Summarizer extension.

## Content Script Inspector

The `inspect_content_script.js` utility helps diagnose issues with the extension's content script, particularly when the extension fails to detect videos or reports communication errors.

### How to Use

1. Open the page where you're experiencing issues with the SVS extension
2. Open Chrome DevTools (right-click anywhere on the page and select "Inspect" or press F12)
3. Navigate to the "Console" tab in DevTools
4. Copy the entire content of `inspect_content_script.js`
5. Paste it into the console and press Enter

### What It Does

The tool will perform several diagnostics:

1. Check if the content script is loaded and responding
2. Request video data from the content script
3. Examine the page directly for video elements
4. Provide troubleshooting recommendations based on findings
5. Offer commands to manually inject the content script

### Interpreting Results

- **Green checkmarks (✅)** indicate successful checks
- **Red X marks (❌)** indicate failed checks or errors
- **Yellow warnings (⚠)** indicate potential issues

### Common Issues and Solutions

#### "Content script not detected"

This means the extension's content script isn't running on the current page. Try:

- Clicking the "Refresh Content Script" button in the extension popup
- Reloading the page
- Checking if you're on a supported domain (YouTube, Olympus, etc.)

#### "No video data found"

The content script is running but can't find a supported video. Try:

- Ensuring the video is actually playing or loaded
- Waiting a few seconds for the video to fully initialize
- Checking if the video is in an iframe that might be blocked

#### "Failed to get video info: Could not establish connection"

This means the content script can't communicate with the extension. Try:

- Reloading the extension by going to chrome://extensions/ and clicking the refresh icon
- Restarting Chrome
- Reinstalling the extension

### Manual Content Script Injection

If all else fails, you can try to manually inject the content script using the provided command:

```javascript
// First, get the current tab ID
chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
  const tabId = tabs[0].id;
  // Inject the content script
  chrome.scripting.executeScript({
    target: {tabId: tabId},
    files: ['content.js']
  });
});
```

## Other Troubleshooting Tips

### Check Extension Permissions

Make sure the extension has the required permissions for the current site:

1. Go to chrome://extensions/
2. Find "Secure Video Summarizer" and click "Details"
3. Ensure "Site access" is set appropriately (usually "On all sites" or includes the domain you're on)

### Check for Console Errors

Open Chrome DevTools and check the Console tab for any error messages from the extension. Look for messages that start with:

- `[SVS Extension]`
- `Error in content script`
- `Failed to execute message on runtime`

### Check API Connection

Verify that the backend API server is running:

1. From the extension popup, check if it shows "Backend connected"
2. Try accessing http://localhost:8081/api/health directly in a browser tab
3. Use the backend's troubleshoot.sh script to verify the server status 