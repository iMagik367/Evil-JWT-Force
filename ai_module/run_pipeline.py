import argparse
import logging
import sys
from pathlib import Path

from run_training import main as run_training
from run_testing import main as run_testing

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )

def main():
    """Executa o pipeline completo de treinamento e teste."""
    parser = argparse.ArgumentParser(description='Pipeline completo de treinamento e teste do modelo JWT')
    parser.add_argument('--data-dir', type=str, default='data/jwt_samples',
                      help='Diretório para armazenar os dados')
    parser.add_argument('--model-dir', type=str, default='models',
                      help='Diretório para salvar o modelo')
    parser.add_argument('--epochs', type=int, default=10,
                      help='Número de épocas de treinamento')
    parser.add_argument('--batch-size', type=int, default=32,
                      help='Tamanho do batch')
    parser.add_argument('--learning-rate', type=float, default=0.001,
                      help='Taxa de aprendizado')
    parser.add_argument('--skip-data-generation', action='store_true',
                      help='Pula a geração de dados se já existirem')
    args = parser.parse_args()
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Cria diretórios necessários
        data_dir = Path(args.data_dir)
        model_dir = Path(args.model_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Treina o modelo
        logger.info("Iniciando pipeline de treinamento...")
        run_training()
        
        # 2. Testa o modelo
        logger.info("Iniciando pipeline de teste...")
        run_testing()
        
        logger.info("Pipeline completo concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o pipeline: {e}")
        raise

if __name__ == '__main__':
    main() 