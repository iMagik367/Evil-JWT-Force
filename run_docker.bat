@echo off

:: Script para construir e executar o container Docker do EVIL_JWT_FORCE

:: Constrói a imagem Docker
echo Construindo a imagem Docker...
docker build -t evil_jwt_force:latest .

:: Verifica se a construção foi bem-sucedida
if %ERRORLEVEL% equ 0 (
    echo Imagem construida com sucesso!
    echo Executando o container...
    :: Executa o container em modo interativo
    docker run -it --rm evil_jwt_force:latest
) else (
    echo Erro ao construir a imagem Docker.
    exit /b 1
) 