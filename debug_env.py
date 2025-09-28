#!/usr/bin/env python3
"""
Debug script to check environment variables and API connections
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 DEBUGGING ENVIRONMENT VARIABLES")
print("=" * 50)

# Check if .env is loaded
print(f"DEFAULT_AI_PROVIDER: {os.getenv('DEFAULT_AI_PROVIDER', 'NOT SET')}")
print(f"GROQ_API_KEY: {'✅ SET' if os.getenv('GROQ_API_KEY') else '❌ NOT SET'}")
print(f"OPENAI_API_KEY: {'✅ SET' if os.getenv('OPENAI_API_KEY') else '❌ NOT SET'}")
print(f"ANTHROPIC_API_KEY: {'✅ SET' if os.getenv('ANTHROPIC_API_KEY') else '❌ NOT SET'}")

print("\n🧪 TESTING GROQ CONNECTION")
print("=" * 50)

try:
    from groq import Groq
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ No Groq API key found")
    else:
        print(f"✅ Groq API key found: {api_key[:10]}...")
        
        # Test connection
        client = Groq(api_key=api_key)
        
        # Try a simple API call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated model
            messages=[
                {"role": "system", "content": "You are a test AI. Respond with exactly: 'CONNECTION_SUCCESS'"},
                {"role": "user", "content": "Test"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        if "CONNECTION_SUCCESS" in result:
            print("✅ Groq API connection successful!")
        else:
            print(f"⚠️  Groq API responded but with unexpected result: {result}")
            
except ImportError:
    print("❌ Groq library not installed. Run: pip install groq")
except Exception as e:
    print(f"❌ Groq API connection failed: {e}")

print("\n📋 NEXT STEPS:")
print("=" * 50)

if not os.getenv("GROQ_API_KEY"):
    print("1. Get Groq API key from: https://console.groq.com/")
    print("2. Add to .env file: GROQ_API_KEY=your_key_here")
    print("3. Set DEFAULT_AI_PROVIDER=groq in .env")
else:
    print("✅ Configuration looks good!")
    print("The game should work with Groq now.")
