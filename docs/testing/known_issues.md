# Known Test Issues

This document catalogs known issues that may be encountered while running tests for the Secure Video Summarizer application. Each issue is documented with its error message, cause, and solution.

## About Issue Codes

Issue codes follow the format `COMPONENT-NN` where:
- `COMPONENT` is an identifier for the application component (e.g., OLYMPUS, YT for YouTube, API for the API service)
- `NN` is a sequential number within that component

Components with known issues include:
- `OLYMPUS` - Issues with the Olympus video processing component
- `YT` - Issues with YouTube video handling
- `API` - Issues with API interactions
- `MYCOMP` - Example custom component (documentation only)

You can create custom error documentation classes for your own components by extending the `ErrorDocumentationBase` class. See [Creating Custom Error Documentation Classes](test_logging.md#creating-custom-error-documentation-classes) for details.

## Table of Contents

- [Backend Tests](#backend-tests)
  - [Olympus Integration Tests](#olympus-integration-tests)
  - [YouTube Integration Tests](#youtube-integration-tests)
  - [API Tests](#api-tests)
- [Extension Tests](#extension-tests)
- [End-to-End Tests](#end-to-end-tests)

## Backend Tests

### Olympus Integration Tests

#### `OLYMPUS-01` - "Failed to download video" Error

**Test:** `test_olympus_process_url`

**Error Message:**
```
ERROR: Failed to download video.
```

**Cause:** 
The Olympus platform serves videos in chunks that cannot be easily downloaded for testing.

**Solution:**
Run the test with the mock download flag to avoid actual video downloads:
```bash
python test_olympus_video.py --test process --verbose --mock-download
```

**Documentation:** [Olympus Integration Guide](../reference/integrations/olympus.md#testing)

---

#### `OLYMPUS-02` - TypeError: 'bool' object is not callable

**Test:** `test_olympus_process_url`

**Error Message:**
```
TypeError: 'bool' object is not callable
```

**Cause:**
The test is trying to call `success()` as a function when it should be using `info()`.

**Solution:**
Update the test code to replace:
```python
success(f"Successfully generated transcript with {transcript_length} characters")
```
with:
```python
info(f"Successfully generated transcript with {transcript_length} characters")
```

**Documentation:** [Test Logging Guide](./test_logging.md)

---

### YouTube Integration Tests

#### `YOUTUBE-01` - "Video Unavailable" Error

**Test:** `test_youtube_process_url`

**Error Message:**
```
ERROR: Video is unavailable or has been removed
```

**Cause:**
The test video URL is no longer valid or the video has been removed.

**Solution:**
Update the test video URL in `test_youtube_video.py` to a known working video:
```python
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # "Me at the zoo" - first YouTube video
```

**Documentation:** [YouTube Integration Guide](../reference/integrations/youtube.md#testing)

---

#### `YOUTUBE-02` - Rate Limiting Error

**Test:** `test_youtube_batch_process`

**Error Message:**
```
ERROR: Too many requests. YouTube API quota exceeded
```

**Cause:**
YouTube API has rate limits that can be exceeded during batch testing.

**Solution:**
1. Use the mock API response for batch testing:
   ```bash
   python test_youtube_video.py --test batch --mock-api
   ```
2. Implement a delay between requests:
   ```python
   import time
   time.sleep(2)  # Add 2-second delay between API calls
   ```

**Documentation:** [YouTube API Rate Limits](../reference/integrations/youtube.md#rate-limits)

---

### API Tests

#### `API-01` - Connection Refused Error

**Test:** Any API test

**Error Message:**
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Cause:**
The backend server is not running or is running on a different port.

**Solution:**
1. Start the backend server:
   ```bash
   cd backend
   python main.py --debug
   ```
2. Ensure the test is using the correct port:
   ```python
   BASE_URL = "http://localhost:8080"  # Update if your server uses a different port
   ```

**Documentation:** [Usage Guide](../guides/usage_guide.md#running-modes)

---

#### `API-02` - Missing API Key

**Test:** Tests requiring external API access

**Error Message:**
```
ERROR: API key not found or invalid
```

**Cause:**
Required API keys are missing from environment variables.

**Solution:**
1. Create a `.env` file in the backend directory:
   ```
   API_KEY=your_api_key_here
   ```
2. Run the test with the environment file:
   ```bash
   python -m dotenv run python test_api.py
   ```

**Documentation:** [Configuration Guide](../guides/configuration.md#api-keys)

---

## Extension Tests

#### `EXT-01` - Extension Not Found

**Test:** Extension integration tests

**Error Message:**
```
ERROR: Extension not found or not properly installed
```

**Cause:**
The Chrome extension is not properly installed in development mode.

**Solution:**
1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the "extension" folder
4. Ensure the extension ID matches what's used in tests

**Documentation:** [Extension Development Guide](../guides/developer/extension.md)

---

## End-to-End Tests

#### `E2E-01` - Test Timeout

**Test:** End-to-end integration tests

**Error Message:**
```
ERROR: Test timed out after 30 seconds
```

**Cause:**
The test is taking too long to complete, often due to slow video processing.

**Solution:**
1. Increase the timeout value:
   ```python
   # Increase timeout to 60 seconds
   @pytest.mark.timeout(60)
   def test_end_to_end():
       # Test code here
   ```
2. Use smaller test videos for faster processing
3. Use mock responses for performance-critical tests

**Documentation:** [End-to-End Testing Guide](./e2e_testing.md)

---

#### `E2E-02` - Browser Driver Not Found

**Test:** End-to-end tests using Selenium

**Error Message:**
```
ERROR: WebDriverException: Chrome executable needs to be in PATH
```

**Cause:**
Chrome WebDriver is not installed or not in the system PATH.

**Solution:**
1. Install ChromeDriver:
   ```bash
   # On macOS with Homebrew
   brew install --cask chromedriver
   
   # On Ubuntu
   apt install chromium-chromedriver
   ```
2. Add to PATH:
   ```bash
   export PATH=$PATH:/path/to/chromedriver
   ```

**Documentation:** [Browser Testing Setup](./browser_testing.md)

---

## Adding New Known Issues

When you encounter a recurring test issue, please add it to this document following the format:

```markdown
#### `CATEGORY-XX` - Brief Error Description

**Test:** `test_name`

**Error Message:**
```
Exact error message
```

**Cause:**
Explanation of what causes this error

**Solution:**
Steps to resolve the issue

**Documentation:** [Link to relevant documentation](path/to/doc.md)
```

Replace `CATEGORY-XX` with the appropriate category code (e.g., `OLYMPUS-03`, `API-04`) and an increasing number. 