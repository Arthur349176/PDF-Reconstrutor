@echo off
setlocal
cd /d "%~dp0"
title PDF Reconstruction Studio

rem Procura o Python: venv do projeto primeiro, depois o do sistema.
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"
if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo Python nao encontrado.
    echo Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
    pause
    exit /b 1
)

rem Confere as dependencias antes de abrir a janela.
%PY% -c "import PySide6, pymupdf, docx" 2>nul
if errorlevel 1 (
    echo Faltam dependencias do programa. Execute este comando e tente de novo:
    echo.
    echo     %PY% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

%PY% run_gui.py
if errorlevel 1 (
    echo.
    echo O programa terminou com erro. Detalhes em: logs\startup_error.log
    pause
)
