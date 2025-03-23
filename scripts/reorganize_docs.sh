#!/bin/bash

# Script to reorganize documentation files into a more structured layout
# Usage: ./reorganize_docs.sh [docs_path]
#
# If docs_path is provided, it will be used as the documentation root
# Otherwise, the script will try to detect it automatically

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Define paths
if [ $# -eq 1 ]; then
    # If path is provided as argument, use it
    DOCS_ROOT="$1"
    if [ ! -d "$DOCS_ROOT" ]; then
        echo -e "${RED}Error: Provided path '$DOCS_ROOT' is not a directory.${NC}"
        exit 1
    fi
else
    # Try to detect docs directory
    if [ -d "${PROJECT_ROOT}/docs" ]; then
        DOCS_ROOT="${PROJECT_ROOT}/docs"
    elif [ -d "${SCRIPT_DIR}/../docs" ]; then
        DOCS_ROOT="${SCRIPT_DIR}/../docs"
    else
        echo -e "${RED}Error: Could not find docs directory.${NC}"
        echo -e "Please provide the path to the docs directory as an argument:"
        echo -e "  ${BLUE}./reorganize_docs.sh /path/to/docs${NC}"
        exit 1
    fi
fi

TEMP_DIR="/tmp/docs_reorganize_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}Starting documentation reorganization...${NC}"
echo -e "Working with docs directory: ${DOCS_ROOT}"

# Check if the directory is a proper docs directory
if [ ! -f "${DOCS_ROOT}/index.md" ] && [ ! -f "${DOCS_ROOT}/README.md" ]; then
    echo -e "${YELLOW}Warning: The specified directory does not appear to be a documentation directory.${NC}"
    echo -e "Could not find index.md or README.md in ${DOCS_ROOT}"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborting.${NC}"
        exit 1
    fi
fi

# Create the new directory structure
echo -e "\n${YELLOW}Creating new directory structure...${NC}"
mkdir -p "${DOCS_ROOT}/guides/user"
mkdir -p "${DOCS_ROOT}/guides/developer"
mkdir -p "${DOCS_ROOT}/reference/api"
mkdir -p "${DOCS_ROOT}/reference/components"
mkdir -p "${DOCS_ROOT}/reference/integrations"
mkdir -p "${DOCS_ROOT}/testing/test_plans"
mkdir -p "${DOCS_ROOT}/testing/templates"
mkdir -p "${DOCS_ROOT}/operations/deployment"
mkdir -p "${DOCS_ROOT}/operations/ci_cd"
mkdir -p "${DOCS_ROOT}/operations/maintenance"
mkdir -p "${DOCS_ROOT}/templates"

# Create temporary directory for backup
mkdir -p "${TEMP_DIR}"
echo -e "Created temporary backup directory: ${TEMP_DIR}"

# Backup current files
echo -e "\n${YELLOW}Backing up current documentation files...${NC}"
cp -r "${DOCS_ROOT}"/* "${TEMP_DIR}/" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup complete.${NC}"
else
    echo -e "${YELLOW}Warning: Some files could not be copied to backup.${NC}"
fi

# Move files to their new locations
echo -e "\n${YELLOW}Moving files to new locations...${NC}"

# Move guides
if [ -f "${DOCS_ROOT}/getting_started.md" ]; then
    cp "${DOCS_ROOT}/getting_started.md" "${DOCS_ROOT}/guides/"
    echo -e "Moved getting_started.md to guides/"
fi

if [ -f "${DOCS_ROOT}/installation.md" ]; then
    cp "${DOCS_ROOT}/installation.md" "${DOCS_ROOT}/guides/"
    echo -e "Moved installation.md to guides/"
fi

if [ -f "${DOCS_ROOT}/configuration.md" ]; then
    cp "${DOCS_ROOT}/configuration.md" "${DOCS_ROOT}/guides/"
    echo -e "Moved configuration.md to guides/"
fi

# Move user guides
if [ -d "${DOCS_ROOT}/user_guides" ]; then
    cp "${DOCS_ROOT}/user_guides"/* "${DOCS_ROOT}/guides/user/" 2>/dev/null
    echo -e "Moved user guides to guides/user/"
fi

# Move developer guides
if [ -f "${DOCS_ROOT}/documentation_guidelines.md" ]; then
    cp "${DOCS_ROOT}/documentation_guidelines.md" "${DOCS_ROOT}/guides/developer/"
    echo -e "Moved documentation_guidelines.md to guides/developer/"
fi

if [ -f "${DOCS_ROOT}/contributing.md" ]; then
    cp "${DOCS_ROOT}/contributing.md" "${DOCS_ROOT}/guides/developer/"
    echo -e "Moved contributing.md to guides/developer/"
fi

if [ -f "${DOCS_ROOT}/code_style.md" ]; then
    cp "${DOCS_ROOT}/code_style.md" "${DOCS_ROOT}/guides/developer/"
    echo -e "Moved code_style.md to guides/developer/"
fi

# Move API reference
if [ -f "${DOCS_ROOT}/backend_api.md" ]; then
    cp "${DOCS_ROOT}/backend_api.md" "${DOCS_ROOT}/reference/api/"
    echo -e "Moved backend_api.md to reference/api/"
fi

# Move components reference
if [ -f "${DOCS_ROOT}/browser_extension.md" ]; then
    cp "${DOCS_ROOT}/browser_extension.md" "${DOCS_ROOT}/reference/components/extension.md"
    echo -e "Moved browser_extension.md to reference/components/extension.md"
fi

# Move integrations reference
if [ -d "${DOCS_ROOT}/integrations" ]; then
    if [ -f "${DOCS_ROOT}/integrations/youtube_integration.md" ]; then
        cp "${DOCS_ROOT}/integrations/youtube_integration.md" "${DOCS_ROOT}/reference/integrations/youtube.md"
        echo -e "Moved youtube_integration.md to reference/integrations/youtube.md"
    fi
    
    if [ -f "${DOCS_ROOT}/integrations/olympus_integration.md" ]; then
        cp "${DOCS_ROOT}/integrations/olympus_integration.md" "${DOCS_ROOT}/reference/integrations/olympus.md"
        echo -e "Moved olympus_integration.md to reference/integrations/olympus.md"
    fi
fi

# Move testing documentation
if [ -f "${DOCS_ROOT}/testing.md" ]; then
    cp "${DOCS_ROOT}/testing.md" "${DOCS_ROOT}/testing/test_strategy.md"
    echo -e "Moved testing.md to testing/test_strategy.md"
fi

if [ -f "${DOCS_ROOT}/test_index.md" ]; then
    cp "${DOCS_ROOT}/test_index.md" "${DOCS_ROOT}/testing/index.md"
    echo -e "Moved test_index.md to testing/index.md"
fi

if [ -f "${DOCS_ROOT}/test_plan_template.md" ]; then
    cp "${DOCS_ROOT}/test_plan_template.md" "${DOCS_ROOT}/testing/templates/"
    echo -e "Moved test_plan_template.md to testing/templates/"
fi

# Move test plans
if [ -d "${DOCS_ROOT}/test_plans" ]; then
    cp "${DOCS_ROOT}/test_plans"/* "${DOCS_ROOT}/testing/test_plans/" 2>/dev/null
    echo -e "Moved test plans to testing/test_plans/"
fi

# Move operations documentation
if [ -d "${DOCS_ROOT}/ci_cd" ]; then
    cp "${DOCS_ROOT}/ci_cd"/* "${DOCS_ROOT}/operations/ci_cd/" 2>/dev/null
    echo -e "Moved CI/CD docs to operations/ci_cd/"
fi

if [ -d "${DOCS_ROOT}/deployment" ]; then
    cp "${DOCS_ROOT}/deployment"/* "${DOCS_ROOT}/operations/deployment/" 2>/dev/null
    echo -e "Moved deployment docs to operations/deployment/"
fi

# Move template
if [ -f "${DOCS_ROOT}/template.md" ]; then
    cp "${DOCS_ROOT}/template.md" "${DOCS_ROOT}/templates/doc_template.md"
    echo -e "Moved template.md to templates/doc_template.md"
fi

# Create index files for each directory
echo -e "\n${YELLOW}Creating index files for directories...${NC}"

# Create guides index
cat > "${DOCS_ROOT}/guides/index.md" << EOF
# Guides

This section contains user and developer guides for the Secure Video Summarizer.

## Getting Started

- [Installation](installation.md) - System requirements and installation steps
- [Configuration](configuration.md) - Environment setup and configuration options
- [Getting Started](getting_started.md) - First steps and basic usage

## User Guides

- [Using the Extension](user/extension_usage.md) - How to use the Chrome extension

## Developer Guides

- [Contributing Guide](developer/contributing.md) - How to contribute to the project
- [Documentation Guidelines](developer/documentation_guidelines.md) - Standards for maintaining documentation
- [Code Style Guide](developer/code_style.md) - Coding standards and practices
EOF
echo -e "Created guides/index.md"

# Create reference index
cat > "${DOCS_ROOT}/reference/index.md" << EOF
# Reference Documentation

This section contains detailed technical reference documentation for the Secure Video Summarizer.

## API Reference

- [Backend API](api/backend_api.md) - API endpoints and usage

## Component Reference

- [Browser Extension](components/extension.md) - Extension design and components

## Integration Reference

- [YouTube Integration](integrations/youtube.md) - Technical details for YouTube support
- [Olympus Integration](integrations/olympus.md) - Technical details for Olympus Learning Platform
EOF
echo -e "Created reference/index.md"

# Create testing index
if [ ! -f "${DOCS_ROOT}/testing/index.md" ]; then
    cat > "${DOCS_ROOT}/testing/index.md" << EOF
# Testing Documentation

This section contains testing documentation for the Secure Video Summarizer.

## Testing Strategy

- [Test Strategy](test_strategy.md) - Comprehensive testing strategy and methodologies

## Test Plans

- [Backend Test Plan](test_plans/backend_test_plan.md) - Testing for the backend server component
- [Extension Test Plan](test_plans/extension_test_plan.md) - Testing for the Chrome extension component
- [Olympus Integration Test Plan](test_plans/olympus_integration_test_plan.md) - Testing for Olympus integration

## Templates

- [Test Plan Template](templates/test_plan_template.md) - Template for creating test plans for new features
EOF
    echo -e "Created testing/index.md"
fi

# Create operations index
cat > "${DOCS_ROOT}/operations/index.md" << EOF
# Operations Documentation

This section contains operational documentation for the Secure Video Summarizer.

## Deployment

- [Deployment Overview](deployment/overview.md) - Overview of the deployment process
- [Backend Deployment](deployment/backend.md) - Backend deployment procedures
- [Extension Deployment](deployment/extension.md) - Extension deployment procedures

## CI/CD

- [CI/CD Overview](ci_cd/overview.md) - Overview of the CI/CD pipeline
- [GitHub Actions Workflow](ci_cd/github_actions_workflow.md) - GitHub Actions configuration

## Maintenance

- [Backup Procedures](maintenance/backup.md) - Backup and recovery procedures
- [Update Procedures](maintenance/updates.md) - System update procedures
EOF
echo -e "Created operations/index.md"

# Update main index file
cat > "${DOCS_ROOT}/index.md" << EOF
# Secure Video Summarizer Documentation

Welcome to the Secure Video Summarizer documentation. This guide provides detailed information on setting up, configuring, and using the Secure Video Summarizer system.

## Documentation Categories

### [User and Developer Guides](guides/index.md)

- [Installation](guides/installation.md) - System requirements and installation steps
- [Configuration](guides/configuration.md) - Environment setup and configuration options
- [Getting Started](guides/getting_started.md) - First steps and basic usage
- [User Guides](guides/user/index.md) - Guides for end users
- [Developer Guides](guides/developer/index.md) - Guides for developers

### [Reference Documentation](reference/index.md)

- [API Reference](reference/api/index.md) - API endpoints and usage
- [Component Reference](reference/components/index.md) - Component design and architecture
- [Integration Reference](reference/integrations/index.md) - Platform integration details

### [Testing Documentation](testing/index.md)

- [Testing Strategy](testing/test_strategy.md) - Overall testing strategy
- [Test Plans](testing/test_plans/index.md) - Detailed test plans
- [Test Templates](testing/templates/index.md) - Templates for test documentation

### [Operations Documentation](operations/index.md)

- [Deployment](operations/deployment/index.md) - Deployment procedures
- [CI/CD](operations/ci_cd/index.md) - Continuous integration and deployment
- [Maintenance](operations/maintenance/index.md) - System maintenance procedures

## Platform Support

The Secure Video Summarizer currently supports the following platforms:

- YouTube
- Olympus Learning Platform (mygreatlearning.com)

## Quick Links

- [GitHub Repository](https://github.com/AkashicRecords/SecureVideoSummarizer)
- [Issue Tracker](https://github.com/AkashicRecords/SecureVideoSummarizer/issues)
- [Change Log](changelog.md)
EOF
echo -e "Updated index.md"

echo -e "\n${GREEN}Documentation reorganization complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the new structure to ensure all files were moved correctly"
echo "2. Update links in the documentation to match the new structure"
echo "3. Once verified, you can remove the old files and directories"
echo "4. A backup of all original files is available at: ${TEMP_DIR}"
echo -e "\n${BLUE}To remove old files after verification, you can run:${NC}"
echo "find ${DOCS_ROOT} -maxdepth 1 -type f -not -name 'index.md' -not -name 'README.md' -not -name 'changelog.md' -exec rm {} \;"
echo "rm -rf ${DOCS_ROOT}/{integrations,user_guides,test_plans,ci_cd,deployment}"

echo -e "\n${BLUE}To create missing documentation from templates, run:${NC}"
echo "./scripts/generate_docs.sh"

echo -e "\n${YELLOW}Note:${NC} You don't need to be in a virtual environment to run documentation scripts." 