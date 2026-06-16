import datetime
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import logging

from utils.logger import get_logger

logger = get_logger("EVIL_JWT_FORCE.report")

class ReportGenerator:
    def __init__(self, output_path: str = "reports/report.html"):
        self.output_path = Path(output_path)
        self.sections: List[str] = []
        self.attachments: Dict[str, str] = {}

    def add_section(self, title: str, content: str):
        self.sections.append(f"<h2>{title}</h2>\n{content}")

    def add_table(self, title: str, data: Dict[str, Any]):
        table = "<table border='1' cellpadding='5' cellspacing='0'>"
        table += "<tr><th>Item</th><th>Valor</th></tr>"
        for key, val in data.items():
            table += f"<tr><td>{key}</td><td>{val}</td></tr>"
        table += "</table>"
        self.add_section(title, table)

    def add_json_data(self, title: str, json_data: Dict[str, Any]):
        """Adiciona dados JSON como uma seção formatada."""
        content = "<pre>" + json.dumps(json_data, indent=2) + "</pre>"
        self.add_section(title, content)

    def add_attachment(self, name: str, content: str):
        """Adiciona um anexo ao relatório."""
        self.attachments[name] = content

    def generate(self):
        """Gera o relatório HTML final."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EVIL-JWT-FORCE Relatório de Segurança</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #d9534f; }}
        h2 {{ color: #5bc0de; margin-top: 30px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th {{ background-color: #5bc0de; color: white; }}
        th, td {{ padding: 8px; text-align: left; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .footer {{ margin-top: 30px; font-size: 0.8em; color: #777; }}
        .timestamp {{ text-align: right; }}
    </style>
</head>
<body>
    <h1>EVIL-JWT-FORCE Relatório de Segurança</h1>
    <p class="timestamp">Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    <div>
        {"".join(self.sections)}
    </div>
    <hr>
    <div class="footer">
        <p>Gerado por EVIL-JWT-FORCE - Ferramenta de Análise e Exploração de JWT</p>
    </div>
</body>
</html>"""
        
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Salva o HTML
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        # Salva os anexos
        for name, content in self.attachments.items():
            attachment_path = Path(os.path.dirname(self.output_path)) / name
            with open(attachment_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        logger.info(f"Relatório HTML gerado com sucesso: {self.output_path}")
        return self.output_path

def generate_report(data: Dict[str, Any], output_path: str = "reports/report.html"):
    """
    Gera um relatório baseado nos dados fornecidos.
    
    Args:
        data: Dados para o relatório
        output_path: Caminho de saída para o relatório
        
    Returns:
        str: Caminho do relatório gerado
    """
    generator = ReportGenerator(output_path)
    
    # Informações gerais
    if "info" in data:
        generator.add_table("Informações Gerais", data["info"])
        
    # Resultados da análise
    if "analysis" in data:
        generator.add_json_data("Análise do Token", data["analysis"])
        
    # Vulnerabilidades encontradas
    if "vulnerabilities" in data:
        vulns_content = "<ul>"
        for vuln in data["vulnerabilities"]:
            vuln_desc = f"<li><strong>{vuln['name']}:</strong> {vuln['description']}</li>"
            vulns_content += vuln_desc
        vulns_content += "</ul>"
        generator.add_section("Vulnerabilidades Encontradas", vulns_content)
        
    # Resultados do teste de força bruta
    if "bruteforce_results" in data:
        generator.add_json_data("Resultados de Força Bruta", data["bruteforce_results"])
        
    # Resultados do Fake Pix Attack
    if "fake_pix_results" in data:
        generator.add_json_data("Fake Pix Attack", data["fake_pix_results"])
        
    # Detalhes do Fake Pix (EMV payload)
    if "fake_pix_emv_details" in data:
        generator.add_json_data("Fake PIX Details", data["fake_pix_emv_details"])
        
    # Resultados de injeção SQL
    if "sql_injection_results" in data:
        generator.add_json_data("Resultados de Injeção SQL", data["sql_injection_results"])
        
    # Configuração de ferramentas externas
    if "external_tools" in data:
        generator.add_table("Ferramentas Externas", data["external_tools"])
    
    # Dados Enriquecidos por APIs Externas
    if "api_enriched" in data:
        generator.add_json_data("Dados Enriquecidos por API", data["api_enriched"])
    
    return generator.generate()

def generate_html_report(input_json_path: str, output_html_path: str) -> str:
    """
    Gera um relatório HTML a partir de um arquivo JSON.
    
    Args:
        input_json_path: Caminho para o arquivo JSON de entrada
        output_html_path: Caminho para o arquivo HTML de saída
        
    Returns:
        str: Caminho do relatório HTML gerado
    """
    logger.info(f"Gerando relatório HTML de {input_json_path} para {output_html_path}")
    
    try:
        # Verifica se o arquivo JSON existe
        if not os.path.exists(input_json_path):
            logger.warning(f"Arquivo JSON não encontrado: {input_json_path}")
            # Cria dados de exemplo para demonstração
            data = {
                "info": {
                    "data": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "alvo": "Demonstração",
                    "status": "Concluído"
                },
                "analysis": {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "algoritmo": "HS256",
                    "resultado": "Token vulnerável"
                },
                "vulnerabilities": [
                    {
                        "name": "Assinatura Fraca",
                        "description": "O token usa uma chave fraca para assinatura"
                    },
                    {
                        "name": "Sem Expiração",
                        "description": "O token não possui data de expiração definida"
                    }
                ]
            }
        else:
            # Carrega dados do arquivo JSON
            with open(input_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Gera o relatório
        return generate_report(data, output_html_path)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório HTML: {e}")
        # Cria um relatório de erro
        generator = ReportGenerator(output_html_path)
        generator.add_section("Erro na Geração", f"<p>Ocorreu um erro ao gerar o relatório: {e}</p>")
        return generator.generate()

if __name__ == "__main__":
    # Teste da função
    report_path = generate_html_report("output/test_results.json", "output/test_report.html")
    print(f"Relatório gerado: {report_path}")