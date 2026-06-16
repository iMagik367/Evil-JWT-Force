@echo off
setlocal EnableDelayedExpansion

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat 2>nul
if %ERRORLEVEL% neq 0 (
    echo Ambiente virtual não encontrado ou não ativado. Continuando sem ativação.
)

if "%1"=="" (
    echo.
    echo Evil-Force-JWT - Sistema de IA para análise e ataque de tokens JWT
    echo.
    echo Modos de operação:
    echo   1. Modo de demonstração
    echo   2. Analisar e atacar um token JWT
    echo   3. Analisar e atacar um token JWT de um arquivo
    echo   4. Analisar um site alvo
    echo   5. Exibir ajuda completa
    echo.
    set /p opcao="Escolha uma opção (1-5): "
    
    if "!opcao!"=="1" (
        echo Iniciando modo de demonstração...
        python ai_system\main.py --demo
    ) else if "!opcao!"=="2" (
        set /p token="Digite o token JWT: "
        set /p wordlist="Caminho para wordlist (opcional, pressione Enter para pular): "
        set /p output="Arquivo de saída (opcional, pressione Enter para pular): "
        
        if not "!wordlist!"=="" (
            if not "!output!"=="" (
                python ai_system\main.py --token !token! --wordlist !wordlist! --output !output! --verbose
            ) else (
                python ai_system\main.py --token !token! --wordlist !wordlist! --verbose
            )
        ) else (
            if not "!output!"=="" (
                python ai_system\main.py --token !token! --output !output! --verbose
            ) else (
                python ai_system\main.py --token !token! --verbose
            )
        )
    ) else if "!opcao!"=="3" (
        set /p token_file="Caminho para o arquivo com o token JWT: "
        set /p wordlist="Caminho para wordlist (opcional, pressione Enter para pular): "
        set /p output="Arquivo de saída (opcional, pressione Enter para pular): "
        
        if not "!wordlist!"=="" (
            if not "!output!"=="" (
                python ai_system\main.py --token-file !token_file! --wordlist !wordlist! --output !output! --verbose
            ) else (
                python ai_system\main.py --token-file !token_file! --wordlist !wordlist! --verbose
            )
        ) else (
            if not "!output!"=="" (
                python ai_system\main.py --token-file !token_file! --output !output! --verbose
            ) else (
                python ai_system\main.py --token-file !token_file! --verbose
            )
        )
    ) else if "!opcao!"=="4" (
        set /p url="Digite a URL do site alvo: "
        set /p output="Arquivo de saída (opcional, pressione Enter para pular): "
        
        if not "!output!"=="" (
            python ai_system\main.py --url !url! --output !output! --verbose
        ) else (
            python ai_system\main.py --url !url! --verbose
        )
    ) else if "!opcao!"=="5" (
        python ai_system\main.py --help
    ) else (
        echo Opção inválida!
        exit /b 1
    )
) else (
    echo Iniciando sistema de IA com parâmetros da linha de comando...
    python ai_system\main.py %*
)

echo.
echo Sistema de IA concluído. Pressione qualquer tecla para fechar esta janela...
pause > nul 