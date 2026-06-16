import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import prometheus_client
import torch
from model_trainer import JWTModel
from prometheus_client import Counter, Gauge, Histogram
from tqdm import tqdm

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

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('production_monitored.log')
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

def analyze_token(model: JWTModel, token: str) -> Dict:
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
        return {
            "token": token,
            "error": str(e),
            "processing_time": time.time() - start_time
        }

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
        return [0] * 8  # Retorna features zeradas em caso de erro

def main():
    """Executa o modelo em produção com monitoramento."""
    parser = argparse.ArgumentParser(description='Executa o modelo de análise de JWT em produção com monitoramento')
    parser.add_argument('--model-path', type=str, default='models/jwt_analyzer.pt',
                      help='Caminho para o modelo treinado')
    parser.add_argument('--input-file', type=str, required=True,
                      help='Arquivo com tokens para análise')
    parser.add_argument('--output-file', type=str, required=True,
                      help='Arquivo para salvar resultados')
    parser.add_argument('--metrics-port', type=int, default=8000,
                      help='Porta para expor métricas Prometheus')
    args = parser.parse_args()
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Inicia servidor de métricas
        prometheus_client.start_http_server(args.metrics_port)
        logger.info(f"Métricas disponíveis em http://localhost:{args.metrics_port}")
        
        # Carrega o modelo
        logger.info(f"Carregando modelo de {args.model_path}...")
        model = load_model(args.model_path)
        
        # Lê tokens
        logger.info(f"Lendo tokens de {args.input_file}...")
        with open(args.input_file, 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
        
        # Analisa cada token
        logger.info("Analisando tokens...")
        results = []
        for token in tqdm(tokens):
            result = analyze_token(model, token)
            results.append(result)
        
        # Salva resultados
        logger.info(f"Salvando resultados em {args.output_file}...")
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Mostra estatísticas
        total = len(results)
        vulnerable = sum(1 for r in results if r.get('is_vulnerable', False))
        errors = sum(1 for r in results if 'error' in r)
        avg_time = sum(r.get('processing_time', 0) for r in results) / total
        
        logger.info(f"\nEstatísticas:")
        logger.info(f"Total de tokens: {total}")
        logger.info(f"Tokens vulneráveis: {vulnerable}")
        logger.info(f"Tokens seguros: {total - vulnerable}")
        logger.info(f"Erros: {errors}")
        logger.info(f"Tempo médio de processamento: {avg_time:.3f}s")
        
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        raise

if __name__ == '__main__':
    main() 