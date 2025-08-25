# Media Uploader Build Guide

This guide explains how to build a standalone EXE file for the Media Uploader application.

## Prerequisites

- Python 3.8 or higher
- Windows operating system (for EXE creation)
- All application dependencies installed

## Quick Build

### Option 1: Using the batch file (Windows)
```cmd
build.bat
```

### Option 2: Using PowerShell
```powershell
.\build.ps1
```

### Option 3: Manual build
```cmd
# Install build requirements
pip install -r requirements-build.txt

# Run build script
python build_exe.py
```

## Build Process

The build process performs the following steps:

1. **Install PyInstaller**: Automatically installs PyInstaller if not present
2. **Create Icon**: Generates a custom icon for the application
3. **Clean Previous Builds**: Removes any existing build artifacts
4. **Package Application**: Creates a single EXE file with all dependencies
5. **Create Launcher**: Generates a batch file for easy launching

## Build Output

After a successful build, you'll find:

- `dist/MediaUploader.exe` - The standalone executable
- `run_media_uploader.bat` - A launcher script
- `assets/icon.ico` - The application icon

## Customization

### Custom Icon

To use your own icon:

1. Create an ICO file (256x256 pixels recommended)
2. Place it at `assets/icon.ico`
3. Run the build process

The build script will automatically use your custom icon.

### Build Options

You can modify `build_exe.py` to customize the build:

- **Single file vs directory**: Change `--onefile` to `--onedir` for a directory-based distribution
- **Console window**: Remove `--windowed` to show a console window
- **Additional files**: Add `--add-data` options to include extra files
- **Hidden imports**: Add `--hidden-import` for modules not automatically detected

## Troubleshooting

### Common Issues

1. **"PyInstaller not found"**
   - Run: `pip install pyinstaller`

2. **"Missing modules"**
   - Add missing modules to the `--hidden-import` list in `build_exe.py`

3. **"Large file size"**
   - The EXE includes all dependencies and can be 50-100MB
   - Use `--onedir` instead of `--onefile` for smaller size

4. **"Application doesn't start"**
   - Check that all required files are included
   - Try running with console window (remove `--windowed`)

### Debug Build

For debugging, create a build with console output:

```cmd
pyinstaller --onefile --icon=assets/icon.ico --name=MediaUploader app/main.py
```

## Distribution

The generated EXE file is completely standalone and can be distributed to other Windows machines without requiring Python or any dependencies to be installed.

### File Size

- Typical size: 50-100MB
- Includes: Python runtime, PySide6, Google APIs, all dependencies

### Performance

- First run: May take 10-30 seconds to extract resources
- Subsequent runs: Normal startup time
- Memory usage: Similar to running from source

## Advanced Configuration

### PyInstaller Spec File

For advanced customization, you can generate and modify a spec file:

```cmd
pyi-makespec --onefile --windowed --icon=assets/icon.ico app/main.py
```

Then edit `app.spec` and build with:

```cmd
pyinstaller app.spec
```

### Code Signing

For production distribution, consider code signing the EXE:

1. Obtain a code signing certificate
2. Use `signtool` or similar to sign the EXE
3. This prevents Windows security warnings

## Support

If you encounter build issues:

1. Check the console output for error messages
2. Ensure all dependencies are installed
3. Try a clean build (delete `dist/` and `build/` folders)
4. Check PyInstaller documentation for specific issues
