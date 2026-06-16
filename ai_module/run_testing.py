import argparse
import logging
import sys
from pathlib import Path

from generate_test_data import main as generate_test_data
from test_model import main as test_model

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('testing.log')
        ]
    )

def main():
    """Executa o pipeline completo de teste."""
    parser = argparse.ArgumentParser(description='Pipeline de teste do modelo JWT')
    parser.add_argument('--model-path', type=str, default='models/jwt_analyzer.pt',
                      help='Caminho para o modelo treinado')
    parser.add_argument('--data-dir', type=str, default='data/jwt_samples',
                      help='Diretório para armazenar os dados')
    parser.add_argument('--skip-data-generation', action='store_true',
                      help='Pula a geração de dados se já existirem')
    args = parser.parse_args()
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Cria diretórios necessários
        data_dir = Path(args.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Gera dados de teste
        if not args.skip_data_generation:
            logger.info("Iniciando geração de dados de teste...")
            generate_test_data()
        else:
            logger.info("Pulando geração de dados de teste...")
        
        # 2. Testa o modelo
        logger.info("Iniciando teste do modelo...")
        test_model()
        
        logger.info("Pipeline de teste concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o pipeline de teste: {e}")
        raise

if __name__ == '__main__':
    main() 