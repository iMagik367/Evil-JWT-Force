# Implementa interceptação de tráfego HTTP via Selenium WebDriver usando selenium-wire
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time

class SeleniumInterceptor:
    def __init__(self, browser, driver_path, headless=False):
        """
        browser: 'Chrome' or 'Firefox'
        driver_path: caminho para o executável do driver
        headless: abre em modo headless se True
        """
        self.browser = browser
        self.driver = None
        self.flows = []  # armazenar fluxos HTTP
        if browser == 'Chrome':
            opts = ChromeOptions()
            if headless:
                opts.add_argument('--headless')
            # habilita captura HAR
            seleniumwire_opts = {'enable_har': True}
            service = ChromeService(executable_path=driver_path) if driver_path else None
            self.driver = webdriver.Chrome(service=service, options=opts, seleniumwire_options=seleniumwire_opts)
        elif browser == 'Firefox':
            opts = FirefoxOptions()
            if headless:
                opts.add_argument('-headless')
            seleniumwire_opts = {'enable_har': True}
            service = FirefoxService(executable_path=driver_path) if driver_path else None
            self.driver = webdriver.Firefox(service=service, options=opts, seleniumwire_options=seleniumwire_opts)
        else:
            raise ValueError(f'Browser não suportado: {browser}')

    def start(self, url, log_callback):
        """
        Navega para a URL e intercepta requisições/respostas.
        log_callback: função para registrar cada evento na interface.
        """
        log_callback(f'[Selenium] Navegando para {url}')
        self.driver.get(url)
        # Aguarda carregamento inicial
        time.sleep(2)
        # Armazena fluxos
        self.flows = []
        for idx, req in enumerate(self.driver.requests):
            if req.response:
                flow = {
                    'id': idx,
                    'method': req.method,
                    'url': req.url,
                    'status': req.response.status_code,
                    'request_headers': dict(req.headers),
                    'request_body': req.body.decode('utf-8', errors='ignore') if req.body else '',
                    'response_headers': dict(req.response.headers),
                    'response_body': req.response.body.decode('utf-8', errors='ignore') if req.response.body else ''
                }
                self.flows.append(flow)
                log_callback(f"[Selenium] {flow['method']} {flow['url']} -> {flow['status']}")
        log_callback('[Selenium] Interceptação finalizada')

    def get_flows(self):
        """Retorna lista de fluxos capturados"""
        return list(self.flows)

    def reload_page(self, log_callback=lambda m: None):
        """Recarrega a página atual"""
        try:
            self.driver.refresh()
            log_callback('[Selenium] Página recarregada')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao recarregar: {e}')

    def execute_script(self, script, log_callback=lambda m: None):
        """Executa script JavaScript na página"""
        try:
            result = self.driver.execute_script(script)
            log_callback('[Selenium] Script executado')
            return result
        except Exception as e:
            log_callback(f'[Selenium] Erro ao executar script: {e}')
            return None

    def export_har(self, filename, log_callback=lambda m: None):
        """Exporta captura HAR para arquivo"""
        try:
            har_data = self.driver.har  # assume enable_har=True
            with open(filename, 'w', encoding='utf-8') as f:
                import json
                json.dump(har_data, f, ensure_ascii=False, indent=2)
            log_callback(f'[Selenium] HAR salvo em {filename}')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao exportar HAR: {e}')

    def filter_flows(self, method=None, status=None, url_contains=None):
        """Filtra fluxos armazenados"""
        results = []
        for flow in self.flows:
            if method and flow['method'] != method:
                continue
            if status and flow['status'] != status:
                continue
            if url_contains and url_contains not in flow['url']:
                continue
            results.append(flow)
        return results

    # --- Métodos primordiais do Selenium ---
    def go_back(self, log_callback=lambda m: None):
        """Navega para trás no navegador"""
        try:
            self.driver.back()
            log_callback('[Selenium] Navegou para trás')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao navegar para trás: {e}')

    def go_forward(self, log_callback=lambda m: None):
        """Navega para frente no navegador"""
        try:
            self.driver.forward()
            log_callback('[Selenium] Navegou para frente')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao navegar para frente: {e}')

    def get_title(self, log_callback=lambda m: None):
        """Retorna o título atual da página"""
        try:
            title = self.driver.title
            log_callback(f'[Selenium] Título da página: {title}')
            return title
        except Exception as e:
            log_callback(f'[Selenium] Erro ao obter título: {e}')
            return None

    def get_page_source(self, log_callback=lambda m: None):
        """Retorna o HTML da página atual"""
        try:
            src = self.driver.page_source
            log_callback('[Selenium] Page source capturado')
            return src
        except Exception as e:
            log_callback(f'[Selenium] Erro ao capturar page source: {e}')
            return ''

    def get_cookies(self, log_callback=lambda m: None):
        """Retorna lista de cookies"""
        try:
            cookies = self.driver.get_cookies()
            log_callback(f'[Selenium] Cookies obtidos: {len(cookies)}')
            return cookies
        except Exception as e:
            log_callback(f'[Selenium] Erro ao obter cookies: {e}')
            return []

    def clear_cookies(self, log_callback=lambda m: None):
        """Limpa todos os cookies"""
        try:
            self.driver.delete_all_cookies()
            log_callback('[Selenium] Cookies limpos')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao limpar cookies: {e}')

    def screenshot(self, filename, log_callback=lambda m: None):
        """Captura screenshot da página"""
        try:
            self.driver.save_screenshot(filename)
            log_callback(f'[Selenium] Screenshot salvo em {filename}')
        except Exception as e:
            log_callback(f'[Selenium] Erro ao capturar screenshot: {e}')

    def stop(self):
        """
        Encerra o WebDriver.
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass 