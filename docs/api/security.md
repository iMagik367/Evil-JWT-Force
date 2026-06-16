# API de Segurança

## Endpoints

### `POST /api/security/analyze`
Executa análise de segurança automatizada.

**Body:**
```json
{
  "target": "https://exemplo.com",
  "type": "scan",
  "data": {}
}
```

**Resposta:**
```json
{
  "result": "Relatório de análise..."
}
```

### `GET /api/security/reports`
Lista relatórios de segurança disponíveis.

### `GET /api/security/report/{id}`
Obtém detalhes de um relatório específico. 