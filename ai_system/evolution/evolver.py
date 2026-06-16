import os
import pandas as pd
import re
from loguru import logger

# Configuração de logs
logger.add("ai_system/logs/evolution_log_{time}.log", rotation="500 MB", level="INFO")
logger.add("ai_system/logs/evolution_error_{time}.log", rotation="500 MB", level="ERROR")

# Caminhos para dados
METRICS_PATH = "ai_system/data/metrics.csv"
ERRORS_PATH = "ai_system/data/errors.csv"
SUGGESTIONS_PATH = "ai_system/evolution/suggestions.txt"

# Cria diretórios se não existirem
os.makedirs("ai_system/logs", exist_ok=True)
os.makedirs("ai_system/evolution", exist_ok=True)

# Função para analisar performance e erros para sugerir melhorias
def analyze_for_improvements():
    suggestions = []
    
    # Analisar métricas de performance
    if os.path.exists(METRICS_PATH):
        try:
            metrics_df = pd.read_csv(METRICS_PATH)
            if not metrics_df.empty:
                avg_cpu = metrics_df['CPU_Percent'].mean()
                avg_memory = metrics_df['Memory_Usage_MB'].mean()
                max_cpu = metrics_df['CPU_Percent'].max()
                max_memory = metrics_df['Memory_Usage_MB'].max()
                
                logger.info(f"Análise de performance: CPU média={avg_cpu}%, Memória média={avg_memory}MB")
                if avg_cpu > 80 or max_cpu > 90:
                    suggestions.append("[PERFORMANCE] Uso de CPU elevado detectado. Considere otimizar loops ou usar multiprocessing.")
                    logger.warning("Uso de CPU elevado detectado.")
                if avg_memory > 500 or max_memory > 800:
                    suggestions.append("[PERFORMANCE] Uso de memória elevado detectado. Verifique vazamentos de memória ou otimize estruturas de dados.")
                    logger.warning("Uso de memória elevado detectado.")
        except Exception as e:
            logger.error(f"Erro ao analisar métricas: {str(e)}")
    else:
        logger.warning("Arquivo de métricas não encontrado.")
    
    # Analisar erros frequentes
    if os.path.exists(ERRORS_PATH):
        try:
            errors_df = pd.read_csv(ERRORS_PATH)
            if not errors_df.empty:
                error_counts = errors_df['ErrorType'].value_counts()
                logger.info(f"Análise de erros: {error_counts.to_dict()}")
                for error_type, count in error_counts.items():
                    if count > 5:  # Threshold para erros frequentes
                        if error_type == "ImportError":
                            suggestions.append(f"[ERRO FREQUENTE] {error_type} detectado {count} vezes. Considere incluir dependências em um arquivo requirements.txt.")
                        elif error_type == "ConnectionError":
                            suggestions.append(f"[ERRO FREQUENTE] {error_type} detectado {count} vezes. Considere implementar retry ou fallback para conexões.")
                        else:
                            suggestions.append(f"[ERRO FREQUENTE] {error_type} detectado {count} vezes. Revise o código para tratar este erro.")
                        logger.warning(f"Erro frequente detectado: {error_type} ({count} vezes)")
        except Exception as e:
            logger.error(f"Erro ao analisar erros: {str(e)}")
    else:
        logger.warning("Arquivo de erros não encontrado.")
    
    return suggestions

# Função para salvar sugestões em arquivo
def save_suggestions(suggestions):
    try:
        with open(SUGGESTIONS_PATH, mode='w', encoding='utf-8') as f:
            for suggestion in suggestions:
                f.write(suggestion + "\n")
        logger.info(f"Sugestões salvas em {SUGGESTIONS_PATH}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar sugestões: {str(e)}")
        return False

# Função para implementar melhorias automaticamente (exemplo simplificado)
def implement_improvement(suggestion):
    logger.info(f"Tentando implementar melhoria: {suggestion}")
    # Aqui poderia haver lógica para modificar código, como adicionar retries ou otimizar loops
    # Por enquanto, apenas registramos a tentativa
    return f"Melhoria implementada (simulação): {suggestion}"

if __name__ == "__main__":
    logger.info("Iniciando módulo de evolução do código...")
    suggestions = analyze_for_improvements()
    if suggestions:
        print("[SUGESTÕES DE MELHORIA]")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        save_suggestions(suggestions)
        # Simulação: implementar a primeira sugestão
        if len(suggestions) > 0:
            result = implement_improvement(suggestions[0])
            print(f"[IMPLEMENTAÇÃO] {result}")
    else:
        print("[INFO] Nenhuma sugestão de melhoria no momento.")
    logger.info("Módulo de evolução concluído.") 