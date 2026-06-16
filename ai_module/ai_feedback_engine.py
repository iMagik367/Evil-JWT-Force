import logging
from typing import Dict, Any, List
from ai_module.vulnerability_annotator import JWTAnnotator

class AIFeedbackEngine:
    """
    Processa eventos, anota, sugere ajustes e gera feedback em tempo real para módulos de ataque.
    """
    def __init__(self, output_dir="data/jwt_samples"):
        self.annotator = JWTAnnotator(output_dir)
        self.logger = logging.getLogger(__name__)
        self.suggestion_history = []

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe evento do módulo (token, resposta, erro, contexto), anota e sugere próximos passos.
        Retorna dict com sugestões e alertas.
        """
        suggestions = []
        alerts = []
        # 1. Anotar vulnerabilidades
        if 'jwt' in event:
            vulns = self.annotator._analyze_token({'token': event['jwt']})
            for v in vulns:
                if v.vulnerability_type == 'blacklist_payload':
                    alerts.append(f"Token contém padrão perigoso: {v.metadata.get('pattern')}")
                if v.vulnerability_type == 'expired_token':
                    suggestions.append("Tente manipular o campo 'exp' para testar aceitação de tokens expirados.")
                if v.vulnerability_type == 'insecure_alg':
                    suggestions.append("Teste brute force com algoritmo 'none' ou algoritmos inseguros.")
                if v.vulnerability_type == 'blacklist_user':
                    alerts.append(f"Usuário perigoso detectado: {v.metadata.get('user')}")
                # Adicione mais heurísticas conforme necessário
        # 2. Sugerir payloads/técnicas
        if 'response' in event and 'invalid signature' in event['response'].lower():
            suggestions.append("Considere testar wordlists de chaves comuns para brute force.")
        # 3. Ajustes automáticos (exemplo)
        if 'module' in event and event['module'] == 'JWTBruteforcer':
            if 'alg' in event and event['alg'] == 'HS256':
                suggestions.append("Tente algoritmos alternativos (ex: RS256, ES256) se suporte detectado.")
        # 4. Registrar histórico
        feedback = {'suggestions': suggestions, 'alerts': alerts, 'event': event}
        self.suggestion_history.append(feedback)
        return feedback

    def get_history(self) -> List[Dict[str, Any]]:
        return self.suggestion_history

    def save_history(self, filepath: str):
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.suggestion_history, f, indent=2, ensure_ascii=False)

    def load_history(self, filepath: str):
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.suggestion_history = json.load(f)
        except Exception:
            self.suggestion_history = []
