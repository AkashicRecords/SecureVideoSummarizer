"""
Error Documentation Module

This module provides a reusable base class for linking errors to documentation.
Other components can inherit from this class to add error-documentation linking capabilities.
"""

import os
import re
import sys
from typing import Dict, List, Optional, Tuple

class ErrorColors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class ErrorDocumentationBase:
    """
    Base class for linking errors to documentation.
    This class can be inherited by other components to add error-documentation linking.
    
    Example usage:
    ```python
    class MyComponentErrors(ErrorDocumentationBase):
        ERROR_PATTERNS = {
            "Connection failed": "MYCOMP-01",
            "Invalid input": "MYCOMP-02",
        }
        
        ISSUE_DOCS = {
            "MYCOMP-01": "docs/my_component/troubleshooting.md#connection-failures",
            "MYCOMP-02": "docs/my_component/troubleshooting.md#input-validation",
        }
    ```
    """
    
    # Error patterns to be overridden by subclasses
    ERROR_PATTERNS: Dict[str, str] = {}
    
    # Issue documentation links to be overridden by subclasses
    ISSUE_DOCS: Dict[str, str] = {}
    
    @classmethod
    def get_project_root(cls) -> str:
        """Get the project root directory"""
        # Start from the current file and navigate up to find the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # By default, assume project root is two directories up from utils
        return os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    
    @classmethod
    def find_matching_issue(cls, error_message: str) -> Optional[Tuple[str, str]]:
        """
        Find a known issue that matches the error message
        
        Args:
            error_message: The error message to check
            
        Returns:
            A tuple of (issue_code, doc_url) if found, None otherwise
        """
        for pattern, issue_code in cls.ERROR_PATTERNS.items():
            if pattern.lower() in error_message.lower():
                doc_path = cls.ISSUE_DOCS.get(issue_code)
                if doc_path:
                    full_path = os.path.join(cls.get_project_root(), doc_path)
                    return (issue_code, full_path)
        return None
    
    @classmethod
    def format_help_for_error(cls, error_message: str) -> Optional[str]:
        """
        Format help information for a known error
        
        Args:
            error_message: The error message to check
            
        Returns:
            Formatted help text if a matching issue was found, None otherwise
        """
        match = cls.find_matching_issue(error_message)
        if not match:
            return None
            
        issue_code, doc_path = match
        help_text = f"\nThis appears to be a known issue: {issue_code}\n"
        help_text += f"For more information and solutions, see:\n"
        help_text += f"{doc_path}\n"
        
        # Check if the documentation file exists
        if os.path.exists(doc_path):
            # Try to extract the relevant section from the docs
            try:
                with open(doc_path, 'r') as f:
                    content = f.read()
                    # Look for the section header with the issue code
                    section_pattern = f"#### `{issue_code}`.*?---"
                    section_match = re.search(section_pattern, content, re.DOTALL)
                    if section_match:
                        section = section_match.group(0).replace("---", "").strip()
                        help_text += f"\nQuick reference:\n{section}\n"
            except Exception:
                # Just skip the quick reference if it fails
                pass
        
        return help_text
    
    @classmethod
    def print_help_for_error(cls, error_message: str) -> bool:
        """
        Print help information for a known error to the console
        
        Args:
            error_message: The error message to check
            
        Returns:
            True if a matching issue was found, False otherwise
        """
        help_text = cls.format_help_for_error(error_message)
        if help_text:
            print(f"{ErrorColors.YELLOW}{help_text}{ErrorColors.RESET}")
            return True
        return False


class KnownTestIssues(ErrorDocumentationBase):
    """
    Known issues for tests.
    This class maps common test error patterns to their documentation.
    """
    
    # Map of error patterns to issue codes
    ERROR_PATTERNS: Dict[str, str] = {
        "Failed to download video": "OLYMPUS-01",
        "TypeError: 'bool' object is not callable": "OLYMPUS-02",
        "Video is unavailable or has been removed": "YOUTUBE-01",
        "Too many requests. YouTube API quota exceeded": "YOUTUBE-02",
        "Connection refused": "API-01",
        "API key not found or invalid": "API-02",
        "Extension not found or not properly installed": "EXT-01",
        "Test timed out after": "E2E-01",
        "WebDriverException: Chrome executable needs to be in PATH": "E2E-02"
    }
    
    # Map of issue codes to documentation URLs
    ISSUE_DOCS: Dict[str, str] = {
        "OLYMPUS-01": "docs/testing/known_issues.md#olympus-01---failed-to-download-video-error",
        "OLYMPUS-02": "docs/testing/known_issues.md#olympus-02---typeerror-bool-object-is-not-callable",
        "YOUTUBE-01": "docs/testing/known_issues.md#youtube-01---video-unavailable-error",
        "YOUTUBE-02": "docs/testing/known_issues.md#youtube-02---rate-limiting-error",
        "API-01": "docs/testing/known_issues.md#api-01---connection-refused-error",
        "API-02": "docs/testing/known_issues.md#api-02---missing-api-key",
        "EXT-01": "docs/testing/known_issues.md#ext-01---extension-not-found",
        "E2E-01": "docs/testing/known_issues.md#e2e-01---test-timeout",
        "E2E-02": "docs/testing/known_issues.md#e2e-02---browser-driver-not-found"
    }


# Logging functions that use the error documentation system
def info(message: str, logger=None) -> None:
    """Log an informational message"""
    if logger:
        logger.info(message)
    print(f"{ErrorColors.BLUE}[INFO] {message}{ErrorColors.RESET}")

def success(message: str, logger=None) -> None:
    """Log a success message"""
    if logger:
        logger.info(f"SUCCESS: {message}")
    print(f"{ErrorColors.GREEN}[SUCCESS] {message}{ErrorColors.RESET}")

def warning(message: str, logger=None) -> None:
    """Log a warning message"""
    if logger:
        logger.warning(message)
    print(f"{ErrorColors.YELLOW}[WARNING] {message}{ErrorColors.RESET}")

def error(message: str, logger=None) -> None:
    """Log an error message with known issue lookup"""
    if logger:
        logger.error(message)
    print(f"{ErrorColors.RED}[ERROR] {message}{ErrorColors.RESET}")
    # Look for known issues that match this error
    KnownTestIssues.print_help_for_error(message)

def debug(message: str, logger=None) -> None:
    """Log a debug message if verbose mode is enabled"""
    if logger:
        logger.debug(message)
    if '--verbose' in sys.argv:
        print(f"{ErrorColors.CYAN}[DEBUG] {message}{ErrorColors.RESET}") 