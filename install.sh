#!/bin/bash

# AI Cycling Coach Installation Script

set -e

echo "🚴 AI Cycling Coach Installation"
echo "================================="

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install the application
echo "📋 Installing AI Cycling Coach..."
pip install -e .

# Initialize database
echo "🗄️ Initializing database..."
make init-db

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the app: cycling-coach"
echo ""
echo "Or use the Makefile:"
echo "  make run"
echo ""
echo "Configure your settings in .env file:"
echo "  - OPENROUTER_API_KEY: Your AI API key"
echo "  - GARMIN_USERNAME: Your Garmin Connect username"  
echo "  - GARMIN_PASSWORD: Your Garmin Connect password"
echo ""
echo "Happy training! 🚴‍♂️"