@echo off
setlocal
echo ===================================================
echo  Pushing Automation Sales Pipeline to GitHub
echo ===================================================

set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%LOCALAPPDATA%\Programs\Git\mingw64\bin;%PATH%"

cd /d "%~dp0"

echo Current directory: %cd%
echo Git executable:
where git

echo.
echo Attempting to push to origin main...
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===================================================
    echo [ERROR] Push failed!
    echo Common reasons:
    echo 1. The repository https://github.com/soham-analyst/Automation-Sales-Pipeline
    echo    has NOT been created on GitHub yet. Please create it at: https://github.com/new
    echo 2. Authentication was cancelled or failed.
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo [SUCCESS] Pushed successfully!
    echo Check actions at: https://github.com/soham-analyst/Automation-Sales-Pipeline/actions
    echo ===================================================
)

pause
