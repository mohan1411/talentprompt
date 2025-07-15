#!/usr/bin/env python3
"""Check OpenAI configuration in Railway environment."""

import os
from app.core.config import settings

print("=== OpenAI Configuration Check ===")
print(f"OPENAI_API_KEY set: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
if settings.OPENAI_API_KEY:
    print(f"API Key length: {len(settings.OPENAI_API_KEY)}")
    print(f"API Key preview: {settings.OPENAI_API_KEY[:8]}...")
print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")

# Check environment directly
env_key = os.environ.get('OPENAI_API_KEY')
print(f"\nDirect env check:")
print(f"OPENAI_API_KEY in env: {'Yes' if env_key else 'No'}")

if not settings.OPENAI_API_KEY:
    print("\n⚠️  WARNING: OPENAI_API_KEY is not set!")
    print("AI-powered LinkedIn parsing will NOT work.")
    print("To enable it, set OPENAI_API_KEY in Railway environment variables.")
else:
    print("\n✅ OpenAI is configured correctly!")
    print("AI-powered LinkedIn parsing should work.")