#!/usr/bin/env python3
"""
Test runner script for Media Uploader application.
Provides easy test execution with different options.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Media Uploader Test Runner")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "coverage", "quick"],
        default="unit",
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-n", type=int, default=1, help="Number of parallel processes"
    )
    parser.add_argument(
        "--stop-on-failure", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--html-report", action="store_true", help="Generate HTML coverage report"
    )

    args = parser.parse_args()

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add options based on arguments
    if args.verbose:
        cmd.append("-v")

    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])

    if args.stop_on_failure:
        cmd.append("-x")

    # Test type specific options
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
        description = "Unit Tests"
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
        description = "Integration Tests"
    elif args.type == "all":
        description = "All Tests"
    elif args.type == "coverage":
        cmd.extend(
            [
                "--cov=app",
                "--cov=core",
                "--cov=services",
                "--cov=infra",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
            ]
        )
        description = "Tests with Coverage"
    elif args.type == "quick":
        cmd.extend(["-m", "not slow"])
        description = "Quick Tests (excluding slow tests)"

    # Add HTML report if requested
    if args.html_report and args.type != "coverage":
        cmd.extend(["--cov-report=html:htmlcov"])

    # Run the tests
    success = run_command(cmd, description)

    if success:
        print(f"\n🎉 {description} passed!")
        return 0
    else:
        print(f"\n💥 {description} failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
