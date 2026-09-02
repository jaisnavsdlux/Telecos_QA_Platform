#!/bin/bash
echo "==============================================================================="
echo "  STRELZA TELECOS QA PLATFORM - PHASE 1"
echo "  AI-Powered Multi-Modal Telecom Compliance Audit Suite"
echo "==============================================================================="
echo ""
echo "[1/2] Verifying Python runtime and dependencies..."
pip install -q --no-warn-conflicts -r requirements.txt
echo "[2/2] Launching Application Server..."
echo ""
python3 run_app.py
