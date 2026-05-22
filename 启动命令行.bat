@echo off
chcp 65001 >nul

:: Python and Git paths
set "PYTHON_HOME=C:\Users\ThinkPad\AppData\Local\Programs\Python\Python312"
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;C:\Program Files\Git\cmd;%PATH%"
set PYTHONIOENCODING=utf-8

cd /d "D:\Claude Code Database\20260520 TradingAgent-Astock"

echo ========================================
echo   TradingAgents-Astock CLI
echo ========================================
echo.

tradingagents

pause
