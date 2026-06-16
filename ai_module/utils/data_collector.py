import csv
import os
from ai_module.utils.logger import log_debug

# Caminho para o arquivo CSV de dados de erros
ERROR_DATA_PATH = "ai_module/data/errors.csv"

# Cria o diretório de dados se não existir
os.makedirs("ai_module/data", exist_ok=True)

# Cria o arquivo CSV com cabeçalhos se não existir
def init_error_data_file():
    if not os.path.exists(ERROR_DATA_PATH):
        with open(ERROR_DATA_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ErrorType", "ErrorMessage", "Context", "Timestamp", "SuggestedAction"])
        log_debug(f"Arquivo de dados de erros criado em {ERROR_DATA_PATH}")

# Salva um erro no arquivo CSV
def save_error_data(error_type, error_msg, context, timestamp, suggested_action):
    init_error_data_file()
    with open(ERROR_DATA_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([error_type, error_msg, context, timestamp, suggested_action])
    log_debug(f"Erro salvo no arquivo de dados: {error_type}") 