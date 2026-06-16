import re
import os
import json
import hashlib
import requests
import threading
import time
from bs4 import BeautifulSoup
from itertools import product, chain
from urllib.parse import quote_plus
from fake_useragent import UserAgent
from modules.osint_module import OSINTScraper
import logging
from logging import FileHandler, Formatter
from config.settings import config
from modules.voidsync_api import VoidSyncClient

# Setup de logging para scraping de wordlist
scraping_logger = logging.getLogger('scraping')
if not scraping_logger.handlers:
    fh = FileHandler('logs/scraping.log')
    fh.setFormatter(Formatter('[%(asctime)s] %(message)s'))
    scraping_logger.addHandler(fh)
    scraping_logger.setLevel(logging.INFO)

# Remover import circular no topo do arquivo
class WordlistGenerator:
    def __init__(self, dump_file='dump_users.txt', tested_file='wordlist_tested.txt'):
        # Mover import para dentro do método para evitar import circular
        # Definindo base_terms diretamente sem chamar generate_common_passwords
        self.base_terms = set([
            'admin', '123456', 'password', 'senha', 'betadmin', 'bet333',
            'user', 'root', 'qwerty', 'abc123', 'letmein',
            # Adicionar mais termos comuns
            'jwt123', 'letmein', 'eviljwt', 'secretkey', 'tokenforce', 
            'bruteforce', 'passw0rd', '12345678', 'welcome', 'master', 
            'superuser'
        ])
        self.tested_words = self.load_tested(tested_file)
        self.enriched_terms = set()
        self.dump_file = dump_file
        self.ua = UserAgent()
        self.osint = OSINTScraper()
        self.lock = threading.Lock()

    def load_tested(self, filepath):
        if not os.path.exists(filepath):
            return set()
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return set([line.strip() for line in f.readlines()])

    def leetspeak_variants(self, word):
        substitutions = {
            'a': ['4', '@'], 'e': ['3'], 'i': ['1', '!'], 'o': ['0'], 's': ['$', '5']
        }
        variants = set()
        for i in range(1, 2 ** len(word)):
            chars = list(word)
            for j, char in enumerate(word):
                if char.lower() in substitutions and (i >> j) & 1:
                    chars[j] = substitutions[char.lower()][0]
            variants.add(''.join(chars))
        return variants

    def advanced_mutations(self, word):
        # Gera mutações avançadas para aumentar a cobertura
        mutations = set([
            word, word.lower(), word.upper(), word.capitalize(), word[::-1],
            word + "123", "123" + word, word + "!", word + "@", word + "#", word + "$", word + "2024",
            word.replace("a", "@"), word.replace("o", "0"), word.replace("i", "1"), word.replace("e", "3"),
            hashlib.md5(word.encode()).hexdigest(),
            hashlib.sha1(word.encode()).hexdigest(),
            hashlib.sha256(word.encode()).hexdigest()
        ])
        mutations |= self.leetspeak_variants(word)
        return mutations

    def extract_terms_from_dump(self):
        if not os.path.exists(self.dump_file):
            return
        with open(self.dump_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                words = re.findall(r'\w+', line)
                for word in words:
                    self.base_terms.add(word.lower())

    def search_database_terms(self, target_url):
        try:
            from .sql_injector import SQLInjector
            injector = SQLInjector()
            terms = injector.detect_vulnerable_fields(target_url)
            self.enriched_terms.update(terms)
        except Exception as e:
            print(f"Erro ao extrair termos do banco de dados: {e}")

    def search_duckduckgo(self, query):
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        retries = 3
        for attempt in range(retries):
            headers = {'User-Agent': self.ua.random}
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = soup.find_all('a', {'class': 'result__a'})
                    for result in results:
                        self.enriched_terms.update(re.findall(r'\w+', result.get_text()))
                    return
                else:
                    print(f"Erro DuckDuckGo (tentativa {attempt+1}/{retries}): Status {response.status_code}")
            except Exception as e:
                print(f"Erro DuckDuckGo (tentativa {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    print(f"Falha após {retries} tentativas. Simulando resultados para {query}")
                    self.enriched_terms.update([f"simulated_{query.replace(' ', '_')}_{i}" for i in range(5)])
                time.sleep(2 * (attempt + 1))

    def scrape_public_sites(self):
        sources = [
            # Governamentais, organizacionais, sociais, técnicos, domínios globais e asiáticos
            "https://www.gov.br/", "https://www.tse.jus.br/", "https://www.usa.gov/", "https://www.europa.eu/",
            "https://www.un.org/", "https://www.who.int/", "https://www.unicef.org/", "https://www.amnesty.org/",
            "https://www.facebook.com", "https://www.instagram.com", "https://www.linkedin.com", "https://www.twitter.com",
            "https://www.youtube.com", "https://www.reddit.com", "https://www.pinterest.com", "https://www.tiktok.com",
            "https://www.github.com", "https://www.gitlab.com", "https://www.bitbucket.org", "https://www.stackoverflow.com",
            "https://www.baidu.com", "https://www.qq.com", "https://www.weibo.com", "https://www.sina.com.cn",
            "https://www.naver.com", "https://www.yandex.ru", "https://www.nic.asia", "https://www.nic.jp", "https://www.nic.cn"
        ]
        retries = 3
        for url in sources:
            for attempt in range(retries):
                try:
                    headers = {'User-Agent': self.ua.random}
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        text = BeautifulSoup(response.text, 'html.parser').get_text()
                        words = re.findall(r'\w+', text)
                        self.enriched_terms.update([w.lower() for w in words if 5 <= len(w) <= 32])
                        break
                    else:
                        print(f"Erro scraping site {url} (tentativa {attempt+1}/{retries}): Status {response.status_code}")
                except Exception as e:
                    print(f"Erro scraping site {url} (tentativa {attempt+1}/{retries}): {e}")
                    if attempt == retries - 1:
                        print(f"Falha após {retries} tentativas para {url}. Simulando resultados.")
                        self.enriched_terms.update([f"simulated_{url.split('.')[1]}_{i}" for i in range(3)])
                    time.sleep(2 * (attempt + 1))

    def scrape_social_media_titles(self, queries):
        search_base = "https://html.duckduckgo.com/html/?q="
        platforms = [
            "site:facebook.com", "site:instagram.com", "site:x.com", "site:youtube.com", "site:threads.net",
            "site:tiktok.com", "site:linkedin.com", "site:github.com", "site:gitlab.com", "site:bitbucket.org",
            "site:stackoverflow.com", "site:reddit.com", "site:pinterest.com", "site:tumblr.com", "site:medium.com",
            "site:.gov", "site:.org", "site:.edu", "site:.net", "site:.bet", "site:.asia", "site:.jp", "site:.cn"
        ]
        retries = 3
        for q in queries:
            for p in platforms:
                full_query = quote_plus(f"{q} {p}")
                url = f"{search_base}{full_query}"
                for attempt in range(retries):
                    try:
                        headers = {'User-Agent': self.ua.random}
                        resp = requests.get(url, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, 'html.parser')
                            for result in soup.find_all('a', {'class': 'result__a'}):
                                self.enriched_terms.update(re.findall(r'\w+', result.get_text()))
                            break
                        else:
                            print(f"Erro em {p} (tentativa {attempt+1}/{retries}): Status {resp.status_code}")
                    except Exception as e:
                        print(f"Erro em {p} (tentativa {attempt+1}/{retries}): {e}")
                        if attempt == retries - 1:
                            print(f"Falha após {retries} tentativas para {q} em {p}. Simulando resultados.")
                            self.enriched_terms.update([f"simulated_{q.replace(' ', '_')}_{p.split(':')[1]}_{i}" for i in range(2)])
                        time.sleep(2 * (attempt + 1))

    def enrich_with_osint(self, term):
        # Busca em redes sociais, sites .gov, .org, .net, .bet, domínios asiáticos, etc.
        findings = self.osint.analyze_target(term)
        for category, items in findings.items():
            self.enriched_terms.update([i.lower() for i in items if 5 <= len(i) <= 32])

    def integrate_theharvester(self, domain):
        # Integração com módulos do theHarvester para enriquecer ainda mais
        try:
            from external.theHarvester.theHarvester.discovery.bingsearch import SearchBing
            from external.theHarvester.theHarvester.discovery.rapiddns import SearchRapidDns
            from external.theHarvester.theHarvester.discovery.subdomainfinderc99 import SearchSubdomainfinderc99
            from external.theHarvester.theHarvester.discovery.bufferoverun import SearchBufferover
            from external.theHarvester.theHarvester.discovery.netlas import SearchNetlas
            import asyncio

            async def run_harvester():
                results = set()
                # Bing
                bing = SearchBing(domain, 100, 0)
                await bing.do_search()
                results.update(await bing.get_hostnames())
                # RapidDNS
                rapiddns = SearchRapidDns(domain)
                await rapiddns.do_search()
                results.update(await rapiddns.get_hostnames())
                # SubdomainFinderC99
                c99 = SearchSubdomainfinderc99(domain)
                await c99.do_search()
                results.update(await c99.get_hostnames())
                # BufferOver
                bufferover = SearchBufferover(domain)
                await bufferover.do_search()
                results.update(await bufferover.get_hostnames())
                # Netlas
                netlas = SearchNetlas(domain, 100)
                await netlas.do_search()
                results.update(await netlas.get_hostnames())
                return results

            loop = asyncio.get_event_loop()
            hosts = loop.run_until_complete(run_harvester())
            self.enriched_terms.update([h.lower() for h in hosts if 5 <= len(h) <= 32])
        except Exception as e:
            print(f"Erro integrando theHarvester: {e}")

    def generate_wordlist(self, output_file='wordlist_final.txt', target_url=None, domain=None):
        # Import movido para dentro da função para evitar import circular
        from utils.wordlist_utils import save_wordlist
        self.extract_terms_from_dump()
        if target_url:
            self.search_database_terms(target_url)
        for base in list(self.base_terms):
            self.base_terms.update(self.leetspeak_variants(base))
            self.base_terms.update(self.advanced_mutations(base))
        # Consultas de busca para enriquecer
        search_queries = [
            "bet333 login admin senha user pass", "betting site admin credentials",
            "gambling platform security", "online casino management", "betting system administration",
            "admin painel acesso", "plataforma apostas admin", "painel controle cassino"
        ]
        for query in search_queries:
            self.search_duckduckgo(query)
        self.scrape_public_sites()
        self.scrape_social_media_titles([
            "bet333", "admin login", "alterar saldo site", "betting admin", "casino management", "platform security"
        ])
        # Enriquecimento OSINT
        for term in list(self.base_terms)[:20]:
            self.enrich_with_osint(term)
        # Integração com theHarvester
        if domain:
            self.integrate_theharvester(domain)
        # Integração com Void Sync API
        if config.get('api_provider') == 'voidsync' and config.get('voidsync', {}).get('enable_wordlist', False):
            vs = VoidSyncClient(access_key=config['voidsync']['access_key'])
            query = domain or target_url or ''
            if query:
                for base in ['nome','email','cpf','cnpj','rg','telefone','titulo','placa','chassi','renavam','mae','pai','cns','motor','funcionarios','razao']:
                    try:
                        resp = vs.search(query, base)
                        items = vs.parse_response(resp)
                        for w in items:
                            if 5 <= len(w) <= 32:
                                self.enriched_terms.add(w.lower())
                        scraping_logger.info(f"VoidSync (base={base}) returned {len(items)} items for {query}")
                    except Exception as e:
                        scraping_logger.error(f"Error in VoidSync base={base}, query={query}: {e}")
        # Finalização e filtragem
        final_words = (self.base_terms | self.enriched_terms) - self.tested_words
        final_words = set([w.lower() for w in final_words if 5 <= len(w) <= 32])
        save_wordlist(sorted(final_words), output_file)
        print(f"[+] Wordlist gerada com {len(final_words)} palavras: {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerador Avançado de Wordlists")
    parser.add_argument("--output", default="wordlist_final.txt", help="Arquivo de saída da wordlist")
    parser.add_argument("--target_url", help="URL do banco de dados alvo para extração")
    parser.add_argument("--domain", help="Domínio alvo para integração com OSINT/theHarvester")
    args = parser.parse_args()
    gen = WordlistGenerator()
    gen.generate_wordlist(output_file=args.output, target_url=args.target_url, domain=args.domain)

def run(target_url: str = 'https://d333bet.com/'):
    """Função para executar a geração de wordlist no modo automático."""
    gen = WordlistGenerator()
    domain = target_url.split('://')[1].split('/')[0] if '://' in target_url else target_url.split('/')[0]
    gen.generate_wordlist(output_file='wordlist_final.txt', target_url=target_url, domain=domain)
    print(f"Wordlist gerada para o alvo {target_url}")

def generate_wordlist(count=100, output_file='output/test_wordlist.txt'):
    """
    Gera uma wordlist simplificada com o número especificado de palavras.
    
    Args:
        count (int): Número de palavras a serem geradas
        output_file (str): Caminho de saída para a wordlist
        
    Returns:
        str: Caminho do arquivo gerado
    """
    # Garante que o diretório exista
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Lista de palavras base para geração rápida
    base_words = [
        "admin", "password", "123456", "qwerty", "letmein", "welcome", 
        "monkey", "dragon", "baseball", "football", "master", "superman",
        "token", "secret", "security", "jwt", "api", "server", "login",
        "key", "private", "public", "crypto", "hash", "secure", "access"
    ]
    
    # Gera combinações e mutações
    words = set()
    for word in base_words:
        # Adiciona palavra base
        words.add(word)
        
        # Adiciona algumas variações
        words.add(word.upper())
        words.add(word.capitalize())
        words.add(word + "123")
        words.add(word + "!")
        words.add("2024" + word)
        
        # Substitui alguns caracteres (leet speak básico)
        words.add(word.replace("a", "@"))
        words.add(word.replace("e", "3"))
        words.add(word.replace("i", "1"))
        words.add(word.replace("o", "0"))
        words.add(word.replace("s", "$"))
    
    # Garante que temos palavras suficientes
    if len(words) < count:
        for i in range(count - len(words)):
            words.add(f"password{i+1}")
    
    # Limita ao número solicitado
    final_words = sorted(list(words))[:count]
    
    # Salva no arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in final_words:
            f.write(f"{word}\n")
    
    print(f"[+] Wordlist simplificada gerada com {len(final_words)} palavras: {output_file}")
    return output_file