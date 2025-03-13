import requests
import time
import argparse
import json

def test_rate_limiting(base_url):
    """Test the rate limiting functionality"""
    print("\n=== Testing Rate Limiting ===")
    
    # Test login endpoint rate limiting
    print("\nTesting login endpoint rate limiting (5 per minute)...")
    for i in range(7):  # Try 7 requests (should hit limit)
        response = requests.get(f"{base_url}/auth/login")
        print(f"Request {i+1}: Status code {response.status_code}")
        
        if response.status_code == 429:
            print("✅ Rate limiting is working correctly!")
            break
        
        if i == 6:
            print("❌ Rate limiting did not trigger as expected")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Wait to reset rate limit
    print("\nWaiting 10 seconds for rate limit to reset...")
    time.sleep(10)
    
    # Test API endpoint rate limiting
    print("\nTesting API endpoint rate limiting...")
    for i in range(12):  # Try 12 requests (should hit limit)
        response = requests.get(f"{base_url}/auth/user")
        print(f"Request {i+1}: Status code {response.status_code}")
        
        if response.status_code == 429:
            print("✅ API rate limiting is working correctly!")
            break
        
        if i == 11:
            print("❌ API rate limiting did not trigger as expected")
        
        time.sleep(0.5)  # Small delay between requests

def test_session_expiry(base_url):
    """Test the session expiry functionality"""
    print("\n=== Testing Session Expiry ===")
    
    # Note: This test requires manual login since we can't programmatically complete Google OAuth
    print("\nPlease login manually by visiting:")
    print(f"{base_url}/auth/login")
    input("Press Enter once you've logged in...")
    
    # Test if we can access a protected endpoint
    response = requests.get(f"{base_url}/auth/user")
    if response.status_code == 200:
        print("✅ Successfully authenticated")
        print(f"User info: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    # Wait for session to expire
    expiry_minutes = 30  # Should match the expiry time in the app
    print(f"\nWaiting for session to expire (this would normally take {expiry_minutes} minutes)...")
    print("For testing purposes, you can manually set a short expiry time in the app.")
    
    # For testing, you might want to set a shorter expiry time in the app during development
    input("Press Enter once you're ready to check if the session has expired...")
    
    # Check if session has expired
    response = requests.get(f"{base_url}/auth/user")
    if response.status_code == 401:
        print("✅ Session expired correctly")
    else:
        print(f"❌ Session did not expire as expected: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="Test security features")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL of the API")
    parser.add_argument("--test", choices=["rate-limiting", "session-expiry", "all"], default="all", help="Test to run")
    args = parser.parse_args()
    
    if args.test == "rate-limiting" or args.test == "all":
        test_rate_limiting(args.base_url)
    
    if args.test == "session-expiry" or args.test == "all":
        test_session_expiry(args.base_url)

if __name__ == "__main__":
    main() 