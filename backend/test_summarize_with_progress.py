#!/usr/bin/env python
"""
Test script for video summarization with progress tracking.
This script uploads a video and tracks the summarization job progress.
"""

import os
import sys
import time
import json
import uuid
import logging
import argparse
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('progress_test')

class SummarizerClient:
    """Client for interacting with the Summarizer API with progress tracking."""
    
    def __init__(self, base_url='http://localhost:8080'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_api_health(self):
        """Check if API is running."""
        try:
            response = self.session.get(urljoin(self.base_url, '/api/health'))
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def upload_video(self, video_path):
        """Upload a video file to the server."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Uploading video: {video_path}")
        with open(video_path, 'rb') as video_file:
            files = {'file': (os.path.basename(video_path), video_file)}
            response = self.session.post(
                urljoin(self.base_url, '/api/upload'),
                files=files
            )
        
        if response.status_code != 200:
            logger.error(f"Failed to upload video: {response.text}")
            raise Exception(f"Failed to upload video: {response.status_code}")
        
        result = response.json()
        logger.info(f"Video uploaded successfully: {result.get('filename')}")
        return result
    
    def create_summary_job(self, filename):
        """Start a summarization job and return the job ID."""
        logger.info(f"Creating summarization job for: {filename}")
        response = self.session.post(
            urljoin(self.base_url, '/api/summarize'),
            json={'filename': filename}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create summary job: {response.text}")
            raise Exception(f"Failed to create summary job: {response.status_code}")
        
        result = response.json()
        job_id = result.get('job_id')
        logger.info(f"Summary job created successfully with ID: {job_id}")
        return job_id
    
    def get_job_status(self, job_id):
        """Get the status of a specific job."""
        response = self.session.get(
            urljoin(self.base_url, f'/api/admin/jobs/{job_id}')
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get job status: {response.text}")
            return None
        
        return response.json()
    
    def get_summary(self, filename):
        """Get the summary for a video."""
        logger.info(f"Retrieving summary for: {filename}")
        response = self.session.get(
            urljoin(self.base_url, f'/api/summary/{filename}')
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get summary: {response.text}")
            return None
        
        return response.json()

def run_test(video_path, api_url, poll_interval=3, timeout=300):
    """Run the summarization progress test."""
    client = SummarizerClient(api_url)
    
    # Check if API is running
    logger.info("Checking if API is running...")
    if not client.check_api_health():
        logger.error("API is not running. Please start the backend server.")
        return False
    
    try:
        # Upload video
        upload_result = client.upload_video(video_path)
        filename = upload_result.get('filename')
        
        # Create summary job
        job_id = client.create_summary_job(filename)
        
        # Poll for job status
        logger.info(f"Polling job status every {poll_interval} seconds (timeout: {timeout}s)")
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < timeout:
            job_status = client.get_job_status(job_id)
            
            if not job_status:
                logger.warning("Could not retrieve job status")
                time.sleep(poll_interval)
                continue
            
            status = job_status.get('status')
            progress = job_status.get('progress', 0)
            stage = job_status.get('stage', 'unknown')
            
            # Display progress bar
            bar_length = 30
            filled_length = int(bar_length * progress / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"\rProgress: [{bar}] {progress:.1f}% - Stage: {stage}", end='')
            
            if status == 'completed':
                print("\nJob completed successfully!")
                completed = True
                break
            elif status == 'failed':
                print(f"\nJob failed: {job_status.get('error', 'Unknown error')}")
                return False
            
            time.sleep(poll_interval)
        
        if not completed:
            logger.error(f"Job did not complete within timeout period ({timeout}s)")
            return False
        
        # Get summary
        summary = client.get_summary(filename)
        if summary:
            print("\nSummary retrieved successfully:")
            print("-" * 80)
            print(summary.get('summary', 'No summary available'))
            print("-" * 80)
            return True
        else:
            logger.error("Failed to retrieve summary")
            return False
            
    except Exception as e:
        logger.exception(f"Error during test: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test video summarization with progress tracking")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--api", default="http://localhost:8080", help="API base URL")
    parser.add_argument("--interval", type=int, default=3, help="Polling interval in seconds")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    success = run_test(
        args.video,
        args.api,
        poll_interval=args.interval,
        timeout=args.timeout
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 