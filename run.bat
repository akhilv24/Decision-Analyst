@echo off
REM Decision Analyst Launcher
echo Starting Decision Analyst with AI Analysis...
echo.

REM Set environment to ignore bottleneck
set PYTHONWARNINGS=ignore::DeprecationWarning
set PYTHONDONTWRITEBYTECODE=1

REM Start the application using project virtual environment
if exist ".venv\Scripts\python.exe" (
	".venv\Scripts\python.exe" -W ignore app.py
) else (
	echo ERROR: .venv\Scripts\python.exe not found.
	echo Please recreate the environment first.
	exit /b 1
)

pause
