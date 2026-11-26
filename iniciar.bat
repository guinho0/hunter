@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Hunter

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado.
    echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Primeira execucao: preparando o ambiente, leva alguns minutos...
    python -m venv .venv || (pause & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install -q --upgrade pip
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt || (pause & exit /b 1)

echo Abrindo o Hunter no navegador. Feche esta janela para encerrar o app.
start "" cmd /c "timeout /t 6 >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
