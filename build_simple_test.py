#!/usr/bin/env python3
"""
Very simple build test.
"""

import subprocess
import sys


def build_simple():
    """Build with minimal options."""
    print("Building simple test...")

    cmd = ["pyinstaller", "--onefile", "--name=SimpleTest", "test_minimal_exe.py"]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Simple build successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Simple build failed: {e}")
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


if __name__ == "__main__":
    if build_simple():
        print("\n✅ Simple build successful!")
        print("Test it with: .\\dist\\SimpleTest.exe")
    else:
        print("\n❌ Simple build failed!")
        sys.exit(1)
