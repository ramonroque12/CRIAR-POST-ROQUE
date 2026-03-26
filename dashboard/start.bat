@echo off
title Roque Content Hub
echo =============================================
echo   ROQUE CONTENT HUB - Iniciando...
echo =============================================
echo.

cd /d "%~dp0"

REM ── Carrega chave do arquivo .env (nao commitar .env no git) ─────────────────
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if "%%A"=="ANTHROPIC_API_KEY" set ANTHROPIC_API_KEY=%%B
)
REM ─────────────────────────────────────────────────────────────────────────────

REM Instala dependencias se necessario
pip install -q flask apscheduler requests pillow anthropic

echo.
echo  Abrindo dashboard em: http://localhost:5001
echo  Pressione CTRL+C para parar.
echo.

start "" http://localhost:5001
python app.py

pause
