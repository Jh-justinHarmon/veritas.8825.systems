#!/usr/bin/env python3
"""
Test OpenAI API authentication
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

print("=" * 60)
print("OpenAI API Authentication Test")
print("=" * 60)

# Load environment with override to use .env file instead of shell
env_path = Path(__file__).parent / ".env"
print(f"Loading from: {env_path}")
load_dotenv(env_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("✗ FAILURE: No OPENAI_API_KEY found")
    exit(1)

print(f"\n✓ API Key loaded: {api_key[:20]}...{api_key[-4:]}")

# Initialize client
print("\nInitializing OpenAI client...")
client = OpenAI(api_key=api_key)

# Test API call
print("Making test API call (embedding)...")
try:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="test"
    )
    
    embedding = response.data[0].embedding
    print(f"✓ SUCCESS: API call succeeded")
    print(f"  Embedding dimensions: {len(embedding)}")
    print(f"  Model: {response.model}")
    print(f"  Usage: {response.usage.total_tokens} tokens")
    
except Exception as e:
    print(f"✗ FAILURE: API call failed")
    print(f"  Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Authentication test PASSED")
print("=" * 60)
