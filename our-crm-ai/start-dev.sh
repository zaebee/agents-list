#!/bin/bash
set -e

echo "🚀 Starting AI-CRM Development Server..."

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the FastAPI application
uvicorn api:app --host 0.0.0.0 --port 5001 --reload
