import sys
import os
import time
import psutil
import threading
import json
from datetime import datetime
from loguru import logger

# Configuração de logs
logger.add("ai_system/logs/monitor_log_{time}.log", rotation="500 MB", level="INFO")
logger.add("ai_system/logs/monitor_error_{time}.log", rotation="500 MB", level="ERROR")

# Caminho para salvar dados de monitoramento
DATA_PATH = "ai_system/data/monitoring_data.json"
METRICS_PATH = "ai_system/data/metrics.csv"

# Cria diretórios se não existirem
os.makedirs("ai_system/logs", exist_ok=True)
os.makedirs("ai_system/data", exist_ok=True)

# Inicializa arquivo de métricas CSV
def init_metrics_file():
    if not os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, mode='w', encoding='utf-8') as f:
            f.write("Timestamp,CPU_Percent,Memory_Usage_MB,Process_ID\n")
        logger.info(f"Arquivo de métricas criado em {METRICS_PATH}")

# Função para coletar métricas do sistema
def collect_metrics(process_id):
    init_metrics_file()
    process = psutil.Process(process_id)
    cpu_percent = process.cpu_percent(interval=1)
    memory_info = process.memory_info()
    memory_usage_mb = memory_info.rss / 1024 / 1024  # Convertendo para MB
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(METRICS_PATH, mode='a', encoding='utf-8') as f:
        f.write(f"{timestamp},{cpu_percent},{memory_usage_mb},{process_id}\n")
    logger.info(f"Métricas coletadas: CPU={cpu_percent}%, Memória={memory_usage_mb}MB, PID={process_id}")
    return {"timestamp": timestamp, "cpu_percent": cpu_percent, "memory_usage_mb": memory_usage_mb, "pid": process_id}

# Função para monitorar erros na saída padrão e erro padrão
def monitor_output():
    logger.info("Iniciando monitoramento de saída e erros...")
    errors_detected = []
    while True:
        try:
            line = sys.stdin.readline()
            if line:
                logger.info(f"Saída detectada: {line.strip()}")
                if "error" in line.lower() or "exception" in line.lower():
                    errors_detected.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "message": line.strip()})
                    logger.error(f"Erro detectado na saída: {line.strip()}")
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Erro no monitoramento de saída: {str(e)}")
            time.sleep(1)

# Função principal de monitoramento
def start_monitoring(target_pid=None):
    if target_pid is None:
        target_pid = os.getpid()
    logger.info(f"Iniciando monitoramento para PID {target_pid}")
    
    # Thread para monitoramento de métricas
    def metrics_thread():
        while True:
            try:
                metrics = collect_metrics(target_pid)
                with open(DATA_PATH, mode='a', encoding='utf-8') as f:
                    json.dump(metrics, f)
                    f.write("\n")
                time.sleep(5)  # Coleta a cada 5 segundos
            except Exception as e:
                logger.error(f"Erro na coleta de métricas: {str(e)}")
                time.sleep(10)
    
    # Inicia threads
    metrics_t = threading.Thread(target=metrics_thread, daemon=True)
    metrics_t.start()
    
    logger.info("Monitoramento iniciado. Pressione Ctrl+C para parar.")
    try:
        metrics_t.join()
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário.")

if __name__ == "__main__":
    start_monitoring() 