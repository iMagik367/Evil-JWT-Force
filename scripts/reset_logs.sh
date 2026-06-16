#!/bin/bash

set -e

echo "🧹 Limpando logs e arquivos de saída..."
cd "$(dirname "$0")/.."

declare -a LOG_FILES=(
    "logs/bruteforce.log"
    "logs/errors.log"
)

declare -a OUTPUT_FILES=(
    "output/wordlist.txt"
    "output/wordlist_tested.txt"
    "output/found_secrets.txt"
    "output/valid_credentials.txt"
    "output/fail_credentials.txt"
    "output/intercepted_tokens.txt"
)

declare -a REPORTS_HTML=(
    "reports/report.html"
    "output/report.html"
)

# Limpar logs
for file in "${LOG_FILES[@]}"; do
    if [ -f "$file" ]; then
        > "$file"
    else
        mkdir -p "$(dirname "$file")"
        touch "$file"
    fi
done

# Limpar outputs
for file in "${OUTPUT_FILES[@]}"; do
    if [ -f "$file" ]; then
        > "$file"
    else
        mkdir -p "$(dirname "$file")"
        touch "$file"
    fi
done

# Remover relatórios HTML antigos
for file in "${REPORTS_HTML[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
    fi
done

echo "✅ Limpeza completa."