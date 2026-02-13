#!/bin/bash
#
# Start Witmind Workflow Dashboard
#

echo "🚀 Starting Witmind Workflow Dashboard"
echo ""
echo "   Port: 5000"
echo "   Dashboard: http://localhost:5000"
echo "   API Docs: http://localhost:5000/docs"
echo ""
echo "   Note: Mission Control runs on port 4001 (separate)"
echo ""

cd "$(dirname "$0")/backend"

# Check if venv exists
if [ ! -d "../../.venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    cd ../..
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r workflow-dashboard/backend/requirements.txt
    cd workflow-dashboard/backend
else
    source ../../.venv/bin/activate
fi

# Check dependencies
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start server
echo "✅ Starting server..."
python3 main.py
