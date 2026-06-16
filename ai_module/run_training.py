import argparse
import logging
import sys
from pathlib import Path

from generate_training_data import main as generate_data
from train_model import main as train_model

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('training.log')
        ]
    )

def main():
    """Executa o pipeline completo de treinamento."""
    parser = argparse.ArgumentParser(description='Pipeline de treinamento do modelo JWT')
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
        
        # 1. Gera dados de treinamento
        if not args.skip_data_generation:
            logger.info("Iniciando geração de dados...")
            generate_data()
        else:
            logger.info("Pulando geração de dados...")
        
        # 2. Treina o modelo
        logger.info("Iniciando treinamento do modelo...")
        train_model()
        
        logger.info("Pipeline de treinamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o pipeline de treinamento: {e}")
        raise

if __name__ == '__main__':
    main() 