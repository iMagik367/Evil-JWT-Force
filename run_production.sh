#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Iniciando ambiente de produção..."

# Cria diretórios necessários
mkdir -p models logs grafana/data grafana/provisioning/dashboards grafana/provisioning/datasources

# Copia arquivos de configuração do Grafana
echo -e "\n${GREEN}Configurando Grafana...${NC}"
cp grafana/dashboards/jwt-analyzer.json grafana/provisioning/dashboards/
cp grafana/provisioning/dashboards/jwt-analyzer.yaml grafana/provisioning/dashboards/
cp grafana/provisioning/datasources/prometheus.yaml grafana/provisioning/datasources/

# Inicia os serviços
echo -e "\n${GREEN}Iniciando serviços...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Aguarda os serviços iniciarem
echo -e "\n${GREEN}Aguardando serviços iniciarem...${NC}"
sleep 10

# Verifica se os serviços estão rodando
echo -e "\n${GREEN}Verificando status dos serviços...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Exibe URLs dos serviços
echo -e "\n${GREEN}Serviços disponíveis:${NC}"
echo "- API: http://localhost:8000"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin)"

# Exibe comandos úteis
echo -e "\n${GREEN}Comandos úteis:${NC}"
echo "- Ver logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "- Parar serviços: docker-compose -f docker-compose.prod.yml down"
echo "- Testar API: python test_api.py"
echo "- Testar carga: python load_test.py"

echo -e "\n${GREEN}Ambiente de produção iniciado!${NC}" 