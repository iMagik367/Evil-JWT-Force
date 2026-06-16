from core.attack_module_base import AttackModuleBase
import time
import random

class JWTBruteforcer(AttackModuleBase):
    def __init__(self, wordlist=None, alg='HS256'):
        super().__init__('JWTBruteforcer')
        self.wordlist = wordlist or ['secret', 'admin', 'jwt', '123456']
        self.alg = alg
        self.suggestion_callback = None

    def run(self, event_bus=None):
        self.set_event_bus(event_bus)
        # Simulação de brute force
        for word in self.wordlist:
            # Simula geração e teste de um token
            token = f"header.{word}.{self.alg}"
            response = random.choice(['invalid signature', 'valid', 'expired'])
            result = {
                'jwt': token,
                'alg': self.alg,
                'response': response,
            }
            self.report_result(result)
            time.sleep(0.5)  # Simula tempo de ataque

    def receive_suggestion(self, suggestion):
        # Exemplo: aplicar sugestão recebida
        if 'HS256' in suggestion:
            self.alg = 'HS256'
        elif 'RS256' in suggestion:
            self.alg = 'RS256'
        elif 'wordlist' in suggestion:
            self.wordlist.append('newword')  # Exemplo
