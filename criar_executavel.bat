@echo off
setlocal
cd /d "%~dp0"
title Criar o programa (.exe) - PDF Reconstruction Studio
echo ============================================================
echo   Criando "PDF Reconstruction Studio.exe"
echo   Isso e feito UMA VEZ e leva alguns minutos (precisa de internet).
echo ============================================================
echo.

rem --- procura o Python ---
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto sem_python

rem --- ambiente isolado so para a construcao ---
if exist ".venv-build\Scripts\python.exe" goto venv_ok
echo [1/4] Criando ambiente isolado...
%PY% -m venv .venv-build
if errorlevel 1 goto erro
:venv_ok
set "VPY=.venv-build\Scripts\python.exe"

echo [2/4] Instalando as bibliotecas...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 goto erro
"%VPY%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto erro
rem opcional: permite conferir o resultado usando o Microsoft Word (se falhar, segue sem ele)
"%VPY%" -m pip install docx2pdf

echo [3/4] Construindo o programa...
"%VPY%" -m PyInstaller --noconfirm --clean pdf_studio.spec
if errorlevel 1 goto erro

set "PASTA=%~dp0dist\PDF Reconstruction Studio"
if not exist "%PASTA%\PDF Reconstruction Studio.exe" goto erro

echo [4/4] Criando o atalho na Area de Trabalho...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\PDF Reconstruction Studio.lnk'); $s.TargetPath='%PASTA%\PDF Reconstruction Studio.exe'; $s.WorkingDirectory='%PASTA%'; $s.Save()"

echo.
echo ============================================================
echo   PRONTO!  Abra o programa pelo atalho "PDF Reconstruction Studio"
echo   na Area de Trabalho, ou por:
echo   %PASTA%\PDF Reconstruction Studio.exe
echo   (pode mover a pasta inteira "PDF Reconstruction Studio" para onde quiser)
echo ============================================================
explorer "%PASTA%"
pause
exit /b 0

:sem_python
echo Python nao encontrado. Instale em https://www.python.org/downloads/
echo marcando "Add python.exe to PATH", e rode este arquivo de novo.
pause
exit /b 1

:erro
echo.
echo Algo deu errado na construcao. Role a janela para cima para ver a mensagem
echo de erro e me envie o texto.
pause
exit /b 1
