#!/bin/bash

# VocalBridge Ops - Frontend Setup and Run Script

set -e

echo "============================================================"
echo "VOCALBRIDGE OPS - FRONTEND SETUP"
echo "============================================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✓ Node.js $(node --version) detected"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "============================================================"
echo "✅ FRONTEND SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Starting development server..."
echo "Frontend will be available at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start dev server
npm run dev
