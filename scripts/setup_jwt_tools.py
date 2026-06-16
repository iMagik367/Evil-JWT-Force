#!/usr/bin/env python3
"""
Script para configurar ferramentas externas de análise e cracking de JWT
"""

import os
import sys
import subprocess
import logging
import shutil
import platform
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("setup_jwt_tools")

# Diretório para ferramentas externas
EXTERNAL_DIR = Path(__file__).resolve().parent.parent / "external"

# Lista de ferramentas com URLs e requisitos
TOOLS = {
    "jwt_tool": {
        "url": "https://github.com/ticarpi/jwt_tool",
        "requirements": ["pycryptodomex", "termcolor", "cprint"],
        "setup": None,
        "type": "python"
    },
    "jwtXploiter": {
        "url": "https://github.com/DontPanicO/jwtXploiter",
        "requirements": ["pyjwt", "pycryptodomex", "requests", "argparse"],
        "setup": "pip install -e .",
        "type": "python"
    },
    "jwt-hack": {
        "url": "https://github.com/hahwul/jwt-hack",
        "requirements": [],
        "setup": None,
        "type": "go"
    },
    "jwt-cracker": {
        "url": "https://github.com/lmammino/jwt-cracker",
        "requirements": [],
        "setup": "npm install",
        "type": "node"
    },
    "jwtcat": {
        "url": "https://github.com/aress31/jwtcat",
        "requirements": ["pyjwt", "pycryptodomex", "requests", "tqdm"],
        "setup": None,
        "type": "python"
    },
    "c-jwt-cracker": {
        "url": "https://github.com/brendan-rius/c-jwt-cracker",
        "requirements": [],
        "setup": "make",
        "type": "c"
    },
    "gojwtcrack": {
        "url": "https://github.com/haxrob/gojwtcrack",
        "requirements": [],
        "setup": None,
        "type": "go"
    },
    "distributed-jwt-cracker": {
        "url": "https://github.com/lmammino/distributed-jwt-cracker",
        "requirements": [],
        "setup": "npm install",
        "type": "node"
    },
    "jwt-secret": {
        "url": "https://github.com/timhudson/jwt-secret",
        "requirements": [],
        "setup": "npm install",
        "type": "node"
    }
}

def check_prerequisites():
    """Verifica se os requisitos básicos estão instalados"""
    prerequisites = {
        "git": "Necessário para clonar repositórios.",
        "python": "Necessário para ferramentas Python.",
        "pip": "Necessário para instalar dependências Python.",
        "npm": "Necessário para ferramentas Node.js.",
        "go": "Necessário para ferramentas Go.",
        "make": "Necessário para compilar ferramentas C."
    }
    
    missing = []
    available_prereqs = {}
    
    for cmd, desc in prerequisites.items():
        if shutil.which(cmd):
            available_prereqs[cmd] = True
        else:
            available_prereqs[cmd] = False
            missing.append(f"{cmd}: {desc}")
    
    if missing:
        logger.warning("Alguns pré-requisitos estão ausentes:")
        for item in missing:
            logger.warning(f"  - {item}")
        logger.warning("As ferramentas que dependem desses pré-requisitos serão ignoradas.")
    
    return available_prereqs

