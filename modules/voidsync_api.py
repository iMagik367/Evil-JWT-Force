import requests
import logging
from typing import List

# Configuração de logging para erros da API Void Sync
logger = logging.getLogger('voidsync')
if not logger.handlers:
    fh = logging.FileHandler('logs/errors.log')
    fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.ERROR)

class VoidSyncClient:
    def __init__(self, access_key: str, api_url: str = 'https://voidsearch.localto.net/api/search', timeout: int = 10):
        self.access_key = access_key
        self.api_url = api_url
        self.timeout = timeout
        self.logger = logger

    def search(self, query: str, tipo: str) -> dict:
        """
        Realiza busca na Void API para o tipo especificado e retorna o JSON.
        """
        params = {'Access-Key': self.access_key, 'Base': tipo, 'Info': query}
        try:
            resp = requests.get(self.api_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(f"VoidSyncClient.search error (tipo={tipo}, query={query}): {e}")
            return {}

    def parse_response(self, response: dict) -> List[str]:
        """
        Extrai valores úteis do JSON de resposta para enriquecer a wordlist.
        """
        results = []
        def extract(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    extract(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)
            else:
                results.append(str(obj))
        extract(response)
        # Remove duplicados e strings vazias
        return list({r for r in results if r})

    def fetch_keywords_from_nome(self, nome: str) -> List[str]:
        """
        Busca na base 'nome' e retorna lista de palavras extraídas.
        """
        resp = self.search(nome, 'nome')
        return self.parse_response(resp) 