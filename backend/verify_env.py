#!/usr/bin/env python3
"""
Verify OPENAI_API_KEY is accessible from .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

print("=" * 60)
print("Environment Variable Verification")
print("=" * 60)

# Check current working directory
print(f"\nCurrent directory: {os.getcwd()}")

# Check if .env exists
env_file = Path(__file__).parent / ".env"
print(f".env file path: {env_file}")
print(f".env exists: {env_file.exists()}")

if env_file.exists():
    print(f".env size: {env_file.stat().st_size} bytes")

# Check shell environment BEFORE loading .env
shell_key = os.getenv("OPENAI_API_KEY")
if shell_key:
    print(f"\n✓ OPENAI_API_KEY found in shell environment")
    print(f"  Shell key: {shell_key[:20]}...{shell_key[-4:]}")
else:
    print(f"\n  No OPENAI_API_KEY in shell environment")

# Load .env
print("\nLoading .env...")
load_dotenv()

# Check OPENAI_API_KEY after loading .env
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"✓ SUCCESS: OPENAI_API_KEY loaded")
    print(f"  Key prefix: {api_key[:20]}...")
    print(f"  Key suffix: ...{api_key[-4:]}")
    print(f"  Key length: {len(api_key)} characters")
    
    # Verify it's a valid OpenAI key format
    if api_key.startswith("sk-"):
        print(f"  Format: ✓ Valid OpenAI key format")
    else:
        print(f"  Format: ✗ WARNING - Does not start with 'sk-'")
else:
    print("✗ FAILURE: OPENAI_API_KEY not found in environment")
    print("\nDebugging info:")
    print(f"  All env vars starting with 'OPENAI': {[k for k in os.environ.keys() if 'OPENAI' in k]}")

print("\n" + "=" * 60)
print("Verification complete")
print("=" * 60)
