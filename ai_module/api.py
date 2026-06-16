import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import prometheus_client
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model_trainer import JWTModel
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Métricas Prometheus
TOKENS_PROCESSED = Counter(
    'jwt_tokens_processed_total',
    'Total de tokens JWT processados'
)
TOKENS_VULNERABLE = Counter(
    'jwt_tokens_vulnerable_total',
    'Total de tokens JWT vulneráveis detectados'
)
PROCESSING_TIME = Histogram(
    'jwt_token_processing_seconds',
    'Tempo de processamento por token',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)
MODEL_CONFIDENCE = Gauge(
    'jwt_model_confidence',
    'Confiança do modelo na predição',
    ['token_id']
)
ERROR_COUNT = Counter(
    'jwt_processing_errors_total',
    'Total de erros durante o processamento'
)
API_REQUESTS = Counter(
    'jwt_api_requests_total',
    'Total de requisições à API',
    ['endpoint', 'method']
)
API_ERRORS = Counter(
    'jwt_api_errors_total',
    'Total de erros na API',
    ['endpoint', 'method', 'error_type']
)

# Modelos Pydantic
class TokenAnalysisRequest(BaseModel):
    token: str
    metadata: Optional[Dict] = None

class TokenAnalysisResponse(BaseModel):
    token: str
    is_vulnerable: bool
    vulnerability_probability: float
    features: List[float]
    processing_time: float
    metadata: Optional[Dict] = None

class BatchAnalysisRequest(BaseModel):
    tokens: List[str]
    metadata: Optional[Dict] = None

class BatchAnalysisResponse(BaseModel):
    results: List[TokenAnalysisResponse]
    total_tokens: int
    vulnerable_tokens: int
    processing_time: float
    metadata: Optional[Dict] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str = "1.0.0"
    uptime: float

# Inicializa FastAPI
app = FastAPI(
    title="JWT Security Analyzer API",
    description="API para análise de segurança de tokens JWT usando IA",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura instrumentação Prometheus
Instrumentator().instrument(app).expose(app)

# Variáveis globais
model = None
start_time = time.time()

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api.log')
        ]
    )

def load_model(model_path: str) -> JWTModel:
    """Carrega o modelo treinado."""
    try:
        checkpoint = torch.load(model_path)
        model = JWTModel(input_size=8)  # 8 features
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        return model
    except Exception as e:
        logging.error(f"Erro ao carregar modelo: {e}")
        ERROR_COUNT.inc()
        raise

def analyze_token(token: str) -> Dict:
    """Analisa um token JWT usando o modelo treinado."""
    start_time = time.time()
    token_id = token[:8]  # Usa os primeiros 8 caracteres como ID
    
    try:
        # Extrai features do token
        features = extract_features(token)
        
        # Converte para tensor
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        # Faz predição
        with torch.no_grad():
            prediction = model(features_tensor)
            probability = prediction.item()
        
        # Atualiza métricas
        TOKENS_PROCESSED.inc()
        if probability > 0.5:
            TOKENS_VULNERABLE.inc()
        MODEL_CONFIDENCE.labels(token_id=token_id).set(probability)
        
        result = {
            "token": token,
            "is_vulnerable": probability > 0.5,
            "vulnerability_probability": probability,
            "features": features,
            "processing_time": time.time() - start_time
        }
        
        # Registra tempo de processamento
        PROCESSING_TIME.observe(result["processing_time"])
        
        return result
        
    except Exception as e:
        logging.error(f"Erro ao analisar token: {e}")
        ERROR_COUNT.inc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao analisar token: {str(e)}"
        )

def extract_features(token: str) -> List[float]:
    """Extrai features de um token JWT."""
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        header = jwt.get_unverified_header(token)
        
        features = []
        
        # Features do header
        features.extend([
            1 if header.get('alg') == 'none' else 0,
            1 if 'kid' in header else 0,
            1 if 'jku' in header else 0,
            1 if 'x5u' in header else 0
        ])
        
        # Features do payload
        features.extend([
            1 if 'exp' not in decoded else 0,
            1 if decoded.get('exp', 0) < datetime.now().timestamp() else 0,
            len(decoded) / 10,  # Normalizado
            len(token.split('.')[-1]) / 100  # Tamanho da assinatura normalizado
        ])
        
        return features
    except Exception as e:
        logging.error(f"Erro ao extrair features: {e}")
        ERROR_COUNT.inc()
        raise HTTPException(
            status_code=400,
            detail=f"Token JWT inválido: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da API."""
    global model
    setup_logging()
    try:
        model = load_model("models/jwt_analyzer.pt")
        logging.info("Modelo carregado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao carregar modelo: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint para verificar a saúde da API."""
    API_REQUESTS.labels(endpoint="/health", method="GET").inc()
    try:
        return {
            "status": "healthy" if model is not None else "unhealthy",
            "model_loaded": model is not None,
            "uptime": time.time() - start_time
        }
    except Exception as e:
        API_ERRORS.labels(endpoint="/health", method="GET", error_type="internal_error").inc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar saúde: {str(e)}"
        )

@app.post("/analyze", response_model=TokenAnalysisResponse)
async def analyze_single_token(request: TokenAnalysisRequest):
    """Endpoint para analisar um único token JWT."""
    API_REQUESTS.labels(endpoint="/analyze", method="POST").inc()
    try:
        result = analyze_token(request.token)
        result["metadata"] = request.metadata
        return result
    except HTTPException as e:
        API_ERRORS.labels(endpoint="/analyze", method="POST", error_type="http_error").inc()
        raise
    except Exception as e:
        API_ERRORS.labels(endpoint="/analyze", method="POST", error_type="internal_error").inc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@app.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch_tokens(request: BatchAnalysisRequest):
    """Endpoint para analisar múltiplos tokens JWT."""
    API_REQUESTS.labels(endpoint="/analyze/batch", method="POST").inc()
    try:
        start_time = time.time()
        results = []
        
        for token in request.tokens:
            result = analyze_token(token)
            result["metadata"] = request.metadata
            results.append(result)
        
        return {
            "results": results,
            "total_tokens": len(results),
            "vulnerable_tokens": sum(1 for r in results if r["is_vulnerable"]),
            "processing_time": time.time() - start_time,
            "metadata": request.metadata
        }
    except HTTPException as e:
        API_ERRORS.labels(endpoint="/analyze/batch", method="POST", error_type="http_error").inc()
        raise
    except Exception as e:
        API_ERRORS.labels(endpoint="/analyze/batch", method="POST", error_type="internal_error").inc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 