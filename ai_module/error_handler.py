from ai_module.utils.logger import log_error, log_debug
import traceback
import sys
from datetime import datetime
from ai_module.utils.data_collector import save_error_data

# Dicionário de erros conhecidos e suas correções
KNOWN_ERRORS = {
    "ImportError": {
        "message": "Módulo não encontrado. Verifique se a biblioteca está instalada.",
        "action": "pip install <module_name>"
    },
    "ConnectionError": {
        "message": "Erro de conexão. Verifique sua internet ou o endpoint.",
        "action": "Tente novamente ou configure um proxy."
    }
}

# Função para capturar e analisar erros
def handle_error(exception, context=""):
    error_type = type(exception).__name__
    error_msg = str(exception)
    log_error(error_msg, context)
    log_debug(f"Tipo de erro: {error_type}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Sugere uma correção baseada no tipo de erro
    if error_type in KNOWN_ERRORS:
        correction = KNOWN_ERRORS[error_type]
        log_debug(f"Correção sugerida: {correction['message']}")
        suggested_action = correction['action']
        save_error_data(error_type, error_msg, context, timestamp, suggested_action)
        return correction['message'], suggested_action
    else:
        log_debug("Erro desconhecido, sem correção automática.")
        suggested_action = "Nenhuma ação automática disponível."
        save_error_data(error_type, error_msg, context, timestamp, suggested_action)
        return "Erro desconhecido. Verifique os logs para mais detalhes.", suggested_action

# Função para executar um bloco de código com tratamento de erros
def run_with_error_handling(func, *args, context="", **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        suggestion, action = handle_error(e, context)
        print(f"[ERRO] {str(e)}")
        print(f"[SUGESTÃO] {suggestion}")
        print(f"[AÇÃO] {action}")
        return None 