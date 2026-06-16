from loguru import logger
import os

# Configura o logger para salvar logs em arquivo e exibir no console
logger.add("ai_module/logs/error_log_{time}.log", rotation="500 MB", level="ERROR")
logger.add("ai_module/logs/debug_log_{time}.log", rotation="500 MB", level="DEBUG")

# Função para logar erros com detalhes
def log_error(error_msg, context=""):
    logger.error(f"Erro detectado: {error_msg} | Contexto: {context}")

# Função para logar informações de debug
def log_debug(debug_msg):
    logger.debug(f"Debug: {debug_msg}") 