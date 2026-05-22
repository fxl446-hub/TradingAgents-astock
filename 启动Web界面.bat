@echo off
chcp 65001 >nul

set "PYTHON_HOME=C:\Users\ThinkPad\AppData\Local\Programs\Python\Python312"
set "PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;C:\Program Files\Git\cmd;%PATH%"
set PYTHONIOENCODING=utf-8

cd /d "D:\Claude Code Database\20260520 TradingAgent-Astock"

echo ========================================
echo   TradingAgents-Astock Web 界面
echo ========================================
echo.
echo 正在启动 Streamlit...
echo 浏览器将打开 http://localhost:8501
echo 按 Ctrl+C 可以停止
echo.

start http://localhost:8501
"%PYTHON_HOME%\python.exe" -m streamlit run web/app.py --server.port 8501 --server.headless true

pause
