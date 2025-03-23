import sys
import re
import os
from typing import Dict, List, Optional, Tuple

# Colors for terminal output
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class KnownIssues:
    """
    A utility class to map test failures to their documentation entries.
    This helps developers quickly find solutions to common test failures.
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
    
    @staticmethod
    def get_project_root() -> str:
        """Get the project root directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up from app/utils to the project root
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
    def print_help_for_error(cls, error_message: str) -> bool:
        """
        Print help information for a known error
        
        Args:
            error_message: The error message to check
            
        Returns:
            True if a matching issue was found, False otherwise
        """
        match = cls.find_matching_issue(error_message)
        if match:
            issue_code, doc_path = match
            print(f"\n{Color.YELLOW}This appears to be a known issue: {Color.BOLD}{issue_code}{Color.RESET}")
            print(f"{Color.YELLOW}For more information and solutions, see:{Color.RESET}")
            print(f"{Color.CYAN}{doc_path}{Color.RESET}\n")
            
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
                            print(f"{Color.PURPLE}Quick reference:{Color.RESET}")
                            print(f"{section}\n")
                except Exception as e:
                    # Just log the error and continue - this is just a helpful extra
                    print(f"{Color.YELLOW}Could not extract quick reference: {str(e)}{Color.RESET}")
            
            return True
        return False


def info(message: str) -> None:
    """Log an informational message"""
    print(f"{Color.BLUE}[INFO] {message}{Color.RESET}")

def success(message: str) -> None:
    """Log a success message"""
    print(f"{Color.GREEN}[SUCCESS] {message}{Color.RESET}")

def warning(message: str) -> None:
    """Log a warning message"""
    print(f"{Color.YELLOW}[WARNING] {message}{Color.RESET}")

def error(message: str) -> None:
    """Log an error message with known issue lookup"""
    print(f"{Color.RED}[ERROR] {message}{Color.RESET}")
    # Look for known issues that match this error
    KnownIssues.print_help_for_error(message)

def debug(message: str) -> None:
    """Log a debug message if verbose mode is enabled"""
    if '--verbose' in sys.argv:
        print(f"{Color.CYAN}[DEBUG] {message}{Color.RESET}") 