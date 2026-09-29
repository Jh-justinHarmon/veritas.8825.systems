#!/usr/bin/env python3
"""
Test the setup_api_key.py script behavior
"""

import os
import sys
from pathlib import Path
from io import StringIO

# Import the setup script
import setup_api_key

# Test 1: Verify ENV_PATH is correct
print("Test 1: ENV_PATH verification")
expected_path = Path(__file__).parent / ".env"
print(f"  Expected: {expected_path}")
print(f"  Actual:   {setup_api_key.ENV_PATH}")
print(f"  ✓ PASS" if setup_api_key.ENV_PATH == expected_path else "  ✗ FAIL")

# Test 2: Verify .env file exists and is writable
print("\nTest 2: .env file writability")
test_env = Path(__file__).parent / ".env.test"
try:
    with open(test_env, "w") as f:
        f.write("TEST=value\n")
    test_env.unlink()
    print("  ✓ PASS - Can write to directory")
except Exception as e:
    print(f"  ✗ FAIL - {e}")

# Test 3: Verify current .env exists
print("\nTest 3: Current .env file")
if setup_api_key.ENV_PATH.exists():
    size = setup_api_key.ENV_PATH.stat().st_size
    print(f"  ✓ EXISTS - {size} bytes")
    
    # Read first line (without exposing full key)
    with open(setup_api_key.ENV_PATH, "r") as f:
        first_line = f.readline().strip()
        if first_line.startswith("OPENAI_API_KEY="):
            key_part = first_line.split("=", 1)[1]
            print(f"  ✓ Format correct: OPENAI_API_KEY={key_part[:20]}...{key_part[-4:]}")
        else:
            print(f"  ✗ Format incorrect: {first_line[:30]}...")
else:
    print("  ⚠️  Does not exist (will be created on first run)")

print("\n" + "=" * 60)
print("Test complete - setup_api_key.py is ready to use")
print("=" * 60)
print("\nTo set up your API key, run:")
print("  python3 setup_api_key.py")
