#!/usr/bin/env python3
import sys
import os
import subprocess

# Caminho para a ferramenta
TOOL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jwtXploiter")

def main():
    # Passa todos os argumentos para a ferramenta
    args = sys.argv[1:]
    cmd = [sys.executable]
    
    # Arquivo principal específico da ferramenta
    main_file = ""
    if "jwtXploiter" == "jwt_tool":
        main_file = os.path.join(TOOL_PATH, "jwt_tool.py")
    elif "jwtXploiter" == "jwtXploiter":
        main_file = os.path.join(TOOL_PATH, "jwtxploiter", "jwtxploiter.py")
    elif "jwtXploiter" == "jwtcat":
        main_file = os.path.join(TOOL_PATH, "jwtcat.py")
    else:
        main_file = os.path.join(TOOL_PATH, "main.py")
    
    cmd.append(main_file)
    cmd.extend(args)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar jwtXploiter: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)

if __name__ == "__main__":
    main()
