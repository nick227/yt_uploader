@echo off
echo Building Media Uploader EXE...
echo.

REM Install build requirements if needed
echo Installing build requirements...
pip install -r requirements-build.txt

REM Run the build script
python build_exe.py

echo.
echo Build process completed!
pause
