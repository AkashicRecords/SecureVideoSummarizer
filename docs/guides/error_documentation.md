# Modular Error Documentation Guide

This guide explains how to use and extend the modular error documentation system in the Secure Video Summarizer application.

## Table of Contents

- [Introduction](#introduction)
- [Using Existing Error Documentation](#using-existing-error-documentation)
- [Creating Custom Error Documentation Classes](#creating-custom-error-documentation-classes)
- [Extending Error Documentation](#extending-error-documentation)
- [Demo and Examples](#demo-and-examples)

## Introduction

The Secure Video Summarizer application uses a modular error documentation system to:

1. Link error messages to relevant documentation
2. Provide contextual help when errors occur
3. Make troubleshooting faster and more efficient
4. Standardize error handling across components

The system is built around the `ErrorDocumentationBase` class, which can be extended to create component-specific error documentation.

## Using Existing Error Documentation

The application comes with pre-defined error documentation for several components:

- `KnownTestIssues`: Documentation for common test failures
- Additional component-specific classes (as they are developed)

### Basic Error Logging

To use the existing error documentation in your code:

```python
from app.utils.error_documentation import error, info, success, warning, debug

# Log an error - this will automatically check for matching error patterns
error("Failed to download video")

# Other logging functions
info("Processing started")
success("Download completed")
warning("Using fallback method")
debug("Request params: {params}")
```

### Direct Error Checking

You can also check for error documentation directly:

```python
from app.utils.error_documentation import KnownTestIssues

error_message = "Failed to download video"
if KnownTestIssues.print_help_for_error(error_message):
    # Error was recognized and help was printed
    pass
else:
    # Error wasn't recognized in known issues
    print("This is an unknown error. Please report it.")
```

## Creating Custom Error Documentation Classes

To create documentation for a new component:

1. First, add error documentation to a markdown file (e.g., `docs/components/my_component.md`)
2. Create a new class that extends `ErrorDocumentationBase`

Example:

```python
from app.utils.error_documentation import ErrorDocumentationBase

class MyComponentErrors(ErrorDocumentationBase):
    """Error documentation for MyComponent."""
    
    # Define error patterns and their issue codes
    ERROR_PATTERNS = {
        "Connection timeout": "MYCOMP-01",
        "Invalid configuration": "MYCOMP-02",
        "Resource not found": "MYCOMP-03",
    }
    
    # Map issue codes to documentation links
    ISSUE_DOCS = {
        "MYCOMP-01": "docs/components/my_component.md#connection-timeouts",
        "MYCOMP-02": "docs/components/my_component.md#invalid-configurations",
        "MYCOMP-03": "docs/components/my_component.md#missing-resources",
    }
```

### Using Your Custom Error Documentation

```python
from my_component.errors import MyComponentErrors

def process_something():
    try:
        # ... your code ...
    except Exception as e:
        error_message = str(e)
        if not MyComponentErrors.print_help_for_error(error_message):
            # No documentation found, handle normally
            print(f"Error: {error_message}")
```

## Extending Error Documentation

### Adding New Error Patterns

To add new error patterns to your custom class:

#### Manual Method

1. Update your markdown documentation file with the new error
2. Add the new pattern to your error documentation class:

```python
class MyComponentErrors(ErrorDocumentationBase):
    ERROR_PATTERNS = {
        # ... existing patterns ...
        "New error pattern": "MYCOMP-04",
    }
    
    ISSUE_DOCS = {
        # ... existing docs ...
        "MYCOMP-04": "docs/components/my_component.md#new-error",
    }
```

#### Using the Utility Script

Use the `add_known_issue.py` script to add new errors:

```bash
python scripts/add_known_issue.py --code "MYCOMP-04" \
                               --title "New error description" \
                               --test "affected_function" \
                               --error "New error pattern" \
                               --cause "What causes this error" \
                               --solution "How to fix the issue" \
                               --class "MyComponentErrors"
```

### Custom Help Formatting

You can override the `print_help_for_error` method to customize how help is displayed:

```python
class MyComponentErrors(ErrorDocumentationBase):
    # ... ERROR_PATTERNS and ISSUE_DOCS ...
    
    @classmethod
    def print_help_for_error(cls, error_message: str) -> bool:
        """Custom formatting for help messages."""
        match = cls.find_matching_issue(error_message)
        if match:
            issue_code, doc_path = match
            print(f"\n--- MyComponent Error Help ---")
            print(f"Issue: {issue_code}")
            print(f"Documentation: {doc_path}")
            print(f"For internal users: Contact Team X for assistance")
            print(f"---------------------------\n")
            return True
        return False
```

## Demo and Examples

The application includes a demo script that showcases how the error documentation system works:

```bash
python scripts/demo_error_linking.py
```

This script simulates various errors and demonstrates how they link to documentation, including:
- Standard errors from known components
- Custom component errors
- Unrecognized errors

### Example Output

```
[INFO] Starting error documentation demo...

Simulating Olympus error:
[ERROR] Failed to download video

This appears to be a known issue: OLYMPUS-01
For more information and solutions, see:
docs/testing/known_issues.md#olympus-01---failed-to-download-video-error

Simulating YouTube error:
[ERROR] Invalid YouTube URL format

This appears to be a known issue: YT-01
For more information and solutions, see:
docs/testing/known_issues.md#yt-01---invalid-youtube-url-format

Simulating custom component error:
[ERROR] Connection timeout in custom component

[MYCOMP-01] This is a known issue in MyComponent.
Please check: docs/components/my_component.md#connection-timeouts

[INFO] Demo completed successfully.
```

## Best Practices

1. **Be specific with error patterns**: Choose unique patterns that won't match other errors
2. **Document first**: Always add documentation before adding error patterns
3. **Use consistent issue codes**: Follow the `COMPONENT-NN` format
4. **Group related errors**: Keep related errors in the same documentation class
5. **Test your patterns**: Verify that your patterns match the actual error messages
6. **Keep documentation updated**: Update documentation as the application evolves 