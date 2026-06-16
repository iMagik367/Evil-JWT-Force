#!/bin/bash

set -e

echo "🔁 Iniciando modo automático do EVIL_JWT_FORCE..."
cd "$(dirname "$0")/.."

# Detecta sistema operacional para ativar o ambiente virtual corretamente
if [ -d "venv" ]; then
    if [ -f "venv/Scripts/activate" ]; then
        # Windows
        echo "🔄 Ativando ambiente virtual (Windows)..."
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        # Linux/Mac
        echo "🔄 Ativando ambiente virtual (Linux/Mac)..."
        source venv/bin/activate
    else
        echo "⚠️ Ambiente virtual encontrado, mas não foi possível ativar."
    fi
else
    echo "⚠️ Ambiente virtual não encontrado. Continuando sem ativação."
fi

# Verifica se o Python está disponível
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "❌ Python não encontrado no sistema. Instale o Python 3 para continuar."
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

# Executa CLI no modo automático
echo "🚀 Executando CLI em modo automático..."
$PYTHON_CMD core/cli.py --auto

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Execução automática concluída com sucesso."
else
    echo "❌ Execução automática finalizada com erro (código $EXIT_CODE)."
fi