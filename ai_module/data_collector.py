import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import jwt
import requests
from tqdm import tqdm

@dataclass
class JWTSample:
    """Classe para representar uma amostra de token JWT."""
    token: str
    header: Dict
    payload: Dict
    signature: str
    is_vulnerable: bool
    vulnerability_type: Optional[str]
    source: str
    collected_at: datetime
    metadata: Dict

class JWTDataCollector:
    """Coletor de dados para treinamento do modelo de análise de JWT."""
    
    def __init__(self, output_dir: str = "data/jwt_samples"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def collect_from_file(self, file_path: str) -> List[JWTSample]:
        """Coleta tokens JWT de um arquivo."""
        samples = []
        try:
            with open(file_path, 'r') as f:
                for line in tqdm(f, desc="Coletando tokens do arquivo"):
                    token = line.strip()
                    if self._is_valid_jwt(token):
                        sample = self._create_sample(token, "file")
                        samples.append(sample)
        except Exception as e:
            self.logger.error(f"Erro ao coletar tokens do arquivo: {e}")
        return samples
    
    def collect_from_api(self, api_url: str, headers: Dict = None) -> List[JWTSample]:
        """Coleta tokens JWT de uma API."""
        samples = []
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                # Procura por tokens JWT na resposta
                tokens = self._extract_tokens_from_response(response.text)
                for token in tokens:
                    sample = self._create_sample(token, "api")
                    samples.append(sample)
        except Exception as e:
            self.logger.error(f"Erro ao coletar tokens da API: {e}")
        return samples
    
    def save_samples(self, samples: List[JWTSample], filename: str):
        """Salva as amostras coletadas em um arquivo JSON."""
        output_file = self.output_dir / filename
        try:
            data = [self._sample_to_dict(sample) for sample in samples]
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Amostras salvas em {output_file}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar amostras: {e}")
    
    def _is_valid_jwt(self, token: str) -> bool:
        """Verifica se uma string é um token JWT válido."""
        try:
            jwt.decode(token, options={"verify_signature": False})
            return True
        except:
            return False
    
    def _create_sample(self, token: str, source: str) -> JWTSample:
        """Cria uma amostra de token JWT."""
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            header = jwt.get_unverified_header(token)
            signature = token.split('.')[-1]
            
            return JWTSample(
                token=token,
                header=header,
                payload=decoded,
                signature=signature,
                is_vulnerable=False,  # Será anotado posteriormente
                vulnerability_type=None,
                source=source,
                collected_at=datetime.now(),
                metadata={}
            )
        except Exception as e:
            self.logger.error(f"Erro ao criar amostra: {e}")
            return None
    
    def _extract_tokens_from_response(self, response_text: str) -> List[str]:
        """Extrai tokens JWT de uma resposta de texto."""
        # Implementar lógica de extração de tokens
        # Pode usar regex ou outras técnicas
        return []
    
    def _sample_to_dict(self, sample: JWTSample) -> Dict:
        """Converte uma amostra para dicionário."""
        return {
            "token": sample.token,
            "header": sample.header,
            "payload": sample.payload,
            "signature": sample.signature,
            "is_vulnerable": sample.is_vulnerable,
            "vulnerability_type": sample.vulnerability_type,
            "source": sample.source,
            "collected_at": sample.collected_at.isoformat(),
            "metadata": sample.metadata
        } 