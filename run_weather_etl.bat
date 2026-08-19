@echo off
cd /d D:\weather_api
set PYTHON_EXE=C:\path\to\python310\python.exe

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" scripts\weather_etl.py >> logs\weather_etl_task.log 2>&1
) else (
    echo Python 3.10 interpreter not found at %PYTHON_EXE%
    echo Update the PYTHON_EXE path in run_weather_etl.bat
    exit /b 1
)
