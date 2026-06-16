# Integração com IA

O sistema utiliza modelos de IA para:
- Análise de padrões de ataque
- Geração de payloads de teste
- Sugestões de mitigação
- Aprendizado contínuo com resultados

## Como funciona
1. O usuário solicita uma análise assistida por IA.
2. O sistema envia os dados para o modelo de IA.
3. O modelo retorna insights, sugestões e possíveis vulnerabilidades.

## Exemplo de uso
```http
POST /api/ai/analyze
Content-Type: application/json

{
  "input": "token_jwt_ou_payload",
  "context": "security"
}
``` 