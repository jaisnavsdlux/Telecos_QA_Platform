@echo off
title Strelza Telecos QA Platform - Phase 1
echo ===============================================================================
echo   STRELZA TELECOS QA PLATFORM - PHASE 1
echo   AI-Powered Multi-Modal Telecom Compliance Audit Suite
echo ===============================================================================
echo.
echo [1/2] Verifying Python runtime and dependencies...
python -m pip install -q --no-warn-conflicts -r requirements.txt
echo [2/2] Launching Application Server...
echo.
python run_app.py
pause
