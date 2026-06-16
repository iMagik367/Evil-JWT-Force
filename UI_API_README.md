# Evil-Force-JWT AI Interface and API

This document describes the AI Interface and RESTful API components of the Evil-Force-JWT tool.

## AI Interface

The AI Interface provides a graphical user interface for interacting with the AI-driven JWT security testing framework.

### Features

- **Dashboard**: Overview of the AI system and quick access to common functions
- **Token Analysis**: Analyze JWT tokens, identify vulnerabilities, and get attack recommendations
- **Target Scan**: Scan websites for JWT tokens and security vulnerabilities
- **Attack Simulation**: Simulate various attacks against JWT implementations
- **Settings**: Configure AI behavior and preferences

### Running the AI Interface

#### Windows

```
run_ai_interface.bat
```

#### Linux/Mac

```
chmod +x run_ai_interface.sh
./run_ai_interface.sh
```

## REST API

The REST API provides programmatic access to the AI-driven JWT security testing framework, allowing integration with other security tools.

### API Endpoints

- `GET /api/health` - Check API health and status
- `POST /api/analyze` - Analyze a JWT token
- `POST /api/scan` - Scan a target URL for JWT tokens
- `POST /api/bruteforce` - Bruteforce a JWT token
- `POST /api/fuzz` - Generate mutations for a JWT token
- `POST /api/predict` - Predict potential secrets for a JWT token

### Running the API Server

#### Windows

```
run_api.bat [port]
```

#### Linux/Mac

```
chmod +x run_api.sh
./run_api.sh [port]
```

Default port is 5000 if not specified.

### Example API Usage

#### Analyze a token

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
  }'
```

#### Scan a target

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - tkinter (for GUI)
  - PIL/Pillow (for GUI)
  - Flask, Flask-CORS (for API)
  - Other dependencies from the Evil-Force-JWT project

## Integration with Other Tools

The REST API allows for easy integration with other security tools and frameworks. You can:

1. Use the `/api/analyze` endpoint to analyze tokens found by other tools
2. Use the `/api/scan` endpoint as part of an automated security testing pipeline
3. Use the `/api/bruteforce` endpoint for enhanced token cracking capabilities
4. Use the `/api/fuzz` endpoint to generate intelligent mutations for fuzzing tests
5. Use the `/api/predict` endpoint to generate wordlists for other cracking tools

## Troubleshooting

- If the GUI doesn't start, check if tkinter and PIL are installed
- If the API server fails to start, check if Flask and Flask-CORS are installed
- For other issues, check the logs in the `logs` directory 