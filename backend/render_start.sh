#!/bin/bash
# Render startup script for AI Campus Companion

# Set the port environment variable that Render provides
export PORT=${PORT:-8002}

# Run the backend
echo "Starting AI Campus Companion on port $PORT..."
python run_backend.py
