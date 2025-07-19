"""Check if OpenAI API key is configured."""
import os
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

print("Checking OpenAI configuration...")
print(f"OPENAI_API_KEY exists: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")

if settings.OPENAI_API_KEY:
    # Show first and last 4 characters for verification
    key = settings.OPENAI_API_KEY
    if len(key) > 8:
        print(f"API Key format: {key[:4]}...{key[-4:]}")
    else:
        print("API Key is too short!")
else:
    print("\n❌ OPENAI_API_KEY is not set!")
    print("Please add it to your .env file:")
    print("OPENAI_API_KEY=sk-...")

# Test OpenAI connection
if settings.OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a basic model for testing
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        print(f"\n✅ OpenAI API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"\n❌ OpenAI API error: {str(e)}")
        print("Please check your API key is valid and has sufficient credits.")