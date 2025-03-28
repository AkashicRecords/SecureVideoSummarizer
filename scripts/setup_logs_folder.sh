#!/bin/bash

# Script to set up a logs folder and move existing log files there
# Usage: ./setup_logs_folder.sh

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Create logs directory if it doesn't exist
LOGS_DIR="${PROJECT_ROOT}/logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}Creating logs directory at ${LOGS_DIR}${NC}"
    mkdir -p "$LOGS_DIR"
    echo -e "${GREEN}Created logs directory${NC}"
else
    echo -e "${GREEN}Logs directory already exists at ${LOGS_DIR}${NC}"
fi

# Create a .gitignore file in the logs directory if it doesn't exist
GITIGNORE_FILE="${LOGS_DIR}/.gitignore"
if [ ! -f "$GITIGNORE_FILE" ]; then
    echo -e "${YELLOW}Creating .gitignore file in logs directory${NC}"
    cat > "$GITIGNORE_FILE" << EOF
# Ignore all files in this directory
*
# Except this file
!.gitignore
# And except the README
!README.md
EOF
    echo -e "${GREEN}Created .gitignore file${NC}"
else
    echo -e "${GREEN}Logs directory .gitignore already exists${NC}"
fi

# Create a README.md file in the logs directory if it doesn't exist
README_FILE="${LOGS_DIR}/README.md"
if [ ! -f "$README_FILE" ]; then
    echo -e "${YELLOW}Creating README.md file in logs directory${NC}"
    cat > "$README_FILE" << EOF
# Logs Directory

This directory contains log files generated by the Secure Video Summarizer application.

## Log Files

The following types of logs are stored here:

- Backend server logs
- Test execution logs
- Deployment logs
- Error logs

## Log Retention

Log files in this directory are not tracked by Git and should be managed according to your organization's log retention policy.

## Log File Naming Convention

Log files follow this naming convention:

- \`server_YYYY-MM-DD.log\` - Backend server logs
- \`test_component_YYYY-MM-DD.log\` - Test logs for specific components
- \`error_YYYY-MM-DD.log\` - Error logs
EOF
    echo -e "${GREEN}Created README.md file${NC}"
else
    echo -e "${GREEN}Logs directory README.md already exists${NC}"
fi

# Find log files in the project root and subdirectories (excluding certain directories)
echo -e "\n${YELLOW}Searching for log files to move...${NC}"
LOG_FILES=$(find "$PROJECT_ROOT" -type f -name "*.log" -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/logs/*" -not -path "*/\.*/*")

# Move log files to the logs directory
if [ -z "$LOG_FILES" ]; then
    echo -e "${YELLOW}No log files found to move${NC}"
else
    echo -e "${YELLOW}Moving log files to logs directory...${NC}"
    for log_file in $LOG_FILES; do
        filename=$(basename "$log_file")
        destination="${LOGS_DIR}/${filename}"
        
        # If file already exists in destination, append timestamp to filename
        if [ -f "$destination" ]; then
            timestamp=$(date +%Y%m%d_%H%M%S)
            destination="${LOGS_DIR}/${filename%.log}_${timestamp}.log"
        fi
        
        echo "Moving $(basename "$log_file") to logs directory"
        mv "$log_file" "$destination"
    done
    echo -e "${GREEN}All log files moved to logs directory${NC}"
fi

# Update gitignore to exclude logs in case someone puts them elsewhere
MAIN_GITIGNORE="${PROJECT_ROOT}/.gitignore"
if [ -f "$MAIN_GITIGNORE" ]; then
    if ! grep -q "# Log files" "$MAIN_GITIGNORE"; then
        echo -e "\n${YELLOW}Updating main .gitignore file to exclude log files${NC}"
        cat >> "$MAIN_GITIGNORE" << EOF

# Log files
*.log
logs/*
!logs/.gitignore
!logs/README.md
EOF
        echo -e "${GREEN}Updated main .gitignore file${NC}"
    else
        echo -e "${GREEN}Main .gitignore already has log exclusion rules${NC}"
    fi
else
    echo -e "${YELLOW}Creating main .gitignore file${NC}"
    cat > "$MAIN_GITIGNORE" << EOF
# Log files
*.log
logs/*
!logs/.gitignore
!logs/README.md
EOF
    echo -e "${GREEN}Created main .gitignore file${NC}"
fi

echo -e "\n${GREEN}Logs setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update your application code to write logs to the logs directory"
echo "2. Update CI/CD scripts to archive logs from the logs directory"
echo -e "\n${BLUE}Example log path to use in your code:${NC}"
echo '${PROJECT_ROOT}/logs/application_name_$(date +%Y-%m-%d).log' 