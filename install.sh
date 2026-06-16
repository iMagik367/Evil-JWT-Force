#!/bin/bash

set -e

echo "[*] Iniciando instalador grafico do Evil JWT Force..."

python3 installer_gui.py || {
    echo "[ERRO] Falha ao iniciar o instalador grafico."
    echo "[*] Tentando instalacao via linha de comando..."
    python3 install_deps.py
}

echo "[*] Criando diretórios necessários..."
mkdir -p logs output reports

echo "[*] Ajustando permissões de scripts e módulos..."
find scripts -type f -name "*.sh" -exec chmod +x {} \;
find core -type f -name "*.py" -exec chmod +x {} \;
chmod 755 -R .

echo "[*] Verificando Python 3 e pip..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] Python 3 não encontrado. Instale antes de continuar."
    exit 1
fi
if ! command -v pip3 >/dev/null 2>&1; then
    echo "[ERRO] pip3 não encontrado. Instale antes de continuar."
    exit 1
fi

echo "[*] Criando ambiente virtual e instalando dependências..."
python3 install_deps.py

echo "[*] Criando link simbólico global para o CLI..."
if [ -L /usr/local/bin/evil-jwt-force ]; then
    sudo rm /usr/local/bin/evil-jwt-force
fi
sudo ln -s "$(pwd)/core/cli.py" /usr/local/bin/evil-jwt-force

echo "[*] Instalação concluída! Você pode rodar 'evil-jwt-force' de qualquer lugar."