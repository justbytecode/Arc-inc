@echo off
echo ===================================================
echo  CSV Import App - Start Celery Worker
echo ===================================================

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo Virtual environment not found. Please run start_web.bat first to set it up.
    pause
    exit /b
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Celery Worker...
celery -A app.worker worker --loglevel=info --pool=solo

pause
