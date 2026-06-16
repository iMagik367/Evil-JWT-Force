#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Parando ambiente de produção..."

# Para os serviços
echo -e "\n${GREEN}Parando serviços...${NC}"
docker-compose -f docker-compose.prod.yml down

# Remove volumes
echo -e "\n${GREEN}Removendo volumes...${NC}"
docker volume rm jwt-analyzer_prometheus_data jwt-analyzer_grafana_data

# Remove diretórios temporários
echo -e "\n${GREEN}Removendo diretórios temporários...${NC}"
rm -rf grafana/data

echo -e "\n${GREEN}Ambiente de produção parado!${NC}" 