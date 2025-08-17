#!/usr/bin/env python3
"""
Test script for Gemini API integration
This script tests the Gemini service functionality
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gemini_service():
    """Test Gemini service functionality"""
    print("🧪 Testing Gemini Service Integration...")
    
    try:
        # Import the service
        from app.services.gemini_service import GeminiService
        
        # Check if API key is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key or api_key == 'your_google_api_key_here':
            print("❌ GOOGLE_API_KEY not set. Please set it in your .env file")
            return False
        
        print("✅ GOOGLE_API_KEY is configured")
        
        # Create service instance
        service = GeminiService()
        print("✅ GeminiService instance created")
        
        # Test text analysis
        print("\n📝 Testing text analysis...")
        test_text = "Hello world, this is a test message for content moderation."
        
        classification, confidence, reasoning, llm_response = await service.analyze_text_content(test_text)
        
        print(f"✅ Text analysis completed:")
        print(f"   - Classification: {classification}")
        print(f"   - Confidence: {confidence}")
        print(f"   - Reasoning: {reasoning}")
        print(f"   - Response length: {len(llm_response)} characters")
        
        # Test content hash generation
        print("\n🔐 Testing content hash generation...")
        hash1 = service.get_content_hash(test_text)
        hash2 = service.get_content_hash(test_text)
        
        if hash1 == hash2:
            print("✅ Content hashing works correctly (deterministic)")
        else:
            print("❌ Content hashing failed (non-deterministic)")
            return False
        
        print(f"   - Hash: {hash1[:16]}...")
        
        print("\n🎉 All Gemini service tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("Gemini API Integration Test")
    print("=" * 60)
    
    success = await test_gemini_service()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Gemini integration is working.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
