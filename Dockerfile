FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV FLASK_APP=backend.app.main
ENV FLASK_ENV=production
ENV PORT=8081

# Expose the port
EXPOSE 8081

# Command to run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8081"] 