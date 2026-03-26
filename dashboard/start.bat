@echo off
title Roque Content Hub
echo =============================================
echo   ROQUE CONTENT HUB - Iniciando...
echo =============================================
echo.

cd /d "%~dp0"

REM ── CONFIGURE SUA CHAVE ANTHROPIC AQUI ──────────────────────────────────────
REM Substitua SUA_CHAVE_AQUI pela sua chave de https://console.anthropic.com
set ANTHROPIC_API_KEY=SUA_CHAVE_AQUI
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
