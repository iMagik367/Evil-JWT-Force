@echo off
echo ===================================
echo EVIL-JWT-FORCE - JWT Analysis Tool
echo ===================================

:: Ativa o ambiente virtual
if exist evil_jwt_env\Scripts\activate.bat (
    call evil_jwt_env\Scripts\activate.bat
) else (
    echo Ambiente virtual nao encontrado.
    echo Criando ambiente virtual...
    python -m venv evil_jwt_env
    call evil_jwt_env\Scripts\activate.bat
    pip install -r requirements.txt
)

:: Cria diretórios de saída
if not exist output mkdir output
if not exist logs mkdir logs

:: Configura ferramentas JWT se necessário
if not exist external\jwt_tool (
    echo [+] Configurando ferramentas JWT pela primeira vez...
    python scripts\setup_jwt_tools.py
    echo.
)

:: Lista as ferramentas disponíveis
python scripts\jwt_analysis.py --list-tools

:: Menu principal
:menu
echo.
echo ===================================
echo        MENU PRINCIPAL
echo ===================================
echo [1] Analisar um token JWT
echo [2] Quebrar um token JWT (brute force)
echo [3] Configurar ferramentas JWT
echo [4] Listar ferramentas disponíveis
echo [5] Executar todos os testes
echo [0] Sair
echo.
set /p opcao="Escolha uma opção: "

if "%opcao%"=="1" goto analisar
if "%opcao%"=="2" goto quebrar
if "%opcao%"=="3" goto configurar
if "%opcao%"=="4" goto listar
if "%opcao%"=="5" goto testes
if "%opcao%"=="0" goto sair

echo Opção inválida!
goto menu

:analisar
echo.
echo === ANÁLISE DE TOKEN JWT ===
set /p token="Digite o token JWT (ou digite 'arquivo' para ler de um arquivo): "

if "%token%"=="arquivo" (
    set /p arquivo="Digite o caminho do arquivo: "
    python scripts\jwt_analysis.py --token-file "%arquivo%" --analyze --output output\jwt_analysis_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json
) else (
    python scripts\jwt_analysis.py --token "%token%" --analyze --output output\jwt_analysis_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json
)

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause > nul
goto menu

:quebrar
echo.
echo === QUEBRA DE TOKEN JWT ===
set /p token="Digite o token JWT (ou digite 'arquivo' para ler de um arquivo): "
set /p wordlist="Digite o caminho da wordlist (deixe em branco para usar a padrão): "

if "%wordlist%"=="" set wordlist=wordlist_final.txt

if "%token%"=="arquivo" (
    set /p arquivo="Digite o caminho do arquivo: "
    python scripts\jwt_analysis.py --token-file "%arquivo%" --crack --wordlist "%wordlist%" --output output\jwt_crack_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json
) else (
    python scripts\jwt_analysis.py --token "%token%" --crack --wordlist "%wordlist%" --output output\jwt_crack_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json
)

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause > nul
goto menu

:configurar
echo.
echo === CONFIGURAÇÃO DE FERRAMENTAS JWT ===
python scripts\setup_jwt_tools.py

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause > nul
goto menu

:listar
echo.
echo === FERRAMENTAS JWT DISPONÍVEIS ===
python scripts\jwt_analysis.py --list-tools

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause > nul
goto menu

:testes
echo.
echo === EXECUTANDO TODOS OS TESTES ===
call run_all_tests.bat

echo.
echo Pressione qualquer tecla para voltar ao menu...
pause > nul
goto menu

:sair
:: Desativa o ambiente virtual
call evil_jwt_env\Scripts\deactivate.bat
echo Saindo...
exit /b 0 