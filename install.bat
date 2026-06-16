@echo off
echo [*] Iniciando instalador grafico do Evil JWT Force...

python installer_gui.py

if errorlevel 1 (
    echo [ERRO] Falha ao iniciar o instalador grafico.
    echo [*] Tentando instalacao via linha de comando...
    python install_deps.py
)

echo [*] Verificando Python 3 e pip...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python 3 nao encontrado. Instale antes de continuar.
    exit /b 1
)
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pip nao encontrado. Instale antes de continuar.
    exit /b 1
)

echo [*] Criando diretorios necessarios...
mkdir logs output reports 2>nul

echo [*] Criando atalho global...
set SCRIPT_DIR=%~dp0
set TARGET_DIR=%SCRIPT_DIR%core\cli.py
set LINK_NAME=%APPDATA%\Python\Scripts\evil-jwt-force.bat

echo @echo off > "%LINK_NAME%"
echo python "%TARGET_DIR%" %%* >> "%LINK_NAME%"

echo [*] Instalacao concluida!
echo [*] Voce pode executar o programa usando o comando 'evil-jwt-force' de qualquer lugar.
pause 