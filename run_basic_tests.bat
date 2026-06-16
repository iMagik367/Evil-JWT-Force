@echo off
echo ===================================
echo EVIL-JWT-FORCE - Testes Básicos
echo ===================================

:: Cria diretórios de saída
if not exist output mkdir output
if not exist logs mkdir logs

:: Define arquivo de log
set LOG_FILE=logs\basic_tests_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
echo Iniciando testes básicos em %date% %time% > %LOG_FILE%

echo.
echo [+] Testando geração de token JWT
python -c "from modules.jwt_utils_simple import generate_test_token; print('Token gerado:', generate_test_token())"

echo.
echo [+] Testando decodificação de token JWT
set TEST_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImFkbWluIjp0cnVlfQ.BeHzSOVmjvh_Kmt5WcW5UqhAJCUKJpZhDRzzkkW-rwE
python -c "from modules.jwt_utils_simple import decode_token_parts; print(decode_token_parts('%TEST_TOKEN%'))"

echo.
echo [+] Testando wordlist_generator (função básica)
python -c "from core.wordlist_generator import generate_wordlist; generate_wordlist(100, 'output/test_wordlist.txt')"

echo.
echo [+] Verificando ferramentas externas instaladas (simulação)
python -c "from modules.jwt_utils_simple import check_tools_availability; print('Ferramentas disponíveis:', check_tools_availability())"

echo.
echo [+] Executando relatório final
python -c "from core.report import generate_html_report; generate_html_report('output/test_results.json', 'output/test_report.html')"

echo.
echo ===================================
echo TESTES BÁSICOS CONCLUÍDOS
echo Verifique a pasta 'output' para os resultados
echo ===================================

echo Todos os testes básicos concluídos! >> %LOG_FILE%

pause 