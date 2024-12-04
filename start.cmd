@echo off
:: Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not added to PATH. Please install Python and try again.
    exit /b 1
)

:: Requirements.txt
if not exist requirements.txt (
    echo Error: requirements.txt not found.
    exit /b 1
)

:: Dependeincies
echo Checking and installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo Error upgrading pip. Please check your Python installation.
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies. Please check your requirements.txt.
    exit /b 1
)

:: Main.py
if not exist main.py (
    echo Error: main.py not found. Please ensure it is in the same directory.
    exit /b 1
)

:: Start main.py
echo Starting main.py...
python main.py
if errorlevel 1 (
    echo Error running main.py. 
    exit /b 1
)