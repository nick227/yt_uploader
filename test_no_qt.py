#!/usr/bin/env python3
"""
Simple test without Qt.
"""

import sys
import time


def main():
    print("Hello from EXE!")
    print("This is a test without Qt.")
    print("If you see this, PyInstaller is working.")

    # Wait a bit so we can see the output
    time.sleep(2)

    print("Test completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
