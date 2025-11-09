#!/bin/bash

# Quick Start Script for AI Product Manager System

echo "🚀 AI Product Manager System - Quick Start"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -q -r requirements.txt

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Please edit .env and add your API keys:"
        echo "   - GOOGLE_API_KEY (required)"
        echo "   - SERPAPI_KEY or EXA_API_KEY (required)"
    else
        echo "❌ No .env.example found. Please create .env manually."
        exit 1
    fi
    exit 0
fi

echo "✅ Environment configured"
echo ""

# Check Node.js for frontend
if command -v node &> /dev/null; then
    echo "✅ Node.js found: $(node --version)"
    
    # Install frontend dependencies if needed
    if [ ! -d "frontend/node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        cd frontend
        npm install
        cd ..
    fi
    echo "✅ Frontend ready"
else
    echo "⚠️  Node.js not found. Frontend will not be available."
    echo "   Install Node.js 18+ to use the web interface."
fi

echo ""
echo "=========================================="
echo "🎉 Setup complete!"
echo ""
echo "To start the system:"
echo ""
echo "  Backend (FastAPI):"
echo "    python backend_api.py"
echo "    → http://localhost:8000"
echo ""
if command -v node &> /dev/null; then
    echo "  Frontend (React):"
    echo "    cd frontend && npm start"
    echo "    → http://localhost:3000"
    echo ""
fi
echo "  CLI Mode:"
echo "    python -m src.pipeline.main --base-dir \"\$(pwd)\" --outputs-dir \"\$(pwd)/outputs\""
echo ""
echo "=========================================="
