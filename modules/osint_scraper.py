import os
import time
import json
import socket
import datetime
import logging

import requests
from bs4 import BeautifulSoup

try:
    import whois
except ImportError:
    whois = None

from modules.osint_module import (
    extract_emails, extract_domains, extract_usernames, extract_keywords,
    leak_check, HEADERS
)
from modules.theharvester_module import run_theharvester
from modules.shodan_module import search_shodan


def validate_osint_config(config: dict):
    """Validate that all required OSINT config fields are present and correct."""
    required = ['alvo', 'redes_sociais', 'motores_busca', 'dominios',
                'limite_resultados', 'delay', 'export_html', 'export_json']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing config field: {field}")
    if not isinstance(config['alvo'], str) or not config['alvo'].strip():
        raise ValueError("Campo 'alvo' deve ser uma string não vazia")
    for arr in ['redes_sociais', 'motores_busca', 'dominios']:
        if not isinstance(config[arr], list):
            raise ValueError(f"Campo '{arr}' deve ser uma lista")
    if not isinstance(config['limite_resultados'], int) or config['limite_resultados'] <= 0:
        raise ValueError("Campo 'limite_resultados' deve ser inteiro positivo")
    if not isinstance(config['delay'], (int, float)) or config['delay'] < 0:
        raise ValueError("Campo 'delay' deve ser número não negativo")
    if not isinstance(config['export_html'], bool):
        raise ValueError("Campo 'export_html' deve ser booleano")
    if not isinstance(config['export_json'], bool):
        raise ValueError("Campo 'export_json' deve ser booleano")


