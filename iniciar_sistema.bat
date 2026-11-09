@echo off
title Vendas Barreto Correa
echo ============================================================
echo        INICIANDO PLATAFORMA VENDAS BARRETO CORREA
echo ============================================================
echo.
echo Abrindo painel no navegador em http://localhost:8501 ...
echo.
cd /d "%~dp0"
start http://localhost:8501
python -m http.server 8501 --bind 127.0.0.1
pause
