@echo off
setlocal EnableDelayedExpansion
echo Minimal Test: Script Iniciado.

echo Minimal Test: Tentando mudar para o diretório do projeto...
cd "C:\Users\yami_\Documents\Tramoias\Virtual Linux\EVIL_JWT_FORCE_BACKUP\EVIL_JWT_FORCE"
if %ERRORLEVEL% neq 0 (
    echo Minimal Test: ERRO CRÍTICO ao mudar para o diretório do projeto.
    pause
    exit /b 1
)
echo Minimal Test: Diretório do projeto definido com sucesso.

echo Minimal Test: Verificando Python...
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Minimal Test: ERRO - Python não encontrado.
    pause
    exit /b 1
)
echo Minimal Test: Python encontrado com sucesso.

echo Minimal Test: Próxima linha é um pause.
pause

echo Minimal Test: Script concluído.
pause > nul 