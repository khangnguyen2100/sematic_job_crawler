#!/bin/bash

# Marqo Learning Project Setup Script

echo "🚀 Marqo Learning Project Setup"
echo "================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ All prerequisites found!"

# Start Marqo server
echo ""
echo "🐳 Starting Marqo server..."
docker-compose up -d

# Wait for Marqo to be ready
echo "⏳ Waiting for Marqo to be ready..."
sleep 10

# Check if Marqo is responding
if curl -s http://localhost:8882 > /dev/null; then
    echo "✅ Marqo server is running!"
else
    echo "❌ Marqo server is not responding. Please check Docker logs."
    echo "   Run: docker-compose logs marqo"
    exit 1
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if command_exists pip3; then
    pip3 install -r requirements.txt
elif command_exists pip; then
    pip install -r requirements.txt
else
    echo "❌ pip is not available. Please install pip first."
    exit 1
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🔥 Ready to run demos:"
echo "   Basic demo:    python3 src/main.py"
echo "   Advanced demo: python3 src/advanced_demo.py"
echo ""
echo "🛑 To stop Marqo server:"
echo "   docker-compose down"
