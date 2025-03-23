#!/usr/bin/env python3
"""
Script to add a new known issue to the documentation and error handling system.
This script updates both the known_issues.md file and the error_documentation.py file.
"""

import argparse
import os
import re
import sys
from typing import Dict

# Define paths relative to the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
KNOWN_ISSUES_PATH = os.path.join(PROJECT_ROOT, 'docs/testing/known_issues.md')
ERROR_DOC_PATH = os.path.join(PROJECT_ROOT, 'backend/app/utils/error_documentation.py')

# ANSI colors for terminal output
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Add a new known issue to the documentation and error handling system.')
    
    parser.add_argument('--code', required=True, help='Issue code (e.g., OLYMPUS-03)')
    parser.add_argument('--title', required=True, help='Brief title of the issue')
    parser.add_argument('--test', required=True, help='Name of the test function where this occurs')
    parser.add_argument('--error', required=True, help='The error message text')
    parser.add_argument('--cause', required=True, help='What causes this error')
    parser.add_argument('--solution', required=True, help='How to fix the issue')
    parser.add_argument('--doc-link', help='Optional link to additional documentation')
    parser.add_argument('--class', dest='error_class', default='KnownTestIssues', 
                        help='Error documentation class to update (default: KnownTestIssues)')
    
    return parser.parse_args()

def format_issue_entry(args: argparse.Namespace) -> str:
    """Format the issue entry for the known_issues.md file."""
    entry = f"""
#### `{args.code}` - {args.title}

**Test:** `{args.test}`

**Error Message:**
```
{args.error}
```

**Cause:**
{args.cause}

**Solution:**
{args.solution}
"""
    if args.doc_link:
        entry += f"\n**Documentation:** [{os.path.basename(args.doc_link)}]({args.doc_link})"
    
    entry += "\n\n---\n"
    return entry

def add_to_known_issues(args: argparse.Namespace) -> bool:
    """Add the new issue to the known_issues.md file."""
    print(f"{Color.BLUE}Adding issue to {KNOWN_ISSUES_PATH}...{Color.RESET}")
    
    try:
        # Read the current content
        with open(KNOWN_ISSUES_PATH, 'r') as file:
            content = file.read()
        
        # Check if the issue already exists
        if f"`{args.code}`" in content:
            print(f"{Color.YELLOW}Warning: Issue {args.code} already exists in the documentation.{Color.RESET}")
            return False
        
        # Find the appropriate section to add the issue
        category = args.code.split('-')[0]
        section_pattern = f"### {category} "
        
        if category == "OLYMPUS":
            section_title = "Olympus Integration Tests"
        elif category == "YOUTUBE":
            section_title = "YouTube Integration Tests"
        elif category == "API":
            section_title = "API Tests"
        elif category == "EXT":
            section_title = "Extension Tests"
        elif category == "E2E":
            section_title = "End-to-End Tests"
        else:
            section_title = f"{category} Tests"
        
        section_match = re.search(f"### {section_title}", content)
        
        if section_match:
            # Find where the section ends
            next_section = re.search(r"### \w+", content[section_match.end():])
            if next_section:
                insert_pos = section_match.end() + next_section.start()
            else:
                insert_pos = len(content)
            
            # Insert the new issue entry
            new_content = content[:insert_pos] + format_issue_entry(args) + content[insert_pos:]
        else:
            print(f"{Color.YELLOW}Warning: Section for {category} not found. Adding to the end of the file.{Color.RESET}")
            new_content = content + f"\n### {section_title}\n" + format_issue_entry(args)
        
        # Write the updated content
        with open(KNOWN_ISSUES_PATH, 'w') as file:
            file.write(new_content)
        
        print(f"{Color.GREEN}Successfully added issue {args.code} to the documentation.{Color.RESET}")
        return True
    
    except Exception as e:
        print(f"{Color.RED}Error adding issue to documentation: {str(e)}{Color.RESET}")
        return False

