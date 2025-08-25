#!/usr/bin/env python3
"""
Linting script for the media uploader project.

This script provides a convenient way to run all linting tools
with various options and configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def run_black(files: Optional[List[str]] = None, check: bool = False) -> bool:
    """Run black code formatter."""
    cmd = ["black"]
    if check:
        cmd.append("--check")
    if files:
        cmd.extend(files)
    else:
        cmd.extend([".", "--exclude", "private", "--exclude", "demo_media"])

    return run_command(cmd, "Black code formatting")


def run_isort(files: Optional[List[str]] = None, check: bool = False) -> bool:
    """Run isort import sorter."""
    cmd = ["isort"]
    if check:
        cmd.append("--check-only")
    if files:
        cmd.extend(files)
    else:
        cmd.extend([".", "--skip", "private", "--skip", "demo_media"])

    return run_command(cmd, "isort import sorting")


def run_flake8(files: Optional[List[str]] = None) -> bool:
    """Run flake8 code linter."""
    cmd = ["flake8"]
    if files:
        cmd.extend(files)
    else:
        cmd.extend([".", "--exclude", "private,demo_media"])

    return run_command(cmd, "Flake8 code linting")


def run_mypy(files: Optional[List[str]] = None) -> bool:
    """Run mypy type checker."""
    cmd = ["mypy"]
    if files:
        cmd.extend(files)
    else:
        cmd.extend(["app", "core", "services", "infra"])

    return run_command(cmd, "MyPy type checking")


def run_bandit(files: Optional[List[str]] = None) -> bool:
    """Run bandit security linter."""
    cmd = ["bandit", "-r", ".", "-f", "json", "-o", "bandit-report.json"]
    if files:
        cmd = ["bandit"] + files + ["-f", "json", "-o", "bandit-report.json"]

    return run_command(cmd, "Bandit security analysis")


def run_all_linters(files: Optional[List[str]] = None, check: bool = False) -> bool:
    """Run all linting tools."""
    success = True

    # Run formatters first
    success &= run_black(files, check)
    success &= run_isort(files, check)

    # Run linters
    success &= run_flake8(files)
    success &= run_mypy(files)
    success &= run_bandit(files)

    return success


def main():
    """Main function to parse arguments and run linting tools."""
    parser = argparse.ArgumentParser(
        description="Run linting tools for the media uploader project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_lint.py --all                    # Run all linters
  python run_lint.py --black --check          # Check black formatting only
  python run_lint.py --isort app/             # Format imports in app/ directory
  python run_lint.py --all --check            # Check all formatting without changes
  python run_lint.py --files app/ui/main_window.py  # Lint specific file
        """,
    )

    parser.add_argument("--all", action="store_true", help="Run all linting tools")
    parser.add_argument("--black", action="store_true", help="Run black code formatter")
    parser.add_argument("--isort", action="store_true", help="Run isort import sorter")
    parser.add_argument("--flake8", action="store_true", help="Run flake8 code linter")
    parser.add_argument("--mypy", action="store_true", help="Run mypy type checker")
    parser.add_argument(
        "--bandit", action="store_true", help="Run bandit security linter"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting without making changes (for black and isort)",
    )
    parser.add_argument(
        "--files", nargs="+", help="Specific files or directories to lint"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Validate files exist if specified
    if args.files:
        for file_path in args.files:
            if not Path(file_path).exists():
                print(f"❌ Error: File or directory '{file_path}' does not exist")
                sys.exit(1)

    # If no specific tools selected, default to all
    if not any([args.all, args.black, args.isort, args.flake8, args.mypy, args.bandit]):
        args.all = True

    success = True

    try:
        if args.all:
            success = run_all_linters(args.files, args.check)
        else:
            if args.black:
                success &= run_black(args.files, args.check)
            if args.isort:
                success &= run_isort(args.files, args.check)
            if args.flake8:
                success &= run_flake8(args.files)
            if args.mypy:
                success &= run_mypy(args.files)
            if args.bandit:
                success &= run_bandit(args.files)

        print(f"\n{'='*60}")
        if success:
            print("🎉 All linting tools completed successfully!")
            sys.exit(0)
        else:
            print("❌ Some linting tools failed. Please fix the issues above.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Linting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
