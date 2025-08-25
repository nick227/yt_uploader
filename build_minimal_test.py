#!/usr/bin/env python3
"""
Minimal build script for testing EXE packaging.
"""

import subprocess
import sys
from pathlib import Path


def build_minimal_exe():
    """Build a minimal test EXE."""
    print("Building minimal test EXE...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=TestExe",
        "test_minimal_exe.py",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Minimal EXE build successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Minimal EXE build failed: {e}")
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


if __name__ == "__main__":
    if build_minimal_exe():
        print("\n✅ Minimal EXE built successfully!")
        print("Test it with: .\\dist\\TestExe.exe")
    else:
        print("\n❌ Minimal EXE build failed!")
        sys.exit(1)
