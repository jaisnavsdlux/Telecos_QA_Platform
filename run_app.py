#!/usr/bin/env python3
"""
===============================================================================
  STRELZA TELECOS QA PLATFORM — PHASE 1 MASTER APPLICATION RUNNER
  AI-Powered Multi-Modal Telecom Compliance Audit Suite (72 Rules)
===============================================================================
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, "backend"))
sys.path.insert(0, CURRENT_DIR)

# Load existing .env if present
env_path = os.path.join(CURRENT_DIR, ".env")
load_dotenv(env_path)

def setup_api_keys():
    """Interactive first-time / update assistant for Claude API credentials."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", os.getenv("CLAUDE_API_KEY", "")).strip()
    
    print("\n" + "=" * 75)
    print("  🔑 CLAUDE API CREDENTIAL SETUP ASSISTANT")
    print("=" * 75)
    
    try:
        if sys.stdin.isatty():
            if anthropic_key:
                masked = anthropic_key[:7] + "..." + anthropic_key[-4:] if len(anthropic_key) > 12 else "***"
                print(f"  [OK] Current Claude API Key configured: {masked}")
                entered_key = input("  ➜ Press [ENTER] to keep current key, or paste new API key to update: ").strip()
                if entered_key:
                    os.environ["ANTHROPIC_API_KEY"] = entered_key
                    # Update .env
                    lines = []
                    if os.path.exists(env_path):
                        with open(env_path, "r", encoding="utf-8") as f:
                            lines = [l for l in f.readlines() if not l.startswith("ANTHROPIC_API_KEY=")]
                    lines.append(f"ANTHROPIC_API_KEY={entered_key}\n")
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    print("  [OK] Successfully updated Claude API Key in .env file.")
                else:
                    print("  [OK] Continuing with active Claude API credentials.")
            else:
                print("  To perform AI-powered CAD drawing compliance audits across all 72 rules,")
                print("  the platform requires an Anthropic Claude API Key.")
                entered_key = input("\n👉 Enter your Anthropic Claude API Key (e.g. sk-ant-...): ").strip()
                if entered_key:
                    os.environ["ANTHROPIC_API_KEY"] = entered_key
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\nANTHROPIC_API_KEY={entered_key}\nLLM_MODEL=claude-opus-5\n")
                    print("  [OK] Saved Claude API Key to .env file.")
                else:
                    print("  [Notice] Running in evaluation mode. You can set ANTHROPIC_API_KEY in .env anytime.")
    except Exception:
        pass
    print("=" * 75)

def main():
    print("\n" + "=" * 75)
    print("🚀 STRELZA TELECOS QA PLATFORM — PHASE 1")
    print("  Enterprise Telecom Compliance & For-Construction Drawing Audit Suite")
    print("  72-Rule Optus BA Engineering Verification Suite")
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
