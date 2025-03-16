#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Get the absolute path to the .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
print(f"Loading environment variables from: {env_path}")

# Explicitly load the .env file
load_dotenv(dotenv_path=env_path, override=True)

# Print Ollama-related environment variables
print("\nOllama-related environment variables:")
print(f"OLLAMA_API_URL: {os.environ.get('OLLAMA_API_URL', 'Not set')}")
print(f"OLLAMA_MODEL: {os.environ.get('OLLAMA_MODEL', 'Not set')}")
print(f"OLLAMA_TIMEOUT: {os.environ.get('OLLAMA_TIMEOUT', 'Not set')}")
print(f"OLLAMA_MAX_TOKENS: {os.environ.get('OLLAMA_MAX_TOKENS', 'Not set')}")
print(f"OLLAMA_CONTEXT_SIZE: {os.environ.get('OLLAMA_CONTEXT_SIZE', 'Not set')}")

# Try to parse the timeout value
print("\nTrying to parse OLLAMA_TIMEOUT as an integer:")
try:
    timeout_str = os.environ.get('OLLAMA_TIMEOUT', '60')
    timeout_int = int(timeout_str)
    print(f"Successfully parsed OLLAMA_TIMEOUT: {timeout_int}")
except ValueError as e:
    print(f"Error parsing OLLAMA_TIMEOUT: {e}")
    print(f"Raw value: '{timeout_str}'")

# Try reading the .env file directly
print("\nReading .env file directly:")
try:
    with open(env_path, 'r') as f:
        content = f.read()
        print("File content:")
        print(content)
except Exception as e:
    print(f"Error reading .env file: {e}")

print("\nDone.") 