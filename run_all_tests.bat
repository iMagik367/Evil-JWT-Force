@echo off
echo ===================================
echo EVIL-JWT-FORCE - Teste Completo
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

:: Define arquivo de log
set LOG_FILE=logs\test_execution_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
echo Iniciando testes em %date% %time% > %LOG_FILE%

echo.
echo [+] Configurando ferramentas JWT...
python scripts\setup_jwt_tools.py

echo.
echo [+] Testando ferramentas JWT...
set TEST_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImFkbWluIjp0cnVlfQ.BeHzSOVmjvh_Kmt5WcW5UqhAJCUKJpZhDRzzkkW-rwE
python scripts\jwt_analysis.py --token %TEST_TOKEN% --analyze --output output\jwt_test_results.json

echo.
echo [+] Testando simulação de brute force JWT...
python scripts\jwt_analysis.py --token %TEST_TOKEN% --crack --wordlist wordlist_final.txt --output output\jwt_crack_results.json

echo.
echo [+] Executando core\bruteforce.py
python -c "from core.bruteforce import JWTBruteforcer; JWTBruteforcer(token='%TEST_TOKEN%', wordlist_path='wordlist_final.txt').run()"

echo.
echo [+] Executando core\auth.py
python -c "from core.auth import Authenticator; Authenticator().run()"

echo.
echo [+] Executando core\sql_injector.py
python -c "from core.sql_injector import SQLInjector; SQLInjector().run()"

echo.
echo [+] Testando geração de token JWT
python -c "from modules.jwt_utils_simple import generate_test_token; print('Token gerado:', generate_test_token())"

echo.
echo [+] Testando decodificação de token JWT
python -c "from modules.jwt_utils_simple import decode_token_parts; print(decode_token_parts('%TEST_TOKEN%'))"

echo.
echo [+] Testando wordlist_generator
python -c "from core.wordlist_generator import generate_wordlist; generate_wordlist(100, 'output/test_wordlist.txt')"

echo.
echo [+] Verificando ferramentas externas instaladas
python -c "from modules.jwt_utils_simple import check_tools_availability; print('Ferramentas disponíveis:', check_tools_availability())"

echo.
echo [+] Executando teste PentestGPT (simulação)
python -c "try: from pentestgpt import PentestGPT; print(PentestGPT().analyze('%TEST_TOKEN%')); except ImportError: print('PentestGPT não disponível')"

echo.
echo [+] Executando relatório final
python -c "from core.report import generate_html_report; generate_html_report('output/jwt_test_results.json', 'output/jwt_test_report.html')"

echo.
echo ===================================
echo TESTES CONCLUÍDOS
echo Verifique a pasta 'output' para os resultados
echo ===================================

echo Todos os testes concluídos com sucesso! >> %LOG_FILE%

:: Desativa o ambiente virtual
call evil_jwt_env\Scripts\deactivate.bat

pause 