#!/bin/bash
#
# Quick run script for Workflow Dashboard
#

echo ""
echo "🚀 Starting Witmind Workflow Dashboard..."
echo ""
echo "   Dashboard: http://localhost:5000"
echo "   API Docs:  http://localhost:5000/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")/backend"

# Activate venv
if [ -f "../../.venv/bin/activate" ]; then
    source ../../.venv/bin/activate
fi

# Start server
exec python3 main.py
