#!/bin/bash

# Create necessary directories
mkdir -p uploads/videos
mkdir -p uploads/temp
mkdir -p summaries
mkdir -p logs
mkdir -p sessions

# Create .env file
cat > .env << 'EOF'
# SecureVideoSummarizer Environment Configuration
FLASK_APP=app.main
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-for-testing-only
SESSION_TYPE=filesystem
SESSION_FILE_DIR=sessions
VIDEOS_DIR=uploads/videos
TEMP_DIR=uploads/temp
SUMMARIES_DIR=summaries
LOGS_DIR=logs
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=mp4,avi,mov,wmv,flv,mkv
MAX_CONTENT_LENGTH=100000000
GOOGLE_CLIENT_ID=dummy-client-id
GOOGLE_CLIENT_SECRET=dummy-client-secret
OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback
ALLOWED_ORIGINS=http://localhost:3000
RATE_LIMIT_DEFAULT=200 per day, 50 per hour
RATE_LIMIT_AUTH=10 per minute
BYPASS_AUTH_FOR_TESTING=true
EOF

echo "Test environment setup complete. Created .env file and necessary directories." 