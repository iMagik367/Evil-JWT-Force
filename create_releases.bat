@echo off
echo ===========================================
echo   Evil JWT Force - Criacao de Releases
echo ===========================================
echo.

REM Verificar se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado. Por favor, instale o Python 3.8 ou superior.
    exit /b 1
)

REM Verificar se o PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo ERRO: Falha ao instalar PyInstaller.
        exit /b 1
    )
)

REM Instalar dependências
echo Instalando dependencias...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Algumas dependencias podem nao ter sido instaladas corretamente.
)

REM Criar diretório para releases se não existir
if not exist "releases" mkdir releases

REM Executar o script de build
echo Criando executavel...
python build_executables.py
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao criar o executavel.
    exit /b 1
)

REM Criar ZIP para distribuição
echo Criando pacote ZIP para distribuicao...
cd dist
powershell -Command "Compress-Archive -Path Evil_JWT_Force.exe, README.md, MANUAL.txt -DestinationPath ..\releases\Evil_JWT_Force_Windows.zip -Force"
cd ..

echo.
echo ===========================================
echo   Release criada com sucesso!
echo   Arquivo: releases\Evil_JWT_Force_Windows.zip
echo ===========================================

exit /b 0 