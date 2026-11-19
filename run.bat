@echo off
cd /d "%~dp0"
title Deadline-Aware Logistics Scheduling & Delivery Performance Evaluation
echo ======================================================================
echo Launching: Deadline-Aware Logistics Scheduling Application
echo ======================================================================
echo.

REM Try running via Python 3.12 where Streamlit and dependencies are installed
py -3.12 -m streamlit run app.py
if %ERRORLEVEL% EQU 0 goto end

REM Fallback to standard streamlit command
streamlit run app.py
if %ERRORLEVEL% EQU 0 goto end

REM Fallback to default python
python -m streamlit run app.py

:end
pause
