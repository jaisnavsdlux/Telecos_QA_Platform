#!/usr/bin/env python3
"""
===============================================================================
  STRELZA TELECOS QA PLATFORM — PHASE 1 MASTER APPLICATION RUNNER
  AI-Powered Multi-Modal Telecom Compliance Audit Suite
===============================================================================
"""
import sys
import os
import getpass
from pathlib import Path
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "backend"))
sys.path.insert(0, CURRENT_DIR)

# Load existing .env if present
env_path = os.path.join(CURRENT_DIR, ".env")
load_dotenv(env_path)

def setup_api_keys():
    """Interactive first-time setup assistant for Claude API credentials."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", os.getenv("CLAUDE_API_KEY", "")).strip()
    
    if not anthropic_key:
        print("\n" + "=" * 75)
        print("  🔑 CLAUDE API CREDENTIAL SETUP ASSISTANT")
        print("=" * 75)
        print("  To perform AI-powered CAD drawing compliance audits, the platform")
        print("  requires an Anthropic Claude API Key.")
        print("=" * 75)
        
        try:
            if sys.stdin.isatty():
                entered_key = input("\n👉 Enter your Anthropic Claude API Key (or press Enter to skip): ").strip()
                if entered_key:
                    os.environ["ANTHROPIC_API_KEY"] = entered_key
                    # Save to .env for persistence
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\nANTHROPIC_API_KEY={entered_key}\nLLM_MODEL=claude-opus-5\n")
                    print("  [OK] Saved Claude API Key to .env file.")
                else:
                    print("  [Notice] Running without Anthropic API key. Add ANTHROPIC_API_KEY to .env anytime.")
        except Exception:
            pass

def main():
    print("\n" + "=" * 75)
    print("🚀 STRELZA TELECOS QA PLATFORM — PHASE 1")
    print("  Enterprise Telecom Compliance & For-Construction Drawing Audit Suite")
    print("=" * 75)
    
    setup_api_keys()
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n  Starting Application Server...")
    print(f"  ➜ Web Interface: http://localhost:{port}/static/index.html")
    print(f"  ➜ Dashboard:     http://localhost:{port}/static/dashboard.html")
    print(f"  ➜ API Docs:      http://localhost:{port}/docs")
    print("=" * 75 + "\n")
    
    import uvicorn
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
