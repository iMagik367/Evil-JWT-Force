import requests
import time

class BurpInterceptor:
    def __init__(self, api_url, api_token, project_file=None):
        """
        api_url: URL base da API do Burp Suite (ex: http://localhost:1337)
        api_token: token de autenticação Bearer
        project_file: caminho para projeto .burp a ser carregado
        """
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.project_file = project_file
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {self.api_token}'})
        self.running = False

    def start(self, url=None, log_callback=lambda msg: None):
        """
        Inicia proxy ou scanner via API do Burp Suite.
        """
        # Carrega projeto
        if self.project_file:
            log_callback(f"[Burp] Carregando projeto {self.project_file}")
            files = {'project': open(self.project_file, 'rb')}
            try:
                resp = self.session.post(f"{self.api_url}/project/load", files=files)
                log_callback(f"[Burp] Projeto carregado: HTTP {resp.status_code}")
            except Exception as e:
                log_callback(f"[Burp] Erro ao carregar projeto: {e}")
        # Adiciona URL ao escopo
        if url:
            log_callback(f"[Burp] Adicionando {url} ao escopo")
            try:
                data = {'url': url}
                resp = self.session.post(f"{self.api_url}/scope/add", json=data)
                log_callback(f"[Burp] URL adicionada: HTTP {resp.status_code}")
            except Exception as e:
                log_callback(f"[Burp] Erro ao adicionar escopo: {e}")
        # Inicia proxy
        log_callback("[Burp] Iniciando proxy via API")
        try:
            resp = self.session.post(f"{self.api_url}/proxy/start")
            log_callback(f"[Burp] Proxy iniciado: HTTP {resp.status_code}")
            self.running = True
        except Exception as e:
            log_callback(f"[Burp] Erro ao iniciar proxy: {e}")

    def stop(self, log_callback=lambda msg: None):
        """
        Para proxy ou scanner via API do Burp Suite.
        """
        if not self.running:
            log_callback('[Burp] Proxy não estava em execução')
            return
        log_callback('[Burp] Parando proxy via API')
        try:
            resp = self.session.post(f"{self.api_url}/proxy/stop")
            log_callback(f"[Burp] Proxy parado: HTTP {resp.status_code}")
        except Exception as e:
            log_callback(f"[Burp] Erro ao parar proxy: {e}")
        self.running = False 