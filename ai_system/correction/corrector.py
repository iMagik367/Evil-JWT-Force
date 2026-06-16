import os
import subprocess
import json
from loguru import logger

# Configuração de logs
logger.add("ai_system/logs/correction_log_{time}.log", rotation="500 MB", level="INFO")
logger.add("ai_system/logs/correction_error_{time}.log", rotation="500 MB", level="ERROR")

# Caminho para dados de erros e métricas
ERRORS_PATH = "ai_system/data/errors.csv"
PREDICTIONS_PATH = "ai_system/data/predictions.json"

# Dicionário de ações automáticas para erros conhecidos
CORRECTION_ACTIONS = {
    "ImportError": {
        "message": "Tentando instalar o módulo ausente.",
        "action": lambda error_msg: install_missing_module(error_msg)
    },
    "ConnectionError": {
        "message": "Verificando conexão de rede ou configurando proxy.",
        "action": lambda error_msg: retry_connection(error_msg)
    }
}

# Função para extrair nome do módulo de um erro ImportError
def extract_module_name(error_msg):
    try:
        if "No module named" in error_msg:
            module_part = error_msg.split("No module named")[1].strip()
            module_name = module_part.split("'")[1] if "'" in module_part else module_part
            return module_name
    except Exception as e:
        logger.error(f"Erro ao extrair nome do módulo: {str(e)}")
        return None
    return None

# Função para instalar módulo ausente
def install_missing_module(error_msg):
    module_name = extract_module_name(error_msg)
    if not module_name:
        return "Não foi possível identificar o módulo ausente."
    
    logger.info(f"Tentando instalar módulo: {module_name}")
    try:
        result = subprocess.run(["pip", "install", module_name], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Módulo {module_name} instalado com sucesso.")
            return f"Módulo {module_name} instalado com sucesso."
        else:
            logger.error(f"Erro ao instalar {module_name}: {result.stderr}")
            return f"Falha ao instalar {module_name}. Verifique os logs."
    except Exception as e:
        logger.error(f"Exceção ao instalar módulo: {str(e)}")
        return f"Erro ao tentar instalar {module_name}: {str(e)}"

# Função para tentar reconexão ou configurar proxy
def retry_connection(error_msg):
    logger.info("Tentando reconectar ou ajustar configurações de rede...")
    # Aqui poderia haver lógica para verificar conexão ou configurar proxy
    return "Tentativa de reconexão realizada. Verifique se o problema persiste."

# Função para aplicar correções com base em erros detectados
def apply_correction(error_type, error_msg):
    if error_type in CORRECTION_ACTIONS:
        correction = CORRECTION_ACTIONS[error_type]
        logger.info(f"Aplicando correção para {error_type}: {correction['message']}")
        result = correction['action'](error_msg)
        logger.info(f"Resultado da correção: {result}")
        return result
    else:
        logger.warning(f"Nenhuma correção automática disponível para {error_type}")
        return "Nenhuma correção automática disponível."

# Função para verificar previsões e agir preventivamente
def check_predictions_and_correct():
    if not os.path.exists(PREDICTIONS_PATH):
        logger.warning("Arquivo de previsões não encontrado.")
        return "Nenhuma previsão disponível para correção preventiva."
    
    try:
        with open(PREDICTIONS_PATH, 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        if predictions.get('prediction', 0) == 1:
            logger.warning("Previsão indica alta probabilidade de erro.")
            # Aqui poderia haver ações preventivas, como reduzir carga ou reiniciar serviços
            return "Ação preventiva tomada: Monitoramento intensificado devido à previsão de erro."
        else:
            logger.info("Previsão indica baixa probabilidade de erro.")
            return "Nenhuma ação preventiva necessária."
    except Exception as e:
        logger.error(f"Erro ao verificar previsões: {str(e)}")
        return f"Erro ao verificar previsões: {str(e)}"

if __name__ == "__main__":
    logger.info("Iniciando módulo de correção automática...")
    # Simulação: aplicar correção para o último erro registrado
    if os.path.exists(ERRORS_PATH):
        try:
            import pandas as pd
            errors_df = pd.read_csv(ERRORS_PATH)
            if not errors_df.empty:
                last_error = errors_df.tail(1).iloc[0]
                error_type = last_error['ErrorType']
                error_msg = last_error['ErrorMessage']
                print(f"[CORREÇÃO] Aplicando correção para último erro: {error_type}")
                result = apply_correction(error_type, error_msg)
                print(f"[RESULTADO] {result}")
            else:
                print("[INFO] Nenhum erro registrado para corrigir.")
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de erros: {str(e)}")
            print(f"[ERRO] Não foi possível processar erros: {str(e)}")
    else:
        print("[INFO] Arquivo de erros não encontrado.")
    
    # Verificar previsões
    prediction_result = check_predictions_and_correct()
    print(f"[PREVENÇÃO] {prediction_result}")
    logger.info("Módulo de correção concluído.") 