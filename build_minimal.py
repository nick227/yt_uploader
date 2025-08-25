#!/usr/bin/env python3
"""
Minimal build script for creating the smallest possible EXE file.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        return False


def force_clean():
    """Force clean all build artifacts."""
    print("🧹 Force cleaning all build artifacts...")

    # Kill any running PyInstaller processes
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "pyinstaller.exe"],
            capture_output=True,
            check=False,
        )
        time.sleep(2)
    except:
        pass

    # Remove directories
    for path in ["dist", "build"]:
        if Path(path).exists():
            try:
                shutil.rmtree(path)
                print(f"✓ Removed {path}/")
            except:
                print(f"⚠️  Could not remove {path}/")

    # Remove spec files
    for spec in Path(".").glob("*.spec"):
        try:
            spec.unlink()
            print(f"✓ Removed {spec}")
        except:
            print(f"⚠️  Could not remove {spec}")


def create_icon():
    """Create a simple icon file if it doesn't exist."""
    icon_path = Path("assets/icon.ico")

    if icon_path.exists():
        return str(icon_path)

    icon_path.parent.mkdir(exist_ok=True)

    with open(icon_path, "wb") as f:
        f.write(
            b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x00\x00\x00\x00\x16\x00\x00\x00\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    return str(icon_path)


def build_minimal_exe():
    """Build the smallest possible EXE file."""
    print("🚀 Starting minimal Media Uploader EXE build...")
    print("📊 Target size: ~70-80 MB")

    # Force clean everything
    force_clean()

    # Create icon
    icon_path = create_icon()

    # Build with aggressive exclusions
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        "--name=MediaUploader",
        "--exclude=PyQt6",
        "--exclude=PyQt5",
        "--exclude=matplotlib",
        "--exclude=pytest",
        "--exclude=IPython",
        "--exclude=jupyter",
        "--exclude=notebook",
        "--exclude=sphinx",
        "--exclude=docutils",
        "--exclude=black",
        "--exclude=flake8",
        "--exclude=mypy",
        "--exclude=isort",
        "--exclude=pre-commit",
        "--exclude=tox",
        "--exclude=tkinter",
        "--exclude=tk",
        "--exclude=wx",
        "--exclude=PyQt4",
        "--exclude=PySide2",
        "--exclude=PySide5",
        "--exclude=IPython",
        "--exclude=jupyter",
        "--exclude=notebook",
        "--exclude=sphinx",
        "--exclude=docutils",
        "--exclude=setuptools",
        "--exclude=pip",
        "--exclude=wheel",
        "--exclude=distutils",
        "--exclude=email",
        "--exclude=html",
        "--exclude=http",
        "--exclude=urllib",
        "--exclude=xml",
        "--exclude=pydoc",
        "--exclude=doctest",
        "--exclude=unittest",
        "--exclude=test",
        "--exclude=tests",
        "--exclude=testing",
        "--exclude=debug",
        "--exclude=profile",
        "--exclude=tracemalloc",
        "--exclude=asyncio",
        "--exclude=concurrent",
        "--exclude=multiprocessing",
        "--exclude=threading",
        "--exclude=subprocess",
        "--exclude=socket",
        "--exclude=ssl",
        "--exclude=cryptography",
        "--exclude=hashlib",
        "--exclude=hmac",
        "--exclude=secrets",
        "--exclude=base64",
        "--exclude=binascii",
        "--exclude=quopri",
        "--exclude=uu",
        "--exclude=encodings",
        "--exclude=codecs",
        "--exclude=unicodedata",
        "--exclude=stringprep",
        "--exclude=readline",
        "--exclude=rlcompleter",
        "--exclude=code",
        "--exclude=codeop",
        "--exclude=py_compile",
        "--exclude=compileall",
        "--exclude=dis",
        "--exclude=pickletools",
        "--exclude=tabnanny",
        "--exclude=pyclbr",
        "--exclude=py_compile",
        "--exclude=compileall",
        "--exclude=dis",
        "--exclude=pickletools",
        "--exclude=tabnanny",
        "--exclude=pyclbr",
        "--exclude=ast",
        "--exclude=token",
        "--exclude=tokenize",
        "--exclude=keyword",
        "--exclude=operator",
        "--exclude=inspect",
        "--exclude=atexit",
        "--exclude=signal",
        "--exclude=weakref",
        "--exclude=functools",
        "--exclude=itertools",
        "--exclude=collections",
        "--exclude=collections.abc",
        "--exclude=heapq",
        "--exclude=bisect",
        "--exclude=array",
        "--exclude=weakref",
        "--exclude=types",
        "--exclude=copy",
        "--exclude=pprint",
        "--exclude=reprlib",
        "--exclude=enum",
        "--exclude=dataclasses",
        "--exclude=typing",
        "--exclude=typing_extensions",
        "--exclude=abc",
        "--exclude=contextlib",
        "--exclude=contextvars",
        "--exclude=asyncio",
        "--exclude=concurrent",
        "--exclude=multiprocessing",
        "--exclude=threading",
        "--exclude=subprocess",
        "--exclude=socket",
        "--exclude=ssl",
        "--exclude=cryptography",
        "--exclude=hashlib",
        "--exclude=hmac",
        "--exclude=secrets",
        "--exclude=base64",
        "--exclude=binascii",
        "--exclude=quopri",
        "--exclude=uu",
        "--exclude=encodings",
        "--exclude=codecs",
        "--exclude=unicodedata",
        "--exclude=stringprep",
        "--exclude=readline",
        "--exclude=rlcompleter",
        "--exclude=code",
        "--exclude=codeop",
        "--exclude=py_compile",
        "--exclude=compileall",
        "--exclude=dis",
        "--exclude=pickletools",
        "--exclude=tabnanny",
        "--exclude=pyclbr",
        "--exclude=ast",
        "--exclude=token",
        "--exclude=tokenize",
        "--exclude=keyword",
        "--exclude=operator",
        "--exclude=inspect",
        "--exclude=atexit",
        "--exclude=signal",
        "--exclude=weakref",
        "--exclude=functools",
        "--exclude=itertools",
        "--exclude=collections",
        "--exclude=collections.abc",
        "--exclude=heapq",
        "--exclude=bisect",
        "--exclude=array",
        "--exclude=weakref",
        "--exclude=types",
        "--exclude=copy",
        "--exclude=pprint",
        "--exclude=reprlib",
        "--exclude=enum",
        "--exclude=dataclasses",
        "--exclude=typing",
        "--exclude=typing_extensions",
        "--exclude=abc",
        "--exclude=contextlib",
        "--exclude=contextvars",
        "app/main.py",
    ]

    if not run_command(cmd, "Building minimal EXE"):
        return False

    # Check result
    exe_path = Path("dist/MediaUploader.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 Build successful!")
        print(f"📁 EXE location: {exe_path.absolute()}")
        print(f"📊 File size: {size_mb:.1f} MB")

        # Create launcher
        batch_path = Path("run_media_uploader.bat")
        with open(batch_path, "w") as f:
            f.write(f'@echo off\n"{exe_path.absolute()}"\n')
        print(f"📝 Created launcher: {batch_path}")

        return True
    else:
        print("✗ EXE file not found")
        return False


def main():
    """Main function."""
    if build_minimal_exe():
        print("\n✅ Minimal build completed!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
