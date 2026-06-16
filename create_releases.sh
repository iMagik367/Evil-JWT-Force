#!/bin/bash

echo "==========================================="
echo "  Evil JWT Force - Criação de Releases"
echo "==========================================="
echo ""

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado. Por favor, instale o Python 3.8 ou superior."
    exit 1
fi

# Verificar se o PyInstaller está instalado
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "Instalando PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao instalar PyInstaller."
        exit 1
    fi
fi

# Instalar dependências
echo "Instalando dependências..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "AVISO: Algumas dependências podem não ter sido instaladas corretamente."
fi

# Criar diretório para releases se não existir
mkdir -p releases

# Executar o script de build
echo "Criando executável..."
python3 build_executables.py
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao criar o executável."
    exit 1
fi

# Identificar o sistema operacional
OS_NAME=$(uname -s)
if [ "$OS_NAME" == "Darwin" ]; then
    # macOS
    echo "Criando pacote para macOS..."
    cd dist
    tar -czvf ../releases/Evil_JWT_Force_macOS.tar.gz Evil_JWT_Force README.md MANUAL.txt
    cd ..
    echo "Pacote criado: releases/Evil_JWT_Force_macOS.tar.gz"
else
    # Linux
    echo "Criando pacote para Linux..."
    cd dist
    tar -czvf ../releases/Evil_JWT_Force_Linux.tar.gz Evil_JWT_Force README.md MANUAL.txt
    cd ..
    echo "Pacote criado: releases/Evil_JWT_Force_Linux.tar.gz"
fi

echo ""
echo "==========================================="
echo "  Release criada com sucesso!"
echo "==========================================="

exit 0 