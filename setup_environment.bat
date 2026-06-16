@echo off
setlocal EnableDelayedExpansion

cd "C:\Users\yami_\Documents\Tramoias\Virtual Linux\EVIL_JWT_FORCE_BACKUP\EVIL_JWT_FORCE"

echo Verificando se o Python está instalado...
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python não encontrado. Por favor, instale o Python 3.9 ou superior de https://www.python.org/downloads/.
    pause
    exit /b 1
)

echo Criando ambiente virtual...
if not exist "venv" (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Erro ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando dependências necessárias...
pip install loguru pandas numpy scikit-learn tensorflow torch
if %ERRORLEVEL% neq 0 (
    echo Erro ao instalar dependências.
    pause
    exit /b 1
)

echo Criando diretórios necessários para o módulo de IA...
mkdir ai_module\models ai_module\data ai_module\logs ai_module\utils 2> nul

echo Configuração concluída com sucesso!
echo Ambiente virtual ativado. Para desativar, digite 'deactivate' no terminal.
pause 