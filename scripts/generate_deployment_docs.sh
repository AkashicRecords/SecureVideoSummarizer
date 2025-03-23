#!/bin/bash

# Script to generate deployment documentation files from templates
# Usage: ./generate_deployment_docs.sh

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define paths
DOCS_ROOT="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")/docs"
DEPLOYMENT_DIR="$DOCS_ROOT/deployment"
TEMPLATE_PATH="$DOCS_ROOT/template.md"

# Check if template exists
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_PATH${NC}"
    exit 1
fi

# Check if deployment directory exists
if [ ! -d "$DEPLOYMENT_DIR" ]; then
    echo -e "${YELLOW}Creating deployment directory at $DEPLOYMENT_DIR${NC}"
    mkdir -p "$DEPLOYMENT_DIR"
fi

# Define the deployment documentation files to create
declare -a DEPLOYMENT_DOCS=(
    "dev_environment:Development Environment Setup"
    "dev_deployment:Development Deployment Procedure"
    "local_development:Local Development Setup"
    "staging_environment:Staging Environment Setup"
    "staging_deployment:Staging Deployment Procedure"
    "staging_testing:Staging Environment Testing"
    "production_environment:Production Environment Setup"
    "production_deployment:Production Deployment Procedure"
    "production_monitoring:Production Monitoring Setup"
    "backend_deployment:Backend Deployment Process"
    "database_migrations:Database Migration Procedures"
    "environment_variables:Environment Variables Reference"
    "extension_packaging:Extension Packaging Guide"
    "chrome_web_store:Chrome Web Store Publishing"
    "extension_updates:Extension Update Procedures"
    "deployment_pipeline:Deployment Pipeline Overview"
    "deployment_scripts:Deployment Scripts Reference"
    "infrastructure_setup:Infrastructure Setup Guide"
    "server_requirements:Server Requirements Specification"
    "scaling_configuration:Scaling Configuration Guide"
    "security_configuration:Security Configuration Guide"
    "backup_recovery:Backup and Recovery Procedures"
    "update_procedures:Update Procedures"
    "rollback_procedures:Rollback Procedures"
    "deployment_issues:Common Deployment Issues"
    "runtime_issues:Runtime Troubleshooting"
    "performance_issues:Performance Troubleshooting"
    "deployment_best_practices:Deployment Best Practices"
    "configuration_management:Configuration Management Guide"
    "release_management:Release Management Procedures"
)

# Create each deployment documentation file
for doc in "${DEPLOYMENT_DOCS[@]}"; do
    # Split the entry into filename and title
    filename="${doc%%:*}"
    title="${doc#*:}"
    
    # Create the target file path
    target_file="$DEPLOYMENT_DIR/${filename}.md"
    
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

echo -e "\n${GREEN}Deployment documentation generation complete!${NC}"
echo -e "Created $(echo "${DEPLOYMENT_DOCS[@]}" | wc -w | xargs) documentation files in $DEPLOYMENT_DIR"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit each file to add content relevant to the topic"
echo "2. Ensure all links are updated in the index.md file"
echo "3. Consider adding these files to version control" 