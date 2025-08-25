#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build script for Media Uploader EXE
.DESCRIPTION
    Installs build requirements and creates a standalone EXE file
#>

Write-Host "Building Media Uploader EXE..." -ForegroundColor Green
Write-Host ""

# Install build requirements if needed
Write-Host "Installing build requirements..." -ForegroundColor Yellow
pip install -r requirements-build.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install build requirements!" -ForegroundColor Red
    exit 1
}

# Run the build script
Write-Host "Running build script..." -ForegroundColor Yellow
python build_exe.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build process completed!" -ForegroundColor Green
Read-Host "Press Enter to continue"
