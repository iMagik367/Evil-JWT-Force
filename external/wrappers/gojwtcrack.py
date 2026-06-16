#!/usr/bin/env python3
import sys
import os
import subprocess

# Caminho para a ferramenta
TOOL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gojwtcrack")

def main():
    # Passa todos os argumentos para a ferramenta
    args = sys.argv[1:]
    
    # Comando específico para cada tipo de ferramenta
    cmd = []
    if "go" == "node":
        cmd = ["node", os.path.join(TOOL_PATH, "index.js")]
    elif "go" == "go":
        cmd = [os.path.join(TOOL_PATH, "gojwtcrack")]
    elif "go" == "c":
        cmd = [os.path.join(TOOL_PATH, "gojwtcrack")]
    
    cmd.extend(args)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar gojwtcrack: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)

if __name__ == "__main__":
    main()
