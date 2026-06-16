# Análise de Segurança

O sistema permite análise automatizada de vulnerabilidades, testes de penetração e análise de tokens JWT.

## Funcionalidades
- Análise de tokens JWT
- Testes de penetração automatizados
- Detecção de vulnerabilidades em APIs
- Geração de relatórios de segurança

## Como usar
1. Acesse o painel de análise de segurança.
2. Selecione o tipo de análise (vulnerabilidade, exploit, scan, report).
3. Informe o alvo e os dados necessários.
4. Execute a análise e aguarde o relatório.

## Exemplo de requisição
```http
POST /api/security/analyze
Content-Type: application/json

{
  "target": "https://exemplo.com",
  "type": "scan",
  "data": {}
}
``` 