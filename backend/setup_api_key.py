#!/usr/bin/env python3
"""
Veritas API Key Setup

Simple script to prompt for OpenAI API key and save to .env file.
Replicates v4 behavior: prompt → paste → save → done.
"""

import os
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"

def main():
    print("=" * 60)
    print("Veritas API Key Setup")
    print("=" * 60)
    print("\nPaste your OPENAI_API_KEY and press Enter:")
    
    api_key = input("> ").strip()

    if not api_key:
        print("\n✗ No key provided. Exiting.")
        return

    # Validate basic format
    if not api_key.startswith("sk-"):
        print("\n⚠️  WARNING: Key doesn't start with 'sk-'")
        print("   This may not be a valid OpenAI API key.")
        confirm = input("   Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("\n✗ Cancelled. No changes made.")
            return

    # Write to .env
    content = f"OPENAI_API_KEY={api_key}\n"

    try:
        with open(ENV_PATH, "w") as f:
            f.write(content)
        
        print(f"\n✓ Saved to {ENV_PATH}")
        print("✓ Done.")
        print("\nYou can now run the Veritas backend:")
        print("  python3 app.py")
        
    except Exception as e:
        print(f"\n✗ Error saving .env file: {e}")
        return

if __name__ == "__main__":
    main()
