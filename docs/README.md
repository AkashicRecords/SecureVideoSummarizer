# Documentation for Secure Video Summarizer

Welcome to the documentation for the Secure Video Summarizer project. This README provides an overview of the documentation structure and how to navigate it.

## Structure

The documentation is organized into the following sections:

- **[guides/](guides/index.md)** - User and developer guides
  - [Quick Start Guide](guides/quick_start.md)
  - [Usage Guide](guides/usage_guide.md)
  - [Error Documentation Guide](guides/error_documentation.md) - NEW!
  - [Development Setup Guide](guides/development_setup.md)

- **[reference/](reference/index.md)** - API and code reference documentation
  - [API Reference](reference/api.md)
  - [Configuration Reference](reference/configuration.md)
  - [Component Reference](reference/components.md)

- **[testing/](testing/index.md)** - Testing documentation
  - [Test Plans](testing/test_plans.md)
  - [Known Issues](testing/known_issues.md)
  - [Test Logging](testing/test_logging.md)

- **[operations/](operations/index.md)** - Operational documentation
  - [Deployment](operations/deployment/index.md)
  - [CI/CD](operations/ci_cd/index.md)
  - [Monitoring](operations/monitoring.md)

- **[templates/](templates/index.md)** - Documentation templates

## Documentation Standards

1. **File Format**: All documentation is in Markdown format (`.md`).
2. **Headers**: Use proper header hierarchy (# for main title, ## for sections, etc.).
3. **Links**: Use relative links for internal documentation.
4. **Images**: Store images in an `images/` directory under the relevant section.
5. **Code Examples**: Use code blocks with language specification.

## Using This Documentation

### Finding Information

- **For users**: Start with the [Quick Start Guide](guides/quick_start.md) and [Usage Guide](guides/usage_guide.md).
- **For developers**: Begin with the [Development Setup Guide](guides/development_setup.md) and refer to the [reference](reference/index.md) section.
- **For troubleshooting**: Check the [Known Issues](testing/known_issues.md) document and the [Error Documentation Guide](guides/error_documentation.md).
- **For operations**: Review the [operations](operations/index.md) documentation.

### Error Documentation System

The project includes a modular error documentation system that:

1. Links error messages to relevant documentation
2. Provides contextual help when errors occur
3. Can be extended for custom components

The [Error Documentation Guide](guides/error_documentation.md) provides details on how to use and extend this system. The error documentation uses a base class approach that allows component-specific error handling while maintaining a consistent interface.

## Contributing to Documentation

1. **New Sections**: Place new documentation in the appropriate section.
2. **Updates**: Keep existing documentation up-to-date with code changes.
3. **Index Files**: Update index files when adding new documents.
4. **Cross-References**: Add cross-references to related documentation.

## Building the Documentation

For local viewing, you can use any Markdown viewer. For web-based viewing, the documentation can be built using [MkDocs](https://www.mkdocs.org/):

```bash
# Install MkDocs
pip install mkdocs

# Build and serve documentation
cd /path/to/project
mkdocs serve
```

Then visit `http://localhost:8000` to view the documentation. 