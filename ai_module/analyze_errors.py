import pandas as pd
import os
from ai_module.utils.logger import log_debug
from pentestgpt import PentestGPT

# Caminho para o arquivo CSV de dados de erros
ERROR_DATA_PATH = "ai_module/data/errors.csv"

def analyze_errors():
    if not os.path.exists(ERROR_DATA_PATH):
        print("[INFO] Nenhum dado de erro encontrado para análise.")
        log_debug("Nenhum arquivo de dados de erros encontrado para análise.")
        return
    
    # Lê o arquivo CSV
    df = pd.read_csv(ERROR_DATA_PATH)
    if df.empty:
        print("[INFO] Arquivo de erros está vazio.")
        log_debug("Arquivo de dados de erros está vazio.")
        return
    
    # Mostra estatísticas básicas
    print("[ANÁLISE DE ERROS]")
    print(f"Total de erros registrados: {len(df)}")
    print("\nTipos de erro mais comuns:")
    error_counts = df['ErrorType'].value_counts()
    print(error_counts)
    log_debug(f"Análise de erros concluída. Total de erros: {len(df)}")
    
    # Sugestões de ações frequentes
    print("\nAções sugeridas mais comuns:")
    action_counts = df['SuggestedAction'].value_counts()
    print(action_counts)
    log_debug("Ações sugeridas analisadas.")

if __name__ == "__main__":
    log_debug("Iniciando análise de erros.")
    analyze_errors()
    log_debug("Análise de erros finalizada.")


class PentestGPTAdapter:
    def __init__(self):
        self.gpt = GPT3Analyzer(api_key=os.getenv('OPENAI_KEY'))
    
    def analyze_vulnerabilities(self, tool_results):
        analysis_prompt = f"Analise estes resultados de ferramentas JWT:\n{tool_results}\n\nListe as vulnerabilidades críticas e sugira ataques combinados:"
        return self.gpt.generate_analysis(analysis_prompt)


class AIVulnerabilityAnalyzer:
    def __init__(self):
        self.gpt = PentestGPT(api_key='SUA_CHAVE_API')
        
    def analyze_results(self, jwt_data):
        """Usa PentestGPT para análise contextual"""
        prompt = f"Analise estas vulnerabilidades JWT: {jwt_data}"
        return self.gpt.generate_attack_plan(prompt)