import random
import time
import httpx
import uuid
import threading
from typing import List, Dict, Any, Optional
from utils.helpers import log_event
from modules.api_clients.external_data_api import IPStackAPI, WeatherStackAPI

EVENT_LEVELS = ["info", "warning", "error", "critical", "fatal", "debug"]
ENVIRONMENTS = ["production", "staging", "development", "qa"]
USERS = ["tester", "admin", "user01", "user02", "guest", "api_bot"]

EXTRA_MESSAGES = [
    "Simulated error log",
    "Unhandled exception occurred",
    "Database connection lost",
    "User authentication failed",
    "API rate limit exceeded",
    "Resource not found",
    "Permission denied",
    "Timeout while processing request",
    "Invalid JWT token",
    "Suspicious activity detected"
]

class SentrySimulator:
    def __init__(self, endpoints: List[str], threads: int = 4, delay_range: tuple = (0.2, 1.5)):
        self.endpoints = endpoints
        self.threads = threads
        self.delay_range = delay_range
        self._stop_event = threading.Event()

    def simulate_traffic(self, count: int = 50, alternate: bool = True):
        log_event("sentry", f"Iniciando simulação com {self.threads} threads, {count} eventos, alternância: {alternate}")
        events_per_thread = count // self.threads
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=self._simulate_worker, args=(events_per_thread, alternate, i))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        log_event("sentry", "Simulação de tráfego finalizada.")

    def _simulate_worker(self, count: int, alternate: bool, thread_id: int):
        for i in range(count):
            if self._stop_event.is_set():
                break
            endpoint = random.choice(self.endpoints)
            payload = self.generate_payload(alternate=alternate)
            retries = 3
            for attempt in range(retries):
                try:
                    response = httpx.post(endpoint, json=payload, timeout=5)
                    log_event("sentry", f"[Thread {thread_id}] Payload {i+1}/{count} enviado para {endpoint} - Status {response.status_code}")
                    break
                except Exception as e:
                    log_event("sentry", f"[Thread {thread_id}] Erro ao enviar payload (tentativa {attempt+1}/{retries}): {e}")
                    if attempt == retries - 1:
                        fallback_endpoint = "http://localhost:9000/sentry"
                        log_event("sentry", f"[Thread {thread_id}] Falha após {retries} tentativas. Usando endpoint local de fallback: {fallback_endpoint}")
                        try:
                            response = httpx.post(fallback_endpoint, json=payload, timeout=5)
                            log_event("sentry", f"[Thread {thread_id}] Payload {i+1}/{count} enviado para {fallback_endpoint} - Status {response.status_code}")
                        except Exception as fallback_e:
                            log_event("sentry", f"[Thread {thread_id}] Erro no endpoint de fallback: {fallback_e}")
                    time.sleep(random.uniform(*self.delay_range))
            time.sleep(random.uniform(*self.delay_range))

    def generate_payload(self, alternate: bool = True) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        timestamp = int(time.time())
        if alternate:
            level = random.choice(EVENT_LEVELS)
            env = random.choice(ENVIRONMENTS)
            user = random.choice(USERS)
            message = random.choice(EXTRA_MESSAGES)
            tags = {
                "env": env,
                "user": user,
                "module": random.choice(["auth", "bruteforce", "sql", "report", "cli"]),
                "session": str(uuid.uuid4())[:8]
            }
            extra = {
                "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(0,255)}",
                "request_id": str(uuid.uuid4()),
                "details": {
                    "attempt": random.randint(1, 10),
                    "success": random.choice([True, False])
                }
            }
            # Obter localizacao via IPStack e clima via WeatherStack
            loc = IPStackAPI.get_location(extra['ip_address'])
            city = loc.get('city') or loc.get('region_name') or ''
            weather = WeatherStackAPI.get_weather(city) if city else {}
            extra['location'] = loc
            extra['weather'] = weather
        else:
            level = "error"
            message = "Simulated error log"
            tags = {"env": "production", "user": "tester"}
            extra = {}
        return {
            "event_id": event_id,
            "message": message,
            "level": level,
            "timestamp": timestamp,
            "tags": tags,
            "extra": extra
        }

    def stop(self):
        self._stop_event.set()

def run(target_url: str = 'https://d333bet.com/'):
    # Endpoint baseado na URL alvo para simulação de interceptação
    endpoints = [f"{target_url}/sentry" if not target_url.endswith('/') else f"{target_url}sentry"]
    print(f"Simulando interceptação de requisições para: {endpoints[0]}")
    simulator = SentrySimulator(endpoints=endpoints, threads=4, delay_range=(0.2, 1.2))
    simulator.simulate_traffic(count=40, alternate=True)

if __name__ == "__main__":
    run()