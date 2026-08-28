"""
Strelza Telecos Drawing QA Validator — Enterprise Production Server Entrypoint
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from api import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print("=" * 75)
    print(">> STRELZA TELECOS DRAWING QA VALIDATION PLATFORM")
    print(f"Server starting on http://{host}:{port}")
    print("Architecture: 3-Tier Enterprise Structure (Frontend, Backend, DB)")
    print(f"Active LLM Model: {os.getenv('LLM_MODEL', 'gemma4:cloud')}")
    print("=" * 75)
    uvicorn.run("api:app", host=host, port=port, reload=False)
