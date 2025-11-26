@echo off
echo ===================================================
echo  CSV Import App - Start Web Server
echo ===================================================

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Running database migrations...
alembic upgrade head

echo Starting Web Server...
echo Access the app at http://localhost:8000
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