def run_command(cmd, cwd=None, shell=False):
    """Executa um comando no shell e retorna o resultado"""
    try:
        logger.info(f"Executando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            shell=shell, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Comando falhou: {e}")
        logger.error(f"Saída: {e.stdout}")
        logger.error(f"Erro: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        logger.error(f"Erro ao executar comando: {e}")
        return False, str(e)

def setup_tool(name, info, available_prereqs):
    """Configura uma ferramenta específica"""
    tool_dir = EXTERNAL_DIR / name
    
    # Verifica se os pré-requisitos para esta ferramenta estão disponíveis
    if info["type"] == "go" and not available_prereqs.get("go", False):
        logger.warning(f"Pulando {name} porque Go não está disponível")
        return False
    
    if info["type"] == "c" and not available_prereqs.get("make", False):
        logger.warning(f"Pulando {name} porque make não está disponível")
        return False
    
    if info["type"] == "node" and not available_prereqs.get("npm", False):
        logger.warning(f"Pulando {name} porque npm não está disponível")
        return False
    
    if tool_dir.exists():
        logger.info(f"Diretório {name} já existe. Removendo...")
        shutil.rmtree(tool_dir)
    
    # Clone do repositório
    success, output = run_command(
        ["git", "clone", info["url"], str(tool_dir)]
    )
    if not success:
        return False
    
    # Instalação de dependências Python
    if info["requirements"]:
        success, output = run_command(
            [sys.executable, "-m", "pip", "install", *info["requirements"]]
        )
        if not success:
            return False
    
    # Comando de setup adicional
    if info["setup"]:
        if info["type"] == "python":
            success, output = run_command(
                info["setup"], 
                cwd=str(tool_dir),
                shell=True
            )
        else:
            success, output = run_command(
                info["setup"], 
                cwd=str(tool_dir),
                shell=True
            )
        if not success:
            return False
    
    # Instruções adicionais específicas para ferramentas
    if name == "jwt-hack" and info["type"] == "go" and available_prereqs.get("go", False):
        success, output = run_command(
            ["go", "build"], 
            cwd=str(tool_dir)
        )
        if not success:
            return False
    
    if name == "gojwtcrack" and info["type"] == "go" and available_prereqs.get("go", False):
        success, output = run_command(
            ["go", "build"], 
            cwd=str(tool_dir)
        )
        if not success:
            return False
    
    logger.info(f"Ferramenta {name} configurada com sucesso!")
    return True

def setup_pentestgpt():
    """Configura a integração com o PentestGPT"""
    try:
        logger.info("Instalando biblioteca PentestGPT...")
        success, output = run_command(
            [sys.executable, "-m", "pip", "install", "pentestgpt"]
        )
        if not success:
            logger.warning("Não foi possível instalar a biblioteca PentestGPT oficialmente.")
            # Cria um módulo simulado para pentestgpt
            pentestgpt_dir = EXTERNAL_DIR / "pentestgpt"
            pentestgpt_dir.mkdir(exist_ok=True)
            
            with open(pentestgpt_dir / "__init__.py", "w") as f:
                f.write("""
class PentestGPT:
    def __init__(self, api_key=None):
        self.api_key = api_key
        
    def analyze(self, content, context=None):
        return {
            "risk_level": "medium",
            "findings": ["Simulated finding for testing purposes"],
            "recommendations": ["This is a simulated PentestGPT response"]
        }
""")
            
            logger.info("Criado módulo simulado para PentestGPT")
        else:
            logger.info("PentestGPT instalado com sucesso!")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao configurar PentestGPT: {e}")
        return False

def create_wrappers():
    """Cria scripts wrapper para facilitar o uso das ferramentas"""
    wrappers_dir = EXTERNAL_DIR / "wrappers"
    wrappers_dir.mkdir(exist_ok=True)
    
    # Cria wrappers para cada ferramenta
    for name, info in TOOLS.items():
        if info["type"] == "python":
            with open(wrappers_dir / f"{name}.py", "w") as f:
                f.write(f"""#!/usr/bin/env python3
import sys
import os
import subprocess

# Caminho para a ferramenta
TOOL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "{name}")

def main():
    # Passa todos os argumentos para a ferramenta
    args = sys.argv[1:]
    cmd = [sys.executable]
    
    # Arquivo principal específico da ferramenta
    main_file = ""
    if "{name}" == "jwt_tool":
        main_file = os.path.join(TOOL_PATH, "jwt_tool.py")
    elif "{name}" == "jwtXploiter":
        main_file = os.path.join(TOOL_PATH, "jwtxploiter", "jwtxploiter.py")
    elif "{name}" == "jwtcat":
        main_file = os.path.join(TOOL_PATH, "jwtcat.py")
    else:
        main_file = os.path.join(TOOL_PATH, "main.py")
    
    cmd.append(main_file)
    cmd.extend(args)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {name}: {{e}}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\nOperação cancelada pelo usuário.")
        sys.exit(130)

if __name__ == "__main__":
    main()
""")
        elif info["type"] in ["node", "go", "c"]:
            with open(wrappers_dir / f"{name}.py", "w") as f:
                f.write(f"""#!/usr/bin/env python3
import sys
import os
import subprocess

# Caminho para a ferramenta
TOOL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "{name}")

def main():
    # Passa todos os argumentos para a ferramenta
    args = sys.argv[1:]
    
    # Comando específico para cada tipo de ferramenta
    cmd = []
    if "{info['type']}" == "node":
        cmd = ["node", os.path.join(TOOL_PATH, "index.js")]
    elif "{info['type']}" == "go":
        cmd = [os.path.join(TOOL_PATH, "{name}")]
    elif "{info['type']}" == "c":
        cmd = [os.path.join(TOOL_PATH, "{name}")]
    
    cmd.extend(args)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {name}: {{e}}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\nOperação cancelada pelo usuário.")
        sys.exit(130)

if __name__ == "__main__":
    main()
""")
    
    logger.info(f"Wrappers criados em {wrappers_dir}")
    return True

def main():
    """Função principal"""
    logger.info("Iniciando configuração das ferramentas JWT...")
    
    # Verifica pré-requisitos
    available_prereqs = check_prerequisites()
    
    # Cria diretório externo se não existir
    EXTERNAL_DIR.mkdir(exist_ok=True)
    
    # Configura cada ferramenta
    successful = 0
    failed = 0
    skipped = 0
    
    for name, info in TOOLS.items():
        logger.info(f"Configurando {name}...")
        
        # Verifica se os pré-requisitos para esta ferramenta estão disponíveis
        if (info["type"] == "go" and not available_prereqs.get("go", False)) or \
           (info["type"] == "c" and not available_prereqs.get("make", False)) or \
           (info["type"] == "node" and not available_prereqs.get("npm", False)):
            logger.warning(f"Pulando {name} devido à falta de pré-requisitos necessários")
            skipped += 1
            continue
        
        if setup_tool(name, info, available_prereqs):
            successful += 1
        else:
            failed += 1
    
    # Configura PentestGPT
    setup_pentestgpt()
    
    # Cria wrappers
    create_wrappers()
    
    # Resumo
    logger.info("=== Resumo da Configuração ===")
    logger.info(f"Total de ferramentas: {len(TOOLS)}")
    logger.info(f"Configuradas com sucesso: {successful}")
    logger.info(f"Falhas na configuração: {failed}")
    logger.info(f"Puladas devido à falta de pré-requisitos: {skipped}")
    
    if failed > 0:
        logger.warning("Algumas ferramentas não foram configuradas corretamente.")
        logger.warning("Verifique os logs acima para mais detalhes.")
    else:
        if skipped > 0:
            logger.info("Algumas ferramentas foram puladas devido à falta de pré-requisitos, mas as demais foram configuradas com sucesso!")
        else:
            logger.info("Todas as ferramentas foram configuradas com sucesso!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 