# API de IA

## Endpoints

### `POST /api/ai/analyze`
Solicita análise assistida por IA.

**Body:**
```json
{
  "input": "token_jwt_ou_payload",
  "context": "security"
}
```

**Resposta:**
```json
{
  "insights": ["Sugestão 1", "Sugestão 2"],
  "risks": ["Risco 1"]
}
``` 