def update_error_documentation(args: argparse.Namespace) -> bool:
    """Update the ERROR_PATTERNS and ISSUE_DOCS dictionaries in error_documentation.py."""
    print(f"{Color.BLUE}Updating error patterns in {ERROR_DOC_PATH}...{Color.RESET}")
    
    try:
        # Read the current content
        with open(ERROR_DOC_PATH, 'r') as file:
            content = file.read()
        
        # Create the anchor link from the title
        anchor = args.title.lower().replace(' ', '-').replace('"', '').replace("'", '')
        doc_link = f"docs/testing/known_issues.md#{args.code.lower()}---{anchor}"
        
        # Check if the pattern already exists
        if f'"{args.code}"' in content:
            print(f"{Color.YELLOW}Warning: Issue code {args.code} already exists in error_documentation.py.{Color.RESET}")
            return False
        
        # Extract key parts of the error message for the pattern
        error_pattern = ' '.join(args.error.split()[:4])  # First few words of the error
        
        # Find the correct class to update
        class_pattern = rf"class\s+{args.error_class}\s*\([^)]+\):.*?ERROR_PATTERNS\s*=\s*{{([^}}]*)}}"
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if not class_match:
            print(f"{Color.RED}Error: Could not find class {args.error_class} in error_documentation.py{Color.RESET}")
            return False
        
        # Update ERROR_PATTERNS
        patterns_content = class_match.group(1)
        new_pattern = f'        "{error_pattern}": "{args.code}",\n'
        
        # Check if the last line ends with a comma
        lines = patterns_content.strip().split('\n')
        if lines and not lines[-1].strip().endswith(','):
            new_pattern = ',' + new_pattern
        
        # Insert the new pattern
        new_patterns_content = patterns_content.rstrip() + new_pattern + '    }'
        new_content = re.sub(class_pattern, f"class {args.error_class}(ErrorDocumentationBase):\n    ERROR_PATTERNS = {{\n{new_patterns_content}", content, flags=re.DOTALL)
        
        # Find and update ISSUE_DOCS
        docs_pattern = rf"class\s+{args.error_class}\s*\([^)]+\):.*?ISSUE_DOCS\s*=\s*{{([^}}]*)}}"
        docs_match = re.search(docs_pattern, new_content, re.DOTALL)
        
        if not docs_match:
            print(f"{Color.RED}Error: Could not find ISSUE_DOCS in class {args.error_class}{Color.RESET}")
            return False
        
        # Update ISSUE_DOCS
        docs_content = docs_match.group(1)
        new_doc = f'        "{args.code}": "{doc_link}",\n'
        
        # Check if the last line ends with a comma
        lines = docs_content.strip().split('\n')
        if lines and not lines[-1].strip().endswith(','):
            new_doc = ',' + new_doc
        
        new_docs_content = docs_content.rstrip() + new_doc + '    }'
        new_content = re.sub(docs_pattern, f"class {args.error_class}(ErrorDocumentationBase):\n    ISSUE_DOCS = {{\n{new_docs_content}", new_content, flags=re.DOTALL)
        
        # Write the updated content
        with open(ERROR_DOC_PATH, 'w') as file:
            file.write(new_content)
        
        print(f"{Color.GREEN}Successfully updated error patterns in error_documentation.py.{Color.RESET}")
        return True
    
    except Exception as e:
        print(f"{Color.RED}Error updating error_documentation.py: {str(e)}{Color.RESET}")
        return False

def main():
    """Main function to add a new known issue."""
    args = parse_arguments()
    
    # Validate issue code format
    if not re.match(r"^[A-Z]+-\d+$", args.code):
        print(f"{Color.RED}Error: Issue code must be in the format CATEGORY-XX (e.g., OLYMPUS-03).{Color.RESET}")
        sys.exit(1)
    
    # Add to known_issues.md
    docs_success = add_to_known_issues(args)
    
    # Update error_documentation.py
    helpers_success = update_error_documentation(args)
    
    if docs_success and helpers_success:
        print(f"\n{Color.GREEN}Successfully added known issue {args.code}.{Color.RESET}")
        print(f"\n{Color.BLUE}To use this issue in your code:{Color.RESET}")
        print(f"When you encounter this error, log it using the error() function:")
        print(f"""
from app.utils.error_documentation import error

# This will automatically link to the documentation
error("{args.error}")
""")
        
        print(f"\nOr use the class directly:")
        print(f"""
from app.utils.error_documentation import {args.error_class}

# Check if this is a known issue and print help
{args.error_class}.print_help_for_error("{args.error}")
""")
    else:
        print(f"\n{Color.YELLOW}Issue adding known issue {args.code}. Please check the warnings above.{Color.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main() 