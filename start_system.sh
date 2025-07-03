#!/bin/bash
echo "============================================================"
echo "🚀 Starting A2A Multi-Agent Flight Management System..."

# Clean up any existing processes on the required ports (uncomment if needed)
# echo "🧹 Cleaning up existing processes on ports 9990-9993..."
# for port in 9990 9991 9992 9993; do
#     lsof -ti:$port | xargs kill -9 2>/dev/null || echo "  ✓ Port $port is free"
# done
# echo ""

# Obtener el directorio base del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📍 Base directory: $SCRIPT_DIR"

echo "📡 Starting Employee Flight Request Agent (Port 9992)..."
(cd "$SCRIPT_DIR/employee_flight_request_agent" && uv run . --host 0.0.0.0) &
EMPLOYEE_PID=$!

echo "🏢 Starting Airport Knowledge Base Agent (Port 9991)..."
(cd "$SCRIPT_DIR/airport_knowledge_base_agent" && uv run . --host 0.0.0.0) &
AIRPORT_PID=$!

echo "✈️  Starting Flight Search Agent (Port 9993)..."
(cd "$SCRIPT_DIR/flight_search_agent" && uv run . --host 0.0.0.0) &
FLIGHT_PID=$!

echo ""
echo "⏳ Waiting 5 seconds for all agents to initialize..."
sleep 5

echo "💬 Starting Chat Agent (Port 9990)..."
echo "============================================================"
cd "$SCRIPT_DIR" && uv run python chat_agent.py

# Cleanup function cuando se termine el chat
cleanup() {
    echo ""
    echo "🛑 Shutting down all agents..."
    kill $EMPLOYEE_PID $AIRPORT_PID $FLIGHT_PID 2>/dev/null
    echo "👋 All agents stopped. Goodbye!"
}

trap cleanup EXIT 