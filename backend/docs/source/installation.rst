============
Installation
============

This guide will help you install and set up the Secure Video Summarizer application.

Prerequisites
============

Before installing, make sure you have the following prerequisites:

* Python 3.9 or higher
* pip (Python package installer)
* FFmpeg (for video processing)
* Git (for obtaining the source code)

System Requirements
==================

* **Operating System**: macOS 10.15+ or Windows 10+
* **CPU**: Quad-core processor or better recommended
* **RAM**: Minimum 8GB, 16GB recommended
* **Storage**: At least 1GB free space for the application plus additional space for videos

Basic Installation
=================

1. Clone the repository:

   .. code-block:: bash

       git clone https://github.com/AkashicRecords/SecureVideoSummarizer.git
       cd SecureVideoSummarizer

2. Set up a virtual environment:

   **On macOS/Linux**:

   .. code-block:: bash

       python -m venv venv
       source venv/bin/activate

   **On Windows**:

   .. code-block:: batch

       python -m venv venv
       venv\Scripts\activate

3. Run the setup script:

   **On macOS/Linux**:

   .. code-block:: bash

       ./setup_dev_env.sh

   **On Windows**:

   .. code-block:: batch

       setup_dev_env.bat

   This script will install all dependencies, set up pre-commit hooks, and create necessary directories.

4. Configure environment variables:

   .. code-block:: bash

       cp .env.example .env

   Edit the `.env` file with your specific configuration.

Development Installation
=======================

For development, you'll need additional tools:

.. code-block:: bash

    pip install -r requirements.dev.txt
    pre-commit install

Google OAuth Setup
=================

To use Google OAuth authentication:

1. Go to the Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project
3. Navigate to "APIs & Services" > "Credentials"
4. Configure the OAuth consent screen
5. Create OAuth 2.0 Client IDs
6. Add your Client ID and Client Secret to the `.env` file:

   .. code-block:: bash

       GOOGLE_CLIENT_ID=your_client_id
       GOOGLE_CLIENT_SECRET=your_client_secret
       OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback

Installation Verification
========================

To verify your installation:

.. code-block:: bash

    python run_tests.py

Troubleshooting
==============

Common issues and solutions:

1. **FFmpeg not found**

   Make sure FFmpeg is installed and in your PATH:

   **macOS**:

   .. code-block:: bash

       brew install ffmpeg

   **Windows**:

   Download and install from https://ffmpeg.org/download.html

2. **ImportError: No module named 'xyz'**

   Ensure your virtual environment is activated and try reinstalling dependencies:

   .. code-block:: bash

       pip install -r requirements.lock

3. **Permission denied when running scripts**

   Make scripts executable:

   .. code-block:: bash

       chmod +x *.sh *.py