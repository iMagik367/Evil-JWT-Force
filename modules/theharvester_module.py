import subprocess
import os
import json
import tempfile
import shutil


def run_theharvester(target: str, limit: int, log_callback):
    """
    Run theHarvester tool for the given target with a result limit, parsing JSON output.
    """
    log_callback(f"Executando theHarvester para {target} com limite {limit}")
    temp_dir = tempfile.mkdtemp()
    base_path = os.path.join(temp_dir, 'harv')
    cmd = ['theHarvester', '-d', target, '-l', str(limit), '-f', base_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            log_callback(f"Erro theHarvester: {proc.stderr.strip()}")
            return {}
        json_path = base_path + '.json'
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            log_callback(f"Resultados theHarvester carregados de {json_path}")
            return data
        else:
            log_callback("Arquivo JSON de saída do theHarvester não encontrado.")
            return {}
    except FileNotFoundError:
        log_callback("Comando 'theHarvester' não encontrado. Certifique-se de que o theHarvester está instalado no PATH.")
        return {}
    except Exception as e:
        log_callback(f"Exceção ao executar theHarvester: {e}")
        return {}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True) 