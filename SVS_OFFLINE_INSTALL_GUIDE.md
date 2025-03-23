# Secure Video Summarizer - Offline Installation Guide

This guide explains how to prepare and perform an offline installation of the Secure Video Summarizer (SVS) application for environments without internet access.

## Overview

The offline installation process consists of two main steps:

1. **Packaging Dependencies**: Downloading all required dependencies on a machine with internet access
2. **Offline Installation**: Installing the application and its dependencies on a machine without internet access

The SVS offline installation system is designed to maintain strict version control of all dependencies. This ensures:

- Exact dependency versions are maintained across all installations
- No automatic upgrading of packages that could introduce conflicts
- Consistent environment between development, testing, and production
- No unexpected behavior from version differences

## Prerequisites

- Python 3.8 or higher
- `pip` package manager
- Access to a machine with internet connection (for the packaging step)

## Step 1: Packaging Dependencies (On a Machine with Internet Access)

1. Clone or download the SVS repository:
   ```
   git clone <repository-url>
   cd SVS
   ```

2. Run the packaging script:
   ```
   ./package_dependencies.sh
   ```

   This script will:
   - Create a virtual environment
   - Download all required dependencies to `backend/vendor/`
   - Create an offline installation script (`install_offline.sh`)
   - Update the startup script to support offline installation
   - Make all scripts executable

3. Transfer the entire SVS directory to the target machine without internet access. Make sure to include the `backend/vendor/` directory, which contains all the downloaded packages.

## Step 2: Offline Installation (On a Machine without Internet Access)

### Option 1: Using the Dedicated Offline Installation Script

1. Navigate to the SVS directory:
   ```
   cd SVS
   ```

2. Run the offline installation script:
   ```
   ./install_offline.sh
   ```

   This script will:
   - Create a virtual environment
   - Install all dependencies from the vendor directory
   - Configure the application for use

3. Start the application using the normal startup script:
   ```
   ./start_svs_application.sh
   ```

### Option 2: Using the Startup Script with Offline Installation Option

1. Navigate to the SVS directory:
   ```
   cd SVS
   ```

2. Run the startup script:
   ```
   ./start_svs_application.sh
   ```

3. Select option `5) Offline installation (using packaged dependencies)` from the menu.

## External Dependencies

Note that the following system dependencies are still required and must be installed separately:

- `ffmpeg`: Required for audio/video processing
- `libmagic`: Required for file type detection

### Installing External Dependencies Without Internet

- **FFmpeg**: Download the binaries from [ffmpeg.org](https://ffmpeg.org/download.html) on a machine with internet, then transfer and install them on the target machine.
  
- **libmagic**:
  - On Linux: Use the distribution's package manager or manually install from a downloaded package
  - On macOS: Install via a downloaded Homebrew bottle
  - On Windows: The Python dependency `python-magic-bin` includes the necessary DLLs (included in the vendor directory)

## Troubleshooting

If you encounter any issues during offline installation:

1. **Missing Dependencies**: Ensure all packages in the vendor directory were properly downloaded. If some are missing, rerun `package_dependencies.sh` on a machine with internet access.

2. **Permission Issues**: Make sure all scripts have execution permissions:
   ```
   chmod +x *.sh
   ```

3. **Python Version Mismatch**: Ensure the Python version on the target machine is compatible with the downloaded packages (Python 3.8+ recommended).

4. **External Dependency Issues**: Check that system dependencies like `ffmpeg` are properly installed and in the system PATH.

5. **Dependency Version Conflicts**: The offline installation strictly enforces dependency versions from the requirements.lock file. If you need to update a specific package version, edit the requirements.lock file before running `package_dependencies.sh`. Note that changing dependency versions is at your own risk and may introduce conflicts.

## Updates and Version Management

The SVS application includes an update checker that can download the latest approved dependency versions from the official GitHub repository. To ensure stability and avoid conflicts:

1. **Updates During Cold Start**: Updates are checked and applied only during the Cold Start process to prevent conflicts with existing installations.

2. **Approved Updates Only**: The system only offers updates that have been tested and approved by the SVS team.

3. **Repackaging After Updates**: After applying updates, rerun `package_dependencies.sh` to download the updated dependencies for offline installation.

4. **Version Control**: All dependency versions are explicitly specified to maintain consistency across different installations.

For additional support, please consult the main documentation or contact the development team. 