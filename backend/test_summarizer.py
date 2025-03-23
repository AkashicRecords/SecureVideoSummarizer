import requests
import os
import time
import argparse

def test_summarization(base_url, video_path):
    """Test the video summarization functionality"""
    print(f"Testing video summarization with {video_path}")
    
    # Step 1: Upload the video
    print("\n1. Uploading video...")
    with open(video_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{base_url}/video/upload", files=files)
    
    if response.status_code != 200:
        print(f"Error uploading video: {response.text}")
        return
    
    video_id = response.json()['video_id']
    print(f"Video uploaded successfully. Video ID: {video_id}")
    
    # Step 2: Request summarization
    print("\n2. Requesting summarization...")
    options = {
        "options": {
            "format": "bullets",
            "length": "medium",
            "focus": ["key_points"]
        }
    }
    response = requests.post(f"{base_url}/summarizer/summarize/{video_id}", json=options)
    
    if response.status_code != 200:
        print(f"Error requesting summarization: {response.text}")
        return
    
    summary_id = response.json()['summary_id']
    print(f"Summarization requested successfully. Summary ID: {summary_id}")
    
    # Step 3: Wait for summarization to complete (in a real app, this would be async)
    print("\n3. Waiting for summarization to complete...")
    time.sleep(5)  # Simple wait, in a real app you'd poll or use websockets
    
    # Step 4: Retrieve the summary
    print("\n4. Retrieving summary...")
    response = requests.get(f"{base_url}/summarizer/summary/{summary_id}")
    
    if response.status_code != 200:
        print(f"Error retrieving summary: {response.text}")
        return
    
    summary = response.json()
    print("\nSummary:")
    print(f"Video ID: {summary['video_id']}")
    print(f"Created at: {summary['created_at']}")
    print(f"Options: {summary['options']}")
    print("\nTranscript (first 200 chars):")
    print(f"{summary['transcript'][:200]}...")
    print("\nSummary content:")
    print(summary['content'])
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test the video summarization functionality')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of the API')
    parser.add_argument('--video', required=True, help='Path to the video file to test with')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        print(f"Error: Video file not found at {args.video}")
        exit(1)
    
    test_summarization(args.url, args.video) 