@echo off
setlocal EnableDelayedExpansion

cd "C:\Users\yami_\Documents\Tramoias\Virtual Linux\EVIL_JWT_FORCE_BACKUP\EVIL_JWT_FORCE"
if %ERRORLEVEL% neq 0 (
    echo Erro ao mudar para o diretório do projeto.
    pause
    exit /b 1
)

echo Iniciando configuração do ambiente avançado...
call setup_advanced_environment.bat
if %ERRORLEVEL% neq 0 (
    echo Erro ao executar o script de configuração.
    pause
    exit /b 1
)

echo Configuração concluída. Pressione qualquer tecla para fechar.
pause > nul 