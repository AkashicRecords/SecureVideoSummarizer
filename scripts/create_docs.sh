#!/bin/bash

# Script to create new documentation files based on the template
# Usage: ./create_docs.sh <doc_type> <doc_name>
# Example: ./create_docs.sh integration new_platform

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define paths
DOCS_ROOT="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/docs"
TEMPLATE_PATH="$DOCS_ROOT/template.md"

# Check if template exists
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_PATH${NC}"
    exit 1
fi

# Check arguments
if [ "$#" -ne 2 ]; then
    echo -e "${YELLOW}Usage: ./create_docs.sh <doc_type> <doc_name>${NC}"
    echo "Available doc_types:"
    echo "  - integration (creates a file in integrations/)"
    echo "  - user_guide (creates a file in user_guides/)"
    echo "  - troubleshooting (creates a file in troubleshooting/)"
    echo "  - development (creates a file in development/)"
    echo "  - root (creates a file in the root docs directory)"
    echo -e "${YELLOW}Example: ./create_docs.sh integration new_platform${NC}"
    exit 1
fi

DOC_TYPE=$1
DOC_NAME=$2

# Determine the target directory based on doc_type
case "$DOC_TYPE" in
    "integration")
        TARGET_DIR="$DOCS_ROOT/integrations"
        ;;
    "user_guide")
        TARGET_DIR="$DOCS_ROOT/user_guides"
        ;;
    "troubleshooting")
        TARGET_DIR="$DOCS_ROOT/troubleshooting"
        ;;
    "development")
        TARGET_DIR="$DOCS_ROOT/development"
        ;;
    "root")
        TARGET_DIR="$DOCS_ROOT"
        ;;
    *)
        echo -e "${RED}Error: Invalid doc_type. Use 'integration', 'user_guide', 'troubleshooting', 'development', or 'root'.${NC}"
        exit 1
        ;;
esac

# Create the target file path
TARGET_FILE="$TARGET_DIR/${DOC_NAME}.md"

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Creating directory $TARGET_DIR${NC}"
    mkdir -p "$TARGET_DIR"
fi

# Check if target file already exists
if [ -f "$TARGET_FILE" ]; then
    echo -e "${RED}Error: File already exists at $TARGET_FILE${NC}"
    echo "Please choose a different name or remove the existing file."
    exit 1
fi

# Copy the template to the target location
cp "$TEMPLATE_PATH" "$TARGET_FILE"

# Replace the placeholder title with the actual name
sed -i.bak "s/\[Component\/Integration Name\]/${DOC_NAME^}/g" "$TARGET_FILE" && rm "${TARGET_FILE}.bak"

echo -e "${GREEN}Documentation file created at:${NC} $TARGET_FILE"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit the file to add your content"
echo "2. Update the index.md file to include a link to your new documentation"
echo "3. Add the file to version control with git"

# Suggest an index.md entry
RELATIVE_PATH=$(realpath --relative-to="$DOCS_ROOT" "$TARGET_FILE")
echo -e "\n${YELLOW}Suggested index.md entry:${NC}"
echo "- [${DOC_NAME^}]($RELATIVE_PATH) - Description of $DOC_NAME" 