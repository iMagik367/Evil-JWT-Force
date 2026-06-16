import argparse
import logging
from pathlib import Path

from data_collector import JWTDataCollector
from enhanced_trainer import EnhancedJWTModelTrainer, TrainingConfig
from utils.metrics import compute_metrics, format_metrics
from ai_module.vulnerability_annotator import JWTAnnotator

def setup_logging():
    """Configura o logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Pipeline principal de treinamento."""
    parser = argparse.ArgumentParser(description='Treina o modelo de análise de JWT')
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
    args = parser.parse_args()
    
    # Configura logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 1. Coleta de dados
        logger.info("Iniciando coleta de dados...")
        collector = JWTDataCollector(args.data_dir)
        
        # Exemplo: coletar de um arquivo
        samples = collector.collect_from_file('data/raw_tokens.txt')
        collector.save_samples(samples, 'raw_samples.json')
        
        # 2. Anotação de vulnerabilidades
        logger.info("Iniciando anotação de vulnerabilidades...")
        annotator = JWTAnnotator(args.data_dir)
        annotator.annotate_samples('raw_samples.json', 'annotated_samples.json')
        
        # 3. Treinamento do modelo
        logger.info("Iniciando treinamento do modelo...")
        config = TrainingConfig(
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            epochs=args.epochs,
            model_save_path=str(Path(args.model_dir) / 'jwt_analyzer.pt')
        )
        
        trainer = EnhancedJWTModelTrainer(config)
        train_loader, val_loader, test_loader = trainer.prepare_data(
            str(Path(args.data_dir) / 'annotated_samples.json')
        )
        
        # Treina com validação cruzada
        logger.info("Iniciando treinamento com validação cruzada...")
        cv_metrics = trainer.train_with_cross_validation(train_loader, val_loader, k_folds=5)
        logger.info(f"Métricas médias da validação cruzada:\n{format_metrics(cv_metrics)}")
        
        # Avalia o modelo no conjunto de teste
        test_metrics = trainer.evaluate(test_loader)
        logger.info(f"Métricas de teste:\n{format_metrics(test_metrics)}")
        
        logger.info("Pipeline de treinamento concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o pipeline de treinamento: {e}")
        raise

if __name__ == '__main__':
    main() 