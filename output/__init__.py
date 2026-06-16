"""
EVIL_JWT_FORCE - Reports Package

Responsável pela manipulação e estruturação dos relatórios gerados.
Relatórios HTML, JSON e arquivos de credenciais/tokens podem ser salvos e exportados a partir deste diretório.
"""

import os

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

REPORT_FILES = {
    "fail_credentials": "fail_credentials.txt",
    "found_secrets": "found_secrets.txt",
    "intercepted_tokens": "intercepted_tokens.txt",
    "valid_credentials": "valid_crendentials.txt"
}

def get_report_path(filename="report.html"):
    return os.path.join(REPORT_DIR, filename)

def list_existing_reports():
    return [f for f in os.listdir(REPORT_DIR) if f.endswith(".html") or f.endswith(".json")]

def get_special_file_path(file_key):
    filename = REPORT_FILES.get(file_key)
    if filename:
        return os.path.join(REPORT_DIR, filename)
    raise ValueError(f"Arquivo especial desconhecido: {file_key}")

def append_to_file(file_key, content):
    path = get_special_file_path(file_key)
    with open(path, "a", encoding="utf-8") as f:
        if isinstance(content, list):
            for item in content:
                f.write(f"{item}\n")
        else:
            f.write(f"{content}\n")

def read_file_lines(file_key):
    path = get_special_file_path(file_key)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def clear_file(file_key):
    path = get_special_file_path(file_key)
    open(path, "w", encoding="utf-8").close()

def save_report(data, filename="report.json"):
    path = get_report_path(filename)
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_html_report(html_content, filename="report.html"):
    path = get_report_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)