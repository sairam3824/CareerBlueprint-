#!/bin/bash

# AI Job Recommendation Bot - Quick Start Script

echo "🤖 AI Job Recommendation Bot"
echo "=============================="
echo ""

# Check if conda environment exists
if conda env list | grep -q "jobbot"; then
    echo "✅ Conda environment 'jobbot' found"
else
    echo "📦 Creating conda environment..."
    conda create -n jobbot python=3.9 -y
fi

# Activate environment
echo "🔄 Activating environment..."
eval "$(conda shell.bash hook)"
conda activate jobbot

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys before running the server"
    exit 1
fi

# Create necessary directories
mkdir -p data logs data/cache

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the backend server:"
echo "  python app.py"
echo ""
echo "To start the frontend (in a new terminal):"
echo "  cd frontend && python -m http.server 8000"
echo ""
echo "Then visit: http://localhost:8000"
echo ""
