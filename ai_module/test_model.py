import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import torch
from model_trainer import JWTModel, TrainingConfig
from tqdm import tqdm

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
        raise

def analyze_token(model: JWTModel, token: str) -> Dict:
    """Analisa um token JWT usando o modelo treinado."""
    try:
        # Extrai features do token
        features = extract_features(token)
        
        # Converte para tensor
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        # Faz predição
        with torch.no_grad():
            prediction = model(features_tensor)
            probability = prediction.item()
        
        return {
            "token": token,
            "is_vulnerable": probability > 0.5,
            "vulnerability_probability": probability,
            "features": features
        }
    except Exception as e:
        logging.error(f"Erro ao analisar token: {e}")
        return {
            "token": token,
            "error": str(e)
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
        return [0] * 8  # Retorna features zeradas em caso de erro

def main():
    """Testa o modelo com tokens de exemplo."""
    parser = argparse.ArgumentParser(description='Testa o modelo de análise de JWT')
    parser.add_argument('--model-path', type=str, default='models/jwt_analyzer.pt',
                      help='Caminho para o modelo treinado')
    parser.add_argument('--input-file', type=str, default='data/jwt_samples/test_tokens.txt',
                      help='Arquivo com tokens para teste')
    parser.add_argument('--output-file', type=str, default='data/jwt_samples/test_results.json',
                      help='Arquivo para salvar resultados')
    args = parser.parse_args()
    
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Carrega o modelo
        logger.info(f"Carregando modelo de {args.model_path}...")
        model = load_model(args.model_path)
        
        # Lê tokens de teste
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
        logger.info(f"\nEstatísticas:")
        logger.info(f"Total de tokens: {total}")
        logger.info(f"Tokens vulneráveis: {vulnerable}")
        logger.info(f"Tokens seguros: {total - vulnerable}")
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        raise

if __name__ == '__main__':
    main() 