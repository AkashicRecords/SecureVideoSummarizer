#!/usr/bin/env python
"""
Test script to verify all dependencies are installed and importable.
Run with: python -m tests.test_dependencies
"""
import sys
import os
import importlib
import unittest
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DependencyTests(unittest.TestCase):
    """Test that all required dependencies can be imported"""

    def test_flask_dependencies(self):
        """Test Flask and its extensions"""
        dependencies = [
            "flask",
            "flask_cors",
            "flask_session",
            "flask_limiter"
        ]
        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    importlib.import_module(dep)
                    logger.info(f"✓ Successfully imported {dep}")
                except ImportError as e:
                    logger.error(f"✗ Failed to import {dep}: {str(e)}")
                    self.fail(f"Failed to import {dep}: {str(e)}")

    def test_audio_processing_dependencies(self):
        """Test audio processing libraries"""
        dependencies = [
            "pydub", 
            "speech_recognition"
        ]
        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    importlib.import_module(dep)
                    logger.info(f"✓ Successfully imported {dep}")
                except ImportError as e:
                    logger.error(f"✗ Failed to import {dep}: {str(e)}")
                    self.fail(f"Failed to import {dep}: {str(e)}")

    def test_file_handling_dependencies(self):
        """Test file handling libraries"""
        # python-magic is installed as 'magic'
        dependencies = ["magic"]
        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    importlib.import_module(dep)
                    logger.info(f"✓ Successfully imported {dep}")
                except ImportError as e:
                    logger.error(f"✗ Failed to import {dep}: {str(e)}")
                    self.fail(f"Failed to import {dep}: {str(e)}")

    def test_google_dependencies(self):
        """Test Google related libraries"""
        dependencies = [
            "google.auth",
            "google_auth_oauthlib.flow",
            "googleapiclient.discovery"
        ]
        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    importlib.import_module(dep)
                    logger.info(f"✓ Successfully imported {dep}")
                except ImportError as e:
                    logger.error(f"✗ Failed to import {dep}: {str(e)}")
                    self.fail(f"Failed to import {dep}: {str(e)}")

    def test_ai_dependencies(self):
        """Test AI related libraries"""
        dependencies = [
            "elevenlabs"
        ]
        for dep in dependencies:
            with self.subTest(dependency=dep):
                try:
                    importlib.import_module(dep)
                    logger.info(f"✓ Successfully imported {dep}")
                except ImportError as e:
                    logger.error(f"✗ Failed to import {dep}: {str(e)}")
                    self.fail(f"Failed to import {dep}: {str(e)}")
                    
    def test_no_openai_dependency(self):
        """Make sure openai is not being imported directly"""
        try:
            import openai
            self.fail("OpenAI should NOT be importable - it was never intended to be a dependency")
        except ImportError:
            logger.info("✓ Confirmed OpenAI is not importable (as expected)")
    
    def test_app_modules(self):
        """Test that our own app modules can be imported"""
        # Make sure parent directory is in path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        modules = [
            "app.main",
            "app.config",
            "app.api.routes",
            "app.api.youtube_routes",
            "app.api.olympus_routes",
            "app.utils.audio_processor",
            "app.utils.helpers",
            "app.utils.validators",
            "app.utils.errors",
            "app.summarizer.processor",
            "app.summarizer.ollama_client"
        ]
        for module in modules:
            with self.subTest(module=module):
                try:
                    importlib.import_module(module)
                    logger.info(f"✓ Successfully imported {module}")
                except Exception as e:
                    logger.error(f"✗ Failed to import {module}: {str(e)}")
                    logger.error(traceback.format_exc())
                    self.fail(f"Failed to import {module}: {str(e)}")
    
    def test_extension_routes_existence(self):
        """Check if extension_routes.py exists, create it if not"""
        # Make sure parent directory is in path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        # Check if the file exists
        extension_routes_path = os.path.join(parent_dir, 'app', 'api', 'extension_routes.py')
        if not os.path.exists(extension_routes_path):
            logger.warning(f"extension_routes.py does not exist at {extension_routes_path}")
            
            # Try to create it by importing app.main which has the create_extension_routes function
            try:
                from app.main import create_extension_routes
                create_extension_routes()
                self.assertTrue(os.path.exists(extension_routes_path), 
                               "extension_routes.py should have been created")
                logger.info("✓ Successfully created extension_routes.py")
            except Exception as e:
                logger.error(f"Failed to create extension_routes.py: {str(e)}")
                self.fail(f"Failed to create extension_routes.py: {str(e)}")
        else:
            logger.info(f"✓ extension_routes.py exists at {extension_routes_path}")

if __name__ == "__main__":
    unittest.main() 