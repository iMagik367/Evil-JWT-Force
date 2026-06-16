import argparse
import json
import logging
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
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
ALERT_COUNT = Counter(
    'jwt_alert_count_total',
    'Total de alertas gerados',
    ['alert_type']
)

class AlertManager:
    """Gerencia alertas do sistema."""
    
    def __init__(self, smtp_server: str, smtp_port: int, smtp_user: str, smtp_password: str,
                 alert_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.alert_email = alert_email
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, subject: str, message: str):
        """Envia um alerta por email."""
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Alerta enviado: {subject}")
            ALERT_COUNT.labels(alert_type=subject).inc()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta: {e}")
            ALERT_COUNT.labels(alert_type="alert_error").inc()

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('production_alerts.log')
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

def analyze_token(model: JWTModel, token: str, alert_manager: AlertManager) -> Dict:
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
            # Gera alerta para token vulnerável
            alert_manager.send_alert(
                "Token JWT Vulnerável Detectado",
                f"Token ID: {token_id}\n"
                f"Probabilidade: {probability:.2f}\n"
                f"Timestamp: {datetime.now()}"
            )
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
        
        # Alerta se o tempo de processamento for muito alto
        if result["processing_time"] > 2.0:  # Mais de 2 segundos
            alert_manager.send_alert(
                "Tempo de Processamento Alto",
                f"Token ID: {token_id}\n"
                f"Tempo: {result['processing_time']:.2f}s\n"
                f"Timestamp: {datetime.now()}"
            )
        
        return result
        
    except Exception as e:
        logging.error(f"Erro ao analisar token: {e}")
        ERROR_COUNT.inc()
        # Gera alerta para erro
        alert_manager.send_alert(
            "Erro no Processamento de Token",
            f"Token ID: {token_id}\n"
            f"Erro: {str(e)}\n"
            f"Timestamp: {datetime.now()}"
        )
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
    """Executa o modelo em produção com monitoramento e alertas."""
    parser = argparse.ArgumentParser(description='Executa o modelo de análise de JWT em produção com monitoramento e alertas')
    parser.add_argument('--model-path', type=str, default='models/jwt_analyzer.pt',
                      help='Caminho para o modelo treinado')
    parser.add_argument('--input-file', type=str, required=True,
                      help='Arquivo com tokens para análise')
    parser.add_argument('--output-file', type=str, required=True,
                      help='Arquivo para salvar resultados')
    parser.add_argument('--metrics-port', type=int, default=8000,
                      help='Porta para expor métricas Prometheus')
    parser.add_argument('--smtp-server', type=str, required=True,
                      help='Servidor SMTP para envio de alertas')
    parser.add_argument('--smtp-port', type=int, required=True,
                      help='Porta do servidor SMTP')
    parser.add_argument('--smtp-user', type=str, required=True,
                      help='Usuário SMTP')
    parser.add_argument('--smtp-password', type=str, required=True,
                      help='Senha SMTP')
    parser.add_argument('--alert-email', type=str, required=True,
                      help='Email para envio de alertas')
    args = parser.parse_args()
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Inicia servidor de métricas
        prometheus_client.start_http_server(args.metrics_port)
        logger.info(f"Métricas disponíveis em http://localhost:{args.metrics_port}")
        
        # Configura gerenciador de alertas
        alert_manager = AlertManager(
            args.smtp_server,
            args.smtp_port,
            args.smtp_user,
            args.smtp_password,
            args.alert_email
        )
        
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
            result = analyze_token(model, token, alert_manager)
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
        
        # Alerta se houver muitos tokens vulneráveis
        if vulnerable / total > 0.1:  # Mais de 10% vulneráveis
            alert_manager.send_alert(
                "Alta Taxa de Tokens Vulneráveis",
                f"Total de tokens: {total}\n"
                f"Tokens vulneráveis: {vulnerable}\n"
                f"Taxa: {vulnerable/total:.2%}\n"
                f"Timestamp: {datetime.now()}"
            )
        
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
        raise

if __name__ == '__main__':
    main() 