#!/usr/bin/env python3
"""
Test backend during Playwright run to see if requests arrive.
"""
import subprocess
import time
import sys

def monitor_backend():
    """Start backend and monitor for incoming requests."""
    print("Starting backend with request logging...")
    proc = subprocess.Popen(
        ["python3", "app.py"],
        cwd="/Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin Harmon/AI_SYSTEMS/8825-modules/Veritas/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("Backend started. Monitoring requests...")
    print("=" * 60)
    
    try:
        for line in proc.stdout:
            print(line, end='')
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nStopping backend...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    monitor_backend()
