# Documentation Directory Structure

This guide outlines the standard directory structure for Secure Video Summarizer documentation. Following this structure ensures that documentation remains organized and easy to find.

## Root Documentation Directory (`/docs`)

The root documentation directory contains:

- Main index file (`index.md`)
- Key documentation files that apply to the entire project
- Template and guidelines for creating documentation
- Subdirectories for specialized documentation

## Directory Structure

```
docs/
│
├── index.md                      # Main documentation entry point
├── template.md                   # Template for creating new documentation
├── documentation_guidelines.md   # Guidelines for maintaining documentation
├── directory_structure.md        # This file - structure guide
├── installation.md               # System installation instructions
├── configuration.md              # Configuration options
├── getting_started.md            # Getting started guide
├── backend_api.md                # General API documentation
├── contributing.md               # How to contribute
├── testing.md                    # Testing guidelines
├── code_style.md                 # Code style guidelines
├── changelog.md                  # Version history
│
├── user_guides/                  # Documentation for end users
│   ├── extension_usage.md        # How to use the extension
│   ├── platform_support.md       # Supported video platforms
│   └── ...
│
├── troubleshooting/              # Troubleshooting guides
│   ├── common_issues.md          # Common issues and solutions
│   ├── logging.md                # Logging and debugging
│   ├── diagnostics.md            # Diagnostic tools
│   └── ...
│
├── integrations/                 # Platform integration documentation
│   ├── youtube_integration.md    # YouTube integration
│   ├── olympus_integration.md    # Olympus integration
│   └── ...
│
└── development/                  # Developer-focused documentation
    ├── architecture.md           # System architecture
    ├── extension_development.md  # Extension development guide
    ├── backend_development.md    # Backend development guide
    └── ...
```

## Documentation Placement Guidelines

Follow these guidelines to determine where to place new documentation:

1. **User-facing documentation** goes in `/docs/user_guides/`
   - This includes how-to guides, feature explanations, and usage instructions

2. **Platform-specific integrations** go in `/docs/integrations/`
   - Each supported platform should have its own file
   - Follow the template structure for consistency

3. **Troubleshooting guides** go in `/docs/troubleshooting/`
   - Organized by component or common issue categories

4. **Developer documentation** goes in `/docs/development/`
   - Technical details aimed at developers contributing to the project

5. **General project documentation** goes directly in `/docs/`
   - Installation, configuration, and project-wide guidelines

## Creating New Documentation Directories

If a new category of documentation is needed:

1. Create a new directory with a descriptive name (use lowercase and underscores)
2. Update this directory structure guide
3. Add links to the new documentation in `index.md`

## Backend-Specific Documentation

Some documentation may also exist in the backend directory structure:

```
backend/
├── docs/                         # Backend-specific documentation
│   ├── api/                      # API documentation
│   ├── setup/                    # Setup guides
│   └── development/              # Development guidelines
└── ...
```

When documentation exists in both places, ensure they are consistent or link to each other appropriately. 