#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Limpando ambiente..."

# Para os serviços
echo -e "\n${GREEN}Parando serviços...${NC}"
docker-compose -f docker-compose.prod.yml down

# Remove containers
echo -e "\n${GREEN}Removendo containers...${NC}"
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Remove imagens
echo -e "\n${GREEN}Removendo imagens...${NC}"
docker rmi -f $(docker images -q) 2>/dev/null || true

# Remove volumes
echo -e "\n${GREEN}Removendo volumes...${NC}"
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Remove diretórios
echo -e "\n${GREEN}Removendo diretórios...${NC}"
rm -rf models logs data grafana/data

# Remove arquivos Python compilados
echo -e "\n${GREEN}Removendo arquivos Python compilados...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Remove arquivos de cache
echo -e "\n${GREEN}Removendo arquivos de cache...${NC}"
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov
rm -rf .mypy_cache
rm -rf .ruff_cache

# Remove arquivos de log
echo -e "\n${GREEN}Removendo arquivos de log...${NC}"
rm -f *.log
rm -f logs/*.log

# Remove arquivos de teste
echo -e "\n${GREEN}Removendo arquivos de teste...${NC}"
rm -f test_*.py
rm -f *_test.py
rm -f *_tests.py

# Remove arquivos temporários
echo -e "\n${GREEN}Removendo arquivos temporários...${NC}"
rm -f *.tmp
rm -f *.temp
rm -f *.swp
rm -f *.swo

echo -e "\n${GREEN}Ambiente limpo!${NC}" 