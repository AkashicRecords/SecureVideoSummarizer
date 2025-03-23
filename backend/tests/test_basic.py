#!/usr/bin/env python3
# Basic test file to demonstrate the test runner functionality

import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from unittest import mock
from app.main import create_app
from tests.test_helpers_validation import (
    create_test_audio_file,
    create_test_video_file,
    create_test_summary_data,
    validate_audio_file
)

class TestBasic(unittest.TestCase):
    """Basic test case to demonstrate test runner functionality"""
    
    def test_addition(self):
        """Test that addition works"""
        self.assertEqual(2 + 2, 4)
    
    def test_subtraction(self):
        """Test that subtraction works"""
        self.assertEqual(5 - 2, 3)
    
    def test_multiplication(self):
        """Test that multiplication works"""
        self.assertEqual(3 * 4, 12)
    
    def test_division(self):
        """Test that division works"""
        self.assertEqual(8 / 4, 2)

class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of the application."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = mock.patch.dict(os.environ, {
            'GOOGLE_CLIENT_SECRETS_FILE': 'dummy_path',
            'FRONTEND_URL': 'http://localhost:3000',
            'BROWSER_EXTENSION_ID': 'test_extension_id',
            'ALLOWED_ORIGINS': 'http://localhost:3000,chrome-extension://test_extension_id'
        })
        self.env_patcher.start()
        
        # Create a test Flask app with testing config
        self.app = create_app('testing')
        
        # Configure app for testing
        self.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False,
            'SECRET_KEY': 'test_secret_key'
        })
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
        self.env_patcher.stop()
    
    def test_app_creation(self):
        """Test that the application is created correctly."""
        self.assertTrue(self.app is not None)
        self.assertEqual(self.app.config['TESTING'], True)
    
    def test_extension_status_endpoint(self):
        """Test the extension status endpoint."""
        response = self.client.get('/api/extension/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'connected')
    
    def test_api_route_exists(self):
        """Test that the API routes exist."""
        response = self.client.get('/api/extension/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'connected')
    
    def test_audio_file_creation(self):
        """Test that audio files can be created."""
        audio_path, temp_dir = create_test_audio_file()
        try:
            self.assertTrue(os.path.exists(audio_path))
            self.assertTrue(validate_audio_file(audio_path))
        finally:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
    
    def test_video_file_creation(self):
        """Test that video files can be created."""
        video_path, temp_dir = create_test_video_file()
        try:
            self.assertTrue(os.path.exists(video_path))
            # Check file size
            self.assertGreater(os.path.getsize(video_path), 0)
        finally:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
    
    def test_summary_data_creation(self):
        """Test that summary data can be created."""
        summary_data = create_test_summary_data()
        self.assertIn('summary', summary_data)
        self.assertIn('video_data', summary_data)
        self.assertIn('title', summary_data['video_data'])
        self.assertIn('duration', summary_data['video_data'])
        self.assertIn('src', summary_data['video_data'])

if __name__ == "__main__":
    unittest.main() 