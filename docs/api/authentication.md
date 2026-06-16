# API de Autenticação

## Endpoints

### `POST /api/auth/login`
Autentica o usuário e retorna um token JWT.

**Body:**
```json
{
  "username": "usuario",
  "password": "senha"
}
```

**Resposta:**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

### `POST /api/auth/logout`
Invalida o token JWT atual.

### `POST /api/auth/refresh`
Gera um novo token de acesso a partir de um refresh token. 