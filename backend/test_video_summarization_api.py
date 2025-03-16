#!/usr/bin/env python
import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path

"""
Test script for the video summarization API endpoint.
This script:
1. Uploads a video file to the server
2. Retrieves the video ID
3. Sends a request to summarize the video
4. Displays the summarization results
"""

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the video summarization API")
    parser.add_argument("video_path", help="Path to a video file to upload and summarize")
    parser.add_argument("--server", default="http://localhost:5000", help="API server URL")
    parser.add_argument("--length", choices=["short", "medium", "long"], default="medium", 
                       help="Summary length")
    parser.add_argument("--format", choices=["paragraph", "bullets", "numbered", "key_points"], 
                       default="bullets", help="Summary format")
    args = parser.parse_args()
    
    # Check if video file exists
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return 1
    
    base_url = args.server
    
    # Step 1: Upload the video
    print(f"\n1. Uploading video: {video_path}")
    with open(video_path, 'rb') as video_file:
        files = {'file': (video_path.name, video_file)}
        upload_response = requests.post(
            f"{base_url}/video/upload",
            files=files
        )
    
    if upload_response.status_code != 200:
        print(f"Error uploading video: {upload_response.status_code}")
        print(upload_response.text)
        return 1
    
    # Get the video ID from the response
    upload_data = upload_response.json()
    video_id = upload_data.get('video_id')
    if not video_id:
        print("Error: No video ID returned from upload")
        return 1
    
    print(f"Video uploaded successfully. Video ID: {video_id}")
    
    # Step 2: Summarize the video
    print(f"\n2. Summarizing video with ID: {video_id}")
    
    summary_options = {
        "length": args.length,
        "format": args.format,
        "focus": ["key_points"],
    }
    
    print(f"Summary options: {json.dumps(summary_options, indent=2)}")
    
    summarize_response = requests.post(
        f"{base_url}/api/summarize/video/{video_id}",
        json=summary_options
    )
    
    if summarize_response.status_code != 200:
        print(f"Error summarizing video: {summarize_response.status_code}")
        print(summarize_response.text)
        return 1
    
    # Get the summarization results
    summarize_data = summarize_response.json()
    
    # Step 3: Display the results
    print("\n==========================================================")
    print("VIDEO SUMMARIZATION RESULTS")
    print("==========================================================")
    
    print("\nVIDEO ID:")
    print(video_id)
    
    print("\nPROCESSING TIME:")
    print(summarize_data.get('processing_time', 'Unknown'))
    
    print("\nTRANSCRIPT:")
    print("----------------------------------------------------------")
    print(summarize_data.get('transcript', 'No transcript available'))
    
    print("\nSUMMARY:")
    print("----------------------------------------------------------")
    print(summarize_data.get('summary', 'No summary available'))
    
    print("\n==========================================================")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 