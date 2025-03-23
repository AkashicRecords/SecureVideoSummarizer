#!/bin/bash

# Script to generate CI/CD documentation files from templates
# Usage: ./generate_cicd_docs.sh

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define paths
DOCS_ROOT="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/docs"
CICD_DIR="$DOCS_ROOT/ci_cd"
TEMPLATE_PATH="$DOCS_ROOT/template.md"

# Check if template exists
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_PATH${NC}"
    exit 1
fi

# Check if CI/CD directory exists
if [ ! -d "$CICD_DIR" ]; then
    echo -e "${YELLOW}Creating CI/CD directory at $CICD_DIR${NC}"
    mkdir -p "$CICD_DIR"
fi

# Define the CI/CD documentation files to create
declare -a CICD_DOCS=(
    "ci_pipeline_setup:CI Pipeline Setup Guide"
    "github_actions_workflow:GitHub Actions Workflow Configuration"
    "test_automation_ci:Test Automation in CI"
    "pipeline_reports:Pipeline Reports Guide"
    "pipeline_monitoring:Pipeline Monitoring Guide"
    "build_notifications:Build Notifications Setup"
    "failure_handling:Pipeline Failure Handling"
    "best_practices:CI/CD Best Practices"
    "pipeline_optimization:Pipeline Optimization Guide"
    "github_actions_reference:GitHub Actions Reference"
    "pipeline_yaml_examples:Pipeline YAML Examples"
)

# Create each CI/CD documentation file
for doc in "${CICD_DOCS[@]}"; do
    # Split the entry into filename and title
    filename="${doc%%:*}"
    title="${doc#*:}"
    
    # Create the target file path
    target_file="$CICD_DIR/${filename}.md"
    
    # Skip if file already exists
    if [ -f "$target_file" ]; then
        echo -e "${YELLOW}File already exists, skipping: $target_file${NC}"
        continue
    fi
    
    # Copy the template to the target location
    cp "$TEMPLATE_PATH" "$target_file"
    
    # Replace the placeholder title with the actual title
    sed -i.bak "s/\[Component\/Integration Name\]/${title}/g" "$target_file" && rm "${target_file}.bak"
    
    echo -e "${GREEN}Created documentation file:${NC} $target_file"
done

echo -e "\n${GREEN}CI/CD documentation generation complete!${NC}"
echo -e "Created $(echo "${CICD_DOCS[@]}" | wc -w | xargs) documentation files in $CICD_DIR"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit each file to add content relevant to the topic"
echo "2. Ensure all links are updated in the index.md file"
echo "3. Consider adding these files to version control" 