# Test Logging Guide

This guide explains how our test logging system works, including the automatic linking of errors to documentation.

## Table of Contents

- [Basic Logging Functions](#basic-logging-functions)
- [Error-to-Documentation Linking](#error-to-documentation-linking)
- [Creating Custom Error Documentation Classes](#creating-custom-error-documentation-classes)
- [How to Add New Error Patterns](#how-to-add-new-error-patterns)
- [Log Configuration](#log-configuration)
- [Best Practices](#best-practices)

## Basic Logging Functions

The test logging system provides several functions for different logging levels:

```python
from app.utils.error_documentation import info, success, warning, error, debug

# Informational messages
info("Processing video at URL: https://example.com/video")

# Success messages
success("Successfully generated transcript with 1200 characters")

# Warning messages
warning("Using fallback processing method due to API limitations")

# Error messages - these automatically link to documentation when possible
error("Failed to download video")

# Debug messages - only shown in verbose mode
debug("API response details: {response_data}")
```

## Error-to-Documentation Linking

When an error is logged using the `error()` function, the system automatically:

1. Checks if the error message matches any known error patterns
2. If a match is found, it displays:
   - The issue code (e.g., `OLYMPUS-01`)
   - The path to the documentation file
   - A quick reference excerpt from the documentation

Example output:

```
[ERROR] Failed to download video

This appears to be a known issue: OLYMPUS-01
For more information and solutions, see:
/Users/username/SecureVideoSummarizer/docs/testing/known_issues.md#olympus-01---failed-to-download-video-error

Quick reference:
#### `OLYMPUS-01` - "Failed to download video" Error

**Test:** `test_olympus_process_url`

**Error Message:**
ERROR: Failed to download video.

**Cause:** 
The Olympus platform serves videos in chunks that cannot be easily downloaded for testing.

**Solution:**
Run the test with the mock download flag to avoid actual video downloads:
```bash
python test_olympus_video.py --test process --verbose --mock-download
```
```

This feature helps developers quickly identify and fix common issues without having to search through documentation.

## Creating Custom Error Documentation Classes

The error documentation system uses a modular approach with a base class (`ErrorDocumentationBase`) that can be extended to create custom error documentation for specific components.

### 1. Define a Custom Error Documentation Class

```python
from app.utils.error_documentation import ErrorDocumentationBase

class MyComponentErrors(ErrorDocumentationBase):
    """Custom error documentation for my component."""
    
    # Define error patterns and their issue codes
    ERROR_PATTERNS = {
        "Connection failed": "MYCOMP-01",
        "Invalid input format": "MYCOMP-02",
    }
    
    # Map issue codes to documentation links
    ISSUE_DOCS = {
        "MYCOMP-01": "docs/my_component/troubleshooting.md#connection-issues",
        "MYCOMP-02": "docs/my_component/troubleshooting.md#input-validation",
    }
    
    # Optionally, override the print_help_for_error method for custom formatting
    @classmethod
    def print_help_for_error(cls, error_message: str) -> bool:
        """Custom formatting for component-specific errors."""
        match = cls.find_matching_issue(error_message)
        if match:
            issue_code, doc_path = match
            print(f"\n[{issue_code}] This is a known issue in MyComponent.")
            print(f"Please check: {doc_path}\n")
            return True
        return False
```

### 2. Use the Custom Error Documentation

```python
from my_component.errors import MyComponentErrors

# Check if an error message matches a known issue
error_message = "Connection failed: timeout after 30 seconds"
MyComponentErrors.print_help_for_error(error_message)
```

### 3. Integrate with Logging

You can also integrate your custom error documentation with your component's logging:

```python
from app.utils.error_documentation import ErrorColors

def my_component_error(message: str):
    """Log an error message with custom error documentation."""
    print(f"{ErrorColors.RED}[ERROR] {message}{ErrorColors.RESET}")
    MyComponentErrors.print_help_for_error(message)
```

## How to Add New Error Patterns

To add a new error pattern to the automatic linking system:

1. First, add the error documentation to `docs/testing/known_issues.md` following the established format

2. Then, update the appropriate error documentation class in `backend/app/utils/error_documentation.py`:

```python
# Add a new error pattern to an existing class
class KnownTestIssues(ErrorDocumentationBase):
    ERROR_PATTERNS = {
        # ... existing patterns ...
        "Your new error message pattern": "NEW-CODE-01",
    }
    
    ISSUE_DOCS = {
        # ... existing docs ...
        "NEW-CODE-01": "docs/testing/known_issues.md#new-code-01---brief-description",
    }
```

The error pattern should be a distinctive substring that appears in error messages. The documentation link should point to the specific section in the known issues document.

## Adding New Errors with the Utility Script

For convenience, you can use the `add_known_issue.py` script to add new error patterns:

```bash
python scripts/add_known_issue.py --code "NEW-CODE-01" \
                               --title "Brief error description" \
                               --test "test_function_name" \
                               --error "Error message text" \
                               --cause "What causes this error" \
                               --solution "How to fix the issue" \
                               --class "MyComponentErrors"  # Optional, defaults to KnownTestIssues
```

This will automatically:
1. Add the entry to `known_issues.md`
2. Update the specified error documentation class in `error_documentation.py`

## Log Configuration

The logging system writes logs to both the console and to files in the `logs/` directory.

### Log Files

Test logs are stored in the `logs/` directory with the following naming convention:
- `test_olympus_YYYY-MM-DD.log`
- `test_youtube_YYYY-MM-DD.log`
- `test_api_YYYY-MM-DD.log`

### Verbosity Levels

To enable verbose logging (including debug messages), run tests with the `--verbose` flag:

```bash
python test_olympus_video.py --test all --verbose
```

## Best Practices

1. **Be Specific**: Use the appropriate logging function for the message type
2. **Include Context**: Always include relevant details in error messages
3. **Error Patterns**: When adding new error patterns, choose unique substrings
4. **Documentation First**: Always add documentation before adding error patterns
5. **Keep it DRY**: If you find yourself logging the same errors across multiple tests, consider standardizing them
6. **Component Separation**: Create separate error documentation classes for different components
7. **Inheritance**: Use inheritance to share common patterns across related components

## Common Logging Patterns

Here are some common patterns for effective test logging:

```python
# Beginning of test
info(f"Starting test: {test_name}")

# API requests
debug(f"Sending request to {url} with params: {params}")

# Assertions
success(f"Response contains expected data: {key}={value}")

# Failures with context
error(f"API returned {status_code} instead of 200: {response_text}")
```

By following these guidelines, our test logs will be more consistent, informative, and helpful for troubleshooting. 