def run_osint_scraping(config: dict, log_callback, progress_callback):
    """
    Run integrated OSINT scraping workflow based on provided config.
    - config: dict with keys 'alvo', 'redes_sociais', 'motores_busca', 'dominios',
      'limite_resultados', 'delay', 'export_html', 'export_json'
    - log_callback: function(str) for real-time logging
    - progress_callback: function(int) for percentage updates
    Returns a dict with collected results.
    """
    validate_osint_config(config)
    log_callback('Iniciando OSINT scraping...')
    use_harvester = config.get('use_harvester', False)
    use_shodan = config.get('use_shodan', False)
    total = len(config['redes_sociais']) + len(config['motores_busca']) + len(config['dominios'])
    total += (1 if use_harvester else 0) + (1 if use_shodan else 0)
    if total == 0:
        log_callback('Nenhuma tarefa selecionada.')
        progress_callback(100)
        return {}
    done = 0
    progress_callback(0)
    results = {
        'emails': [],
        'domains': [],
        'usernames': [],
        'keywords': [],
        'links': [],
        'leaks': [],
        'whois': {},
        'dns': {},
        'shodan': []
    }
    # mappings
    platform_map = {
        'Facebook': 'facebook.com',
        'X (Twitter)': 'x.com',
        'Instagram': 'instagram.com',
        'Discord': 'discord.com',
        'YouTube': 'youtube.com',
        'Threads': 'threads.net',
        'Reddit': 'reddit.com',
        'Telegram': 'telegram.org'
    }
    engine_urls = {
        'Google': 'https://www.google.com/search?q=',
        'Bing': 'https://www.bing.com/search?q=',
        'Yahoo': 'https://search.yahoo.com/search?p='
    }
    if use_harvester:
        log_callback(f"Executando theHarvester para {config['alvo']}...")
        try:
            harv_data = run_theharvester(config['alvo'], config['limite_resultados'], log_callback)
            results['emails'].extend(harv_data.get('emails', []))
            results['domains'].extend(harv_data.get('hosts', []))
            results['links'].extend(harv_data.get('hosts', []))
        except Exception as e:
            log_callback(f"Erro theHarvester: {e}")
        done += 1
        progress_callback(int(done/total*100))
        time.sleep(config['delay'])
    if use_shodan:
        log_callback(f"Buscando no Shodan por {config['alvo']}...")
        try:
            shodan_matches = search_shodan(config['alvo'], config['limite_resultados'], log_callback)
            results['shodan'].extend(shodan_matches)
        except Exception as e:
            log_callback(f"Erro Shodan: {e}")
        done += 1
        progress_callback(int(done/total*100))
        time.sleep(config['delay'])
    # 1. Redes Sociais
    for platform in config['redes_sociais']:
        domain = platform_map.get(platform, '')
        log_callback(f"Buscando no {platform}...")
        try:
            # execute generic leak-based social scrape then filter
            links = leak_check(config['alvo'] + ' ' + domain)
            filtered = [l for l in links if domain in l]
        except Exception as e:
            log_callback(f"Erro ao buscar em {platform}: {e}")
            filtered = []
        results['links'].extend(filtered)
        log_callback(f"{len(filtered)} resultados encontrados em {platform}.")
        done += 1
        progress_callback(int(done/total*100))
        time.sleep(config['delay'])
    # 2. Mecanismos de Busca
    for engine in config['motores_busca']:
        base = engine_urls.get(engine)
        if not base:
            log_callback(f"Engine desconhecido: {engine}")
            done += 1
            progress_callback(int(done/total*100))
            continue
        log_callback(f"Buscando no {engine}...")
        try:
            url = base + requests.utils.quote(config['alvo'])
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            hrefs = [a.get('href') for a in soup.find_all('a', href=True)]
            filtered = hrefs[:config['limite_resultados']]
        except Exception as e:
            log_callback(f"Erro ao buscar em {engine}: {e}")
            filtered = []
        results['links'].extend(filtered)
        log_callback(f"{len(filtered)} resultados encontrados em {engine}.")
        done += 1
        progress_callback(int(done/total*100))
        time.sleep(config['delay'])
    # 3. Domínios
    for tld in config['dominios']:
        domain_name = f"{config['alvo']}{tld}"
        # WHOIS
        log_callback(f"Coletando WHOIS de {domain_name}...")
        if whois:
            try:
                w = whois.whois(domain_name)
                results['whois'][domain_name] = w.text if hasattr(w, 'text') else str(w)
            except Exception as e:
                log_callback(f"Erro WHOIS {domain_name}: {e}")
        else:
            log_callback("Módulo whois não disponível.")
        # DNS
        log_callback(f"Resolvendo DNS de {domain_name}...")
        try:
            ips = socket.gethostbyname_ex(domain_name)[2]
            results['dns'][domain_name] = ips
        except Exception as e:
            log_callback(f"Erro DNS {domain_name}: {e}")
            results['dns'][domain_name] = []
        # leaks
        log_callback(f"Verificando vazamentos para {domain_name}...")
        try:
            leaks = leak_check(domain_name)
        except Exception as e:
            log_callback(f"Erro leak_check {domain_name}: {e}")
            leaks = []
        results['leaks'].extend(leaks)
        log_callback(f"{len(leaks)} vazamentos encontrados em {domain_name}.")
        done += 1
        progress_callback(int(done/total*100))
        time.sleep(config['delay'])
    # Extrair dados agregados
    log_callback("Extraindo emails, domínios, usuários e palavras-chave...")
    all_text = "\n".join(results['links'] + results['leaks'])
    try:
        results['emails'] = list(set(extract_emails(all_text)))[:config['limite_resultados']]
        results['domains'] = list(set(extract_domains(all_text)))[:config['limite_resultados']]
        results['usernames'] = list(set(extract_usernames(all_text)))[:config['limite_resultados']]
        results['keywords'] = list(set(extract_keywords(all_text)))[:config['limite_resultados']]
    except Exception as e:
        log_callback(f"Erro na extração de dados: {e}")
    progress_callback(90)
    # Exportar
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('output', 'osint_results')
    os.makedirs(out_dir, exist_ok=True)
    if config['export_json']:
        path_json = os.path.join(out_dir, f"osint_{timestamp}.json")
        with open(path_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        log_callback(f"Resultados JSON salvos em {path_json}")
    if config['export_html']:
        path_html = os.path.join(out_dir, f"osint_{timestamp}.html")
        with open(path_html, 'w', encoding='utf-8') as f:
            f.write(f"<html><head><meta charset='utf-8'><title>OSINT {timestamp}</title></head><body>")
            for key, val in results.items():
                f.write(f"<h2>{key}</h2><ul>")
                if isinstance(val, dict):
                    for k, v in val.items():
                        f.write(f"<li><strong>{k}:</strong> {v}</li>")
                else:
                    for item in val:
                        f.write(f"<li>{item}</li>")
                f.write("</ul>")
            f.write("</body></html>")
        log_callback(f"Resultados HTML salvos em {path_html}")
    progress_callback(100)
    log_callback('OSINT scraping concluído.')
    return results 