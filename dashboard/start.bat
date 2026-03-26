@echo off
title Roque Content Hub
echo =============================================
echo   ROQUE CONTENT HUB - Iniciando...
echo =============================================
echo.

cd /d "%~dp0"

REM Instala dependencias se necessario
pip install -q flask apscheduler requests pillow

echo.
echo  Abrindo dashboard em: http://localhost:5000
echo  Pressione CTRL+C para parar.
echo.

start "" http://localhost:5001
python app.py

pause
