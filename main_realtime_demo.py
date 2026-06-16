import logging
import time
from core.jwt_bruteforcer import JWTBruteforcer
from core.orchestrator import Orchestrator
from core.cli_feedback import cli_feedback_callback

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Instancia módulo de ataque
    bruteforcer = JWTBruteforcer(wordlist=['admin', 'jwt', 'evil', 'force'], alg='HS256')
    # Orquestrador com feedback CLI dinâmico
    orchestrator = Orchestrator(
        modules={'brute': bruteforcer},
        cli_callback=cli_feedback_callback,
        auto_mode=False  # True para aplicar sugestões automaticamente
    )
    orchestrator.start()
    # Aguarda execução dos módulos
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.stop()
        print("Execução finalizada.")
