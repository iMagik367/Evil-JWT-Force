#!/bin/bash

set -e

cd "$(dirname "$0")/.."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPORT_DIR="exports"
FILENAME="EVIL_JWT_FORCE_REPORT_$TIMESTAMP.zip"

# Verifica se o zip está instalado
if ! command -v zip >/dev/null 2>&1; then
    echo "❌ O utilitário 'zip' não está instalado. Instale-o para continuar."
    exit 1
fi

mkdir -p "$EXPORT_DIR"

INCLUDE_PATHS=(
    "output/"
    "logs/"
    "reports/"
    "config/*.txt"
    "config/*.yaml"
    "config/*.json"
    "output/*.txt"
    "output/*.json"
    "output/*.html"
    "output/*.log"
    "output/*.csv"
    "reports/*.html"
    "reports/*.json"
    "reports/*.log"
)

EXCLUDE_PATTERNS=(
    "*.DS_Store"
    "*.tmp"
    "*.bak"
    "output/__pycache__/*"
    "logs/__pycache__/*"
    "reports/__pycache__/*"
)

ZIP_CMD=(zip -r "$EXPORT_DIR/$FILENAME")

for path in "${INCLUDE_PATHS[@]}"; do
    ZIP_CMD+=("$path")
done

for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    ZIP_CMD+=(-x "$pattern")
done

echo "📦 Compactando logs, outputs, relatórios e arquivos de configuração..."
"${ZIP_CMD[@]}"

if [ $? -eq 0 ]; then
    echo "✅ Arquivo gerado: $EXPORT_DIR/$FILENAME"
else
    echo "❌ Falha ao gerar o arquivo ZIP."
    exit 2
fi