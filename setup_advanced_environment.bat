@echo off
setlocal EnableDelayedExpansion
echo DEBUG: Script de Configuração Avançada Iniciado.

echo DEBUG: Mudando para o diretório do projeto...
cd "C:\Users\yami_\Documents\Tramoias\Virtual Linux\EVIL_JWT_FORCE_BACKUP\EVIL_JWT_FORCE"
if %ERRORLEVEL% neq 0 (
    echo ERRO CRÍTICO: Falha ao mudar para o diretório do projeto.
    pause
    exit /b 1
)
echo DEBUG: Diretório do projeto definido.

echo DEBUG: Verificando Python...
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERRO: Python não encontrado. Instale Python 3.9+.
    pause
    exit /b 1
)
echo DEBUG: Python encontrado.

echo DEBUG: Configurando Rust e target GNU...
echo INFO: rustup não foi encontrado. Tentando instalar Rust completo (incluindo rustup e toolchain MSVC padrão)...
echo DEBUG: Preparando para executar comando PowerShell para instalar Rust...
set SCRIPT_DIR=%CD%
set RUSTUP_DOWNLOAD_URL=https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; Write-Host 'PowerShell: Baixando rustup-init.exe de %RUSTUP_DOWNLOAD_URL% ...'; Invoke-WebRequest -Uri '%RUSTUP_DOWNLOAD_URL%' -OutFile '%SCRIPT_DIR%\rustup-init.exe'; Write-Host 'PowerShell: Download concluído.'; if (Test-Path '%SCRIPT_DIR%\rustup-init.exe') { Write-Host 'PowerShell: rustup-init.exe encontrado. Tentando executar...'; Start-Process -FilePath '%SCRIPT_DIR%\rustup-init.exe' -ArgumentList '-y --default-toolchain stable-x86_64-pc-windows-msvc' -Wait; Write-Host 'PowerShell: Start-Process para rustup-init.exe concluído.'; } else { Write-Error 'PowerShell: ERRO - rustup-init.exe não encontrado após download.' }"
set RUST_INSTALL_ERRORLEVEL=%ERRORLEVEL%
echo DEBUG: Comando PowerShell para instalar Rust concluído com código de erro: %RUST_INSTALL_ERRORLEVEL%.

if %RUST_INSTALL_ERRORLEVEL% neq 0 (
    echo ERRO: Falha ao instalar Rust via PowerShell. Código de erro: %RUST_INSTALL_ERRORLEVEL%.
    echo       Verifique a saída do PowerShell acima e o arquivo '%SCRIPT_DIR%\rustup-init.exe'.
    echo       Baixe manualmente de https://www.rust-lang.org/tools/install.
    pause
    exit /b 1
)

set PATH=%PATH%;%USERPROFILE%\.cargo\bin
echo DEBUG: Rust (potencialmente) instalado. PATH (potencialmente) atualizado.
echo DEBUG: Agora adicionando toolchain GNU...
call "%USERPROFILE%\.cargo\bin\rustup.exe" target add x86_64-pc-windows-gnu
if %ERRORLEVEL% neq 0 (
    echo AVISO: Falha ao adicionar target x86_64-pc-windows-gnu após a instalação do Rust. A compilação pode falhar.
) else (
    echo DEBUG: Target x86_64-pc-windows-gnu adicionado após a instalação do Rust.
)

rem --- Seção Node.js (Manter comentada por enquanto) ---
rem echo DEBUG: Verificando Node.js...
rem where node > nul 2>&1
rem if %ERRORLEVEL% neq 0 (
rem     echo INFO: Node.js não encontrado. Tentando instalar...
rem     C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "Invoke-WebRequest -Uri https://nodejs.org/dist/v18.17.0/node-v18.17.0-x64.msi -OutFile node-installer.msi; msiexec /i node-installer.msi /quiet"
rem     if %ERRORLEVEL% neq 0 (
rem         echo ERRO: Falha ao instalar Node.js.
rem         pause
rem         exit /b 1
rem     )
rem     set PATH=%PATH%;C:\Program Files\nodejs
rem     echo DEBUG: Node.js instalado.
rem ) else (
rem     echo DEBUG: Node.js já encontrado.
rem )

rem --- Seção Docker (Manter comentada por enquanto) ---
rem echo DEBUG: Verificando Docker...
rem where docker > nul 2>&1
rem if %ERRORLEVEL% neq 0 (
rem     echo ERRO: Docker não encontrado.
rem     pause
rem     exit /b 1
rem )
rem echo DEBUG: Docker encontrado.

echo DEBUG: Criando ambiente virtual Python (venv)...
if not exist "venv" (
    echo DEBUG: Diretório venv não existe. Criando...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERRO: Falha ao criar ambiente virtual venv.
        pause
        exit /b 1
    )
    echo DEBUG: Ambiente virtual venv criado.
) else (
    echo DEBUG: Ambiente virtual venv já existe.
)

echo DEBUG: Ativando ambiente virtual venv...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERRO: Falha ao ativar ambiente virtual venv.
    pause
    exit /b 1
)
echo DEBUG: Ambiente virtual venv ativado.

echo DEBUG: Instalando dependências Python...
pip install loguru pandas numpy scikit-learn torch flask websocket-client psutil joblib
if %ERRORLEVEL% neq 0 (
    echo ERRO: Falha ao instalar dependências Python.
    pause
    exit /b 1
)
echo DEBUG: Dependências Python instaladas.

echo DEBUG: Criando diretórios do sistema de IA...
mkdir ai_system\monitoring ai_system\analysis ai_system\correction ai_system\evolution ai_system\data ai_system\logs ai_system\interfaces 2> nul
echo DEBUG: Diretórios do sistema de IA criados/verificados.

echo Configuração do ambiente concluída com sucesso!
echo Pressione qualquer tecla para fechar esta janela...
pause > nul 