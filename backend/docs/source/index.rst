=======================
Secure Video Summarizer
=======================

.. image:: ../../Assets/SVS.jpg
   :width: 200
   :alt: Secure Video Summarizer Logo

A secure backend application for summarizing video content with privacy-focused features.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   development
   security
   architecture
   components

Features
========

Security Features
----------------

* **Google OAuth Authentication**: Secure user authentication using Google SSO
* **Rate Limiting**: Protection against brute force and DoS attacks
* **CSRF Protection**: State parameter validation in OAuth flow
* **Secure Session Management**: Signed, HTTP-only cookies with proper expiration
* **Security Headers**: Implementation of recommended security headers
* **Input Validation**: Thorough validation of all user inputs
* **Privacy-Focused**: Videos processed locally without sending to third-party services
* **Comprehensive Logging**: Detailed logging of all operations with rotating file handlers
* **Robust Error Handling**: Centralized error handling with custom API error responses

Video Processing Features
------------------------

* **Local Processing**: All video processing happens locally for privacy
* **Audio Extraction**: Separation of audio tracks from video
* **Transcription**: Converting speech to text
* **Summarization**: Using LLMs to generate concise summaries
* **Browser Extension**: Integration with the Olympus platform for seamless workflow
* **Cross-Platform Support**: Works on macOS and Windows

Indices and tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 