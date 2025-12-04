#!/bin/bash

# Run Streamlit app for AWS Migration Assistant

echo "🚀 Starting AWS Migration Assistant..."
echo ""

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit pillow
fi

# Run the app
echo "🌐 Starting Streamlit server..."
echo "📍 Open browser at: http://localhost:8501"
echo ""
streamlit run streamlit_app.py
