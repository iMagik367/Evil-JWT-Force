import os
import requests
import re
import logging
import threading
from queue import Queue
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from utils.logger import logger

SOCIAL_PLATFORMS = [
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com", "youtube.com", "tiktok.com",
    "reddit.com", "pinterest.com", "tumblr.com", "medium.com", "vk.com", "weibo.com", "bilibili.com",
    "line.me", "kakao.com", "naver.com", "qq.com", "baidu.com", "douyin.com", "zhihu.com", "telegram.org"
]

GLOBAL_DOMAINS = [
    ".com", ".org", ".gov", ".edu", ".net", ".info", ".asia", ".jp", ".cn", ".kr", ".tw", ".hk", ".sg", ".in", ".ru"
]

SEARCH_ENGINES = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://duckduckgo.com/html/?q=",
    "https://search.yahoo.com/search?p="
]

HEADERS = {
    "User-Agent": UserAgent().random
}

# Nova funcionalidade: integração com API Void
ACCESS_KEY = os.environ.get('VOID_ACCESS_KEY', '')
VOID_API_URL = 'https://voidsearch.localto.net/api/search'
SUPPORTED_BASES = [
    'cpf', 'cnpj', 'rg', 'cpfsimpl', 'rgsimpl', 'nome', 'pis', 'titulo', 'telefone', 'email',
    'cns', 'mae', 'pai', 'placa', 'chassi', 'renavam', 'motor', 'fotorj', 'fotosp', 'funcionarios', 'razao'
]

def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def extract_domains(text):
    return re.findall(r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)

def extract_usernames(text):
    return re.findall(r"@([a-zA-Z0-9_]{3,32})", text)

def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z0-9_-]{5,32}\b", text)
    return list(set(words))

def search_engine_scrape(query, limit=10):
    results = []
    for engine in SEARCH_ENGINES:
        try:
            url = f"{engine}{query}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            for link in links:
                if any(domain in link for domain in GLOBAL_DOMAINS):
                    results.append(link)
            if len(results) >= limit:
                break
        except Exception as e:
            logger.warning(f"Erro ao buscar em {engine}: {e}")
    return results[:limit]

def social_media_scrape(query):
    results = []
    for platform in SOCIAL_PLATFORMS:
        try:
            url = f"https://www.google.com/search?q=site:{platform}+{query}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            for link in links:
                if platform in link:
                    results.append(link)
        except Exception as e:
            logger.warning(f"Erro ao buscar em {platform}: {e}")
    return results

def gov_org_scrape(query):
    results = []
    for tld in [".gov", ".org", ".edu"]:
        try:
            url = f"https://www.google.com/search?q=site:{tld}+{query}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            for link in links:
                if tld in link:
                    results.append(link)
        except Exception as e:
            logger.warning(f"Erro ao buscar em {tld}: {e}")
    return results

def asia_domain_scrape(query):
    results = []
    for tld in [".asia", ".jp", ".cn", ".kr", ".tw", ".hk", ".sg", ".in"]:
        try:
            url = f"https://www.google.com/search?q=site:{tld}+{query}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a", href=True)]
            for link in links:
                if tld in link:
                    results.append(link)
        except Exception as e:
            logger.warning(f"Erro ao buscar em {tld}: {e}")
    return results

def leak_check(query):
    leaks = []
    try:
        url = f"https://www.google.com/search?q={query}+site:pastebin.com"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        for link in links:
            if "pastebin.com" in link:
                leaks.append(link)
    except Exception as e:
        logger.warning(f"Erro ao buscar leaks: {e}")
    return leaks

def parallel_scrape(queries, scrape_func, results, max_threads=8):
    q = Queue()
    for query in queries:
        q.put(query)
    def worker():
        while not q.empty():
            query = q.get()
            try:
                res = scrape_func(query)
                results.extend(res)
            except Exception as e:
                logger.warning(f"Erro no worker: {e}")
            q.task_done()
    threads = []
    for _ in range(max_threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)
    q.join()

def void_api_scrape(info, bases=None, access_key=ACCESS_KEY):
    """
    Consulta a API Void para múltiplas bases e retorna um dict base->dados.
    """
    results = {}
    if bases is None:
        bases = SUPPORTED_BASES
    for base in bases:
        try:
            params = {'Access-Key': access_key, 'Base': base, 'Info': info}
            resp = requests.get(VOID_API_URL, params=params, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                results[base] = resp.json()
            else:
                logger.warning(f"Void API retornou status {resp.status_code} para base {base}")
        except Exception as e:
            logger.warning(f"Erro na Void API para base {base} info {info}: {e}")
    return results

class OSINTScraper:
    def __init__(self, target_domain=None):
        self.target_domain = target_domain
        self.collected_data = set()

    def analyze_target(self, terms, output_file="output/osint_results.txt"):
        results = {
            "emails": set(),
            "domains": set(),
            "usernames": set(),
            "keywords": set(),
            "links": set(),
            "leaks": set(),
            "api_void": set()
        }
        queries = [terms]
        # Busca paralela em mecanismos de busca globais
        search_results = []
        parallel_scrape(queries, search_engine_scrape, search_results)
        # Busca paralela em redes sociais
        social_results = []
        parallel_scrape(queries, social_media_scrape, social_results)
        # Busca paralela em domínios .gov, .org, .edu
        gov_org_results = []
        parallel_scrape(queries, gov_org_scrape, gov_org_results)
        # Busca paralela em domínios asiáticos
        asia_results = []
        parallel_scrape(queries, asia_domain_scrape, asia_results)
        # Busca por leaks
        leak_results = []
        parallel_scrape(queries, leak_check, leak_results)
        # Extração de dados
        all_text = "\n".join(search_results + social_results + gov_org_results + asia_results + leak_results)
        results["emails"].update(extract_emails(all_text))
        results["domains"].update(extract_domains(all_text))
        results["usernames"].update(extract_usernames(all_text))
        results["keywords"].update(extract_keywords(all_text))
        results["links"].update(search_results + social_results + gov_org_results + asia_results)
        results["leaks"].update(leak_results)

        # Integração com API Void
        api_data = void_api_scrape(terms)
        for base, data in api_data.items():
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        for item in v:
                            results["api_void"].add(str(item))
                    else:
                        results["api_void"].add(str(v))
            elif isinstance(data, list):
                for item in data:
                    results["api_void"].add(str(item))
            else:
                results["api_void"].add(str(data))

        # Conversão para lista
        for k in results:
            results[k] = list(results[k])
        # Salvar resultados
        with open(output_file, 'w', encoding='utf-8') as f:
            for category, items in results.items():
                f.write(f"\n=== {category.upper()} ===\n")
                for item in sorted(items):
                    f.write(f"{item}\n")
        logger.info(f"OSINT coletado para {terms}: {results}")
        return results