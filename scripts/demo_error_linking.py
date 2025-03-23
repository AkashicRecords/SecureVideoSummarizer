#!/usr/bin/env python3
"""
Demonstration script for error linking system.
This script shows how errors are automatically linked to documentation.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backend'))

from app.utils.error_documentation import info, success, warning, error, debug, KnownTestIssues, ErrorDocumentationBase

# Example of creating a custom error documentation class for a specific component
class CustomComponentErrors(ErrorDocumentationBase):
    """Example custom error documentation for a hypothetical component."""
    
    ERROR_PATTERNS = {
        "Database connection failed": "DB-01",
        "Invalid configuration": "CONFIG-01",
    }
    
    ISSUE_DOCS = {
        "DB-01": "docs/database/troubleshooting.md#connection-issues",
        "CONFIG-01": "docs/configuration/troubleshooting.md#invalid-settings",
    }
    
    @classmethod
    def print_help_for_error(cls, error_message: str) -> bool:
        """Override to add custom formatting for this component's errors."""
        match = cls.find_matching_issue(error_message)
        if match:
            issue_code, doc_path = match
            print(f"\n[{issue_code}] This is a known database or configuration issue.")
            print(f"Please check the documentation at: {doc_path}\n")
            return True
        return False

def simulate_olympus_error():
    """Simulate an Olympus download error."""
    info("Starting Olympus video download test...")
    info("Connecting to Olympus platform...")
    warning("Using development API credentials")
    error("Failed to download video")
    
def simulate_youtube_error():
    """Simulate a YouTube API error."""
    info("Starting YouTube batch processing test...")
    info("Processing 10 videos...")
    warning("API rate limit approaching")
    error("Too many requests. YouTube API quota exceeded")
    
def simulate_api_error():
    """Simulate an API connection error."""
    info("Testing API connection...")
    error("Connection refused")
    
def simulate_unknown_error():
    """Simulate an unknown error (without documentation)."""
    info("Testing unknown feature...")
    error("Unknown feature failed with XYZ exception")

def simulate_custom_component_error():
    """Simulate a custom component error."""
    info("Testing database connection...")
    message = "Database connection failed: timeout after 30s"
    print(f"\nError message: {message}")
    CustomComponentErrors.print_help_for_error(message)
    
def main():
    """Run the demo script."""
    print("Error Linking Demonstration")
    print("==========================")
    print("This script demonstrates how errors are automatically linked to documentation.")
    print("When an error matches a known pattern, the system will provide:")
    print("  1. An issue code (e.g., OLYMPUS-01)")
    print("  2. A link to the documentation")
    print("  3. A quick reference excerpt from the documentation")
    print("\nDemonstrating different error types...\n")
    
    print("\n1. Olympus Error Example:")
    simulate_olympus_error()
    
    print("\n2. YouTube Error Example:")
    simulate_youtube_error()
    
    print("\n3. API Error Example:")
    simulate_api_error()
    
    print("\n4. Unknown Error Example (no documentation link):")
    simulate_unknown_error()
    
    print("\n5. Custom Component Error Example (custom formatter):")
    simulate_custom_component_error()
    
    print("\nTo add documentation for unknown errors, use the add_known_issue.py script:")
    print("python scripts/add_known_issue.py --code \"ERROR-01\" --title \"...\" --test \"...\" ...")
    
    print("\nTo create a custom error documentation class for your component:")
    print("""
class MyComponentErrors(ErrorDocumentationBase):
    ERROR_PATTERNS = {
        "Error pattern": "MYCOMP-01",
    }
    
    ISSUE_DOCS = {
        "MYCOMP-01": "docs/my_component/troubleshooting.md#section",
    }
""")

if __name__ == "__main__":
    main() 