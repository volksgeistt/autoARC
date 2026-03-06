@echo off
title Auto ARC — Dependency Installer
color 0B


echo            Auto ARC — Dependency Installer                
echo                    by volksgeistt                           


python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR]  Python not found!
    echo.
    echo  Please install Python 3.8+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  [OK]  Found %PYVER%
echo.

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR]  pip not found. Trying to bootstrap...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo  [ERROR]  Could not install pip. Please install it manually.
        pause
        exit /b 1
    )
)

echo  [OK]  pip found
echo.

echo  [....] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  [OK]  pip up to date
echo.

:: ── Install dependencies ─────────────────────────────────────────
echo  
echo  ">"              Installing Dependencies                      
echo  
echo.

set FAILED=0

call :install pyautogui       "Mouse and keyboard automation"
call :install pyperclip       "Clipboard access for Unicode typer"
call :install colorama        "Colored terminal output"
call :install pyfiglet        "ASCII art banner"
call :install opencv-python   "Screen capture and image analysis"
call :install numpy           "Numerical arrays (required by OpenCV)"
call :install keyboard        "F8 pause/resume hotkey listener"

echo.

if %FAILED%==0 (
    echo    All dependencies installed successfully!  You're ready. 
) else (
    echo   Done with errors. Check above for failed packages.      
)


if %FAILED%==0 (
    echo  Run Auto ARC with:
    echo.
    echo      python main.py
    echo.
) else (
    echo  Some packages failed. Try running this installer as Administrator,
    echo  or install failed packages manually with:
    echo.
    echo      pip install ^<package-name^>
    echo.
)

pause
exit /b %FAILED%


:install
echo  [....] Installing %~1  —  %~2
pip install %~1 --quiet
if %errorlevel% neq 0 (
    echo  [FAIL] %~1 failed to install
    set FAILED=1
) else (
    echo  [ OK ] %~1
)
echo.
goto :eof