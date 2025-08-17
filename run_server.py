#!/usr/bin/env python3
"""
Simple script to run the Content Moderation Service
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Set default port
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting Content Moderation Service...")
    print(f"📡 Server will be available at: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"🔍 Health Check: http://localhost:{port}/api/v1/health")
    print()
    print("⚠️  Make sure you have set GOOGLE_API_KEY in your .env file")
    print("   or as an environment variable")
    print()
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
