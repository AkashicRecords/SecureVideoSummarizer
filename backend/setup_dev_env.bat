@echo off
echo Setting up development environment for Secure Video Summarizer...

REM Check if Python 3 is installed
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python 3 and try again.
    exit /b 1
)

REM Check for system dependencies
echo Checking system dependencies...

REM Check for ffmpeg
where ffmpeg >NUL 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo ffmpeg is not installed. This is required for audio processing.
    echo Install instructions:
    echo   - Download from https://ffmpeg.org/download.html
    echo   - Add to PATH
    echo Please install ffmpeg and run this script again.
    exit /b 1
)

echo All system dependencies are installed or will be installed automatically.

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Please install venv package and try again.
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install setuptools and wheel
echo Installing setuptools and wheel...
pip install setuptools wheel

REM Install Windows-specific dependencies
echo Installing Windows-specific dependencies...
pip install python-magic-bin

REM Install dependencies from lock file
echo Installing dependencies from lock file...
if exist requirements.lock (
    pip install -r requirements.lock
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install from requirements.lock. Trying development requirements...
        if exist requirements.dev.txt (
            pip install -r requirements.dev.txt
            if %ERRORLEVEL% NEQ 0 (
                echo Failed to install dependencies. Please check requirements.dev.txt and try again.
                exit /b 1
            ) else (
                echo Successfully installed dependencies from requirements.dev.txt
            )
        ) else (
            echo requirements.dev.txt not found. Trying requirements.txt...
            pip install -r requirements.txt
            if %ERRORLEVEL% NEQ 0 (
                echo Failed to install dependencies. Please check requirements.txt and try again.
                exit /b 1
            ) else (
                echo Successfully installed dependencies from requirements.txt
            )
        )
    ) else (
        echo Successfully installed dependencies from requirements.lock
    )
) else (
    echo requirements.lock not found. Using requirements.dev.txt instead.
    if exist requirements.dev.txt (
        pip install -r requirements.dev.txt
        if %ERRORLEVEL% NEQ 0 (
            echo Failed to install dependencies. Please check requirements.dev.txt and try again.
            exit /b 1
        ) else (
            echo Successfully installed dependencies from requirements.dev.txt
        )
    ) else (
        echo requirements.dev.txt not found. Using requirements.txt...
        pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
            echo Failed to install dependencies. Please check requirements.txt and try again.
            exit /b 1
        ) else (
            echo Successfully installed dependencies from requirements.txt
        )
    )
)

REM Verify installation
echo Verifying installation...
python -c "import flask, torch, transformers, pydub, numpy; print('All core dependencies are installed.')"
if %ERRORLEVEL% NEQ 0 (
    echo Verification failed. Some dependencies may not be installed correctly.
    exit /b 1
)

REM Install pre-commit hooks
echo Installing pre-commit hooks...
pip install pre-commit
pre-commit install
echo Pre-commit hooks installed successfully.

echo Development environment setup completed successfully!
echo Run 'venv\Scripts\activate' to activate the virtual environment.
echo To run tests, run: python run_tests.py 