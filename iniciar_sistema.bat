@echo off
title Controle de Vendas Natura
echo ============================================================
echo      INICIANDO SISTEMA DE CONTROLE DE VENDAS NATURA
echo ============================================================
echo.
cd /d "%~dp0"
python -m streamlit run app.py
pause
