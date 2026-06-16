# Monitoramento e Alertas

## Métricas Principais
- CPU, Memória, Disco
- Latência de requisições
- Taxa de erros
- Uso de recursos por container
- Tempo de resposta da API

## Ferramentas
- Prometheus para coleta de métricas
- Grafana para visualização
- AlertManager para notificações

## Alertas Configurados
- CPU > 80% por 5 minutos
- Memória > 90% por 5 minutos
- Latência > 1s por 1 minuto
- Taxa de erro > 5% por 5 minutos
- Container down

## Como verificar
1. Acesse o dashboard do Grafana
2. Verifique os painéis relevantes
3. Analise os alertas ativos
4. Consulte o histórico de métricas

## Exemplos de Queries Prometheus
```promql
# CPU Usage
rate(process_cpu_seconds_total[5m])

# Memory Usage
process_resident_memory_bytes

# Request Latency
rate(http_request_duration_seconds_sum[5m])
``` 