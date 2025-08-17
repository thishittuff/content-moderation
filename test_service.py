#!/usr/bin/env python3
"""
Simple test script for Content Moderation Service
This script tests basic functionality without external dependencies
"""

import asyncio
import json
from datetime import datetime
from app.schemas import TextModerationRequest, ImageModerationRequest
from app.models import ContentType, ModerationStatus, ContentClassification

def test_schemas():
    """Test Pydantic schemas"""
    print("Testing Pydantic schemas...")
    
    # Test text moderation request
    try:
        text_request = TextModerationRequest(
            email_id="angadsinghthethi@gmail.com",
            text_content="Hello world, this is a test message."
        )
        print(f"✓ Text moderation request created: {text_request.email_id}")
    except Exception as e:
        print(f"✗ Text moderation request failed: {e}")
    
    # Test image moderation request
    try:
        image_request = ImageModerationRequest(
            email_id="angadsinghthethi@gmail.com",
            image_data="base64_encoded_image_data_here"
        )
        print(f"✓ Image moderation request created: {image_request.email_id}")
    except Exception as e:
        print(f"✗ Image moderation request failed: {e}")
    
    print()

def test_models():
    """Test SQLAlchemy models"""
    print("Testing SQLAlchemy models...")
    
    # Test enums
    try:
        content_types = [ContentType.TEXT, ContentType.IMAGE]
        statuses = [ModerationStatus.PENDING, ModerationStatus.PROCESSING, ModerationStatus.COMPLETED]
        classifications = [ContentClassification.SAFE, ContentClassification.TOXIC, ContentClassification.SPAM]
        
        print(f"✓ Content types: {[ct.value for ct in content_types]}")
        print(f"✓ Statuses: {[s.value for s in statuses]}")
        print(f"✓ Classifications: {[c.value for c in classifications]}")
    except Exception as e:
        print(f"✗ Model enums failed: {e}")
    
    print()

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        from app.config import settings
        print(f"✓ Configuration loaded successfully")
        print(f"  - Gemini model: {settings.gemini_model}")
        print(f"  - Database URL: {settings.database_url[:50]}...")
        print(f"  - Redis URL: {settings.redis_url}")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
    
    print()

def test_imports():
    """Test all module imports"""
    print("Testing module imports...")
    
    modules = [
        "app.database",
        "app.services.gemini_service",
        "app.services.notification_service", 
        "app.services.sentry_service",
        "app.services.moderation_service",
        "app.api.v1.endpoints"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
    
    print()

def main():
    """Run all tests"""
    print("=" * 50)
    print("Content Moderation Service - Test Suite")
    print("=" * 50)
    print()
    
    test_imports()
    test_schemas()
    test_models()
    test_config()
    
    print("=" * 50)
    print("Test suite completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
