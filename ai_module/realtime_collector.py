import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
from data_collector import JWTDataCollector
from ai_module.vulnerability_annotator import JWTAnnotator
import asyncio
import websockets
import json
from siem_integration import send_event_to_siem

class RealTimeJWTCollector:
    """
    Coleta tokens JWT em tempo real de endpoints, arquivos de log ou APIs.
    """
    def __init__(self, output_dir: str = "data/jwt_samples", poll_interval: int = 5):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self.poll_interval = poll_interval
        self.collector = JWTDataCollector(output_dir)
        self.annotator = JWTAnnotator(output_dir)

    def monitor_api(self, api_url: str, headers: Optional[Dict] = None, stop_after: int = 60):
        """
        Monitora uma API em tempo real e coleta/anota tokens JWT conforme aparecem.
        stop_after: tempo em segundos para parar a coleta (None para rodar indefinidamente)
        """
        start_time = time.time()
        all_samples = []
        while True:
            try:
                samples = self.collector.collect_from_api(api_url, headers)
                if samples:
                    self.collector.save_samples(samples, 'realtime_raw_samples.json')
                    self.annotator.annotate_samples('realtime_raw_samples.json', 'realtime_annotated_samples.json')
                    all_samples.extend(samples)
                    self.logger.info(f"Coletados e anotados {len(samples)} tokens JWT em tempo real.")
                else:
                    self.logger.info("Nenhum novo token encontrado nesta iteração.")
            except Exception as e:
                self.logger.error(f"Erro na coleta/anotação em tempo real: {e}")
            if stop_after and (time.time() - start_time) > stop_after:
                break
            time.sleep(self.poll_interval)
        return all_samples

    def monitor_logfile(self, logfile_path: str, stop_after: int = 60):
        """
        Monitora um arquivo de log em tempo real e coleta/anota tokens JWT conforme aparecem.
        """
        start_time = time.time()
        seen_lines = set()
        all_samples = []
        while True:
            try:
                with open(logfile_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                new_lines = [line for line in lines if line not in seen_lines]
                seen_lines.update(new_lines)
                for line in new_lines:
                    tokens = self.collector._extract_tokens_from_response(line)
                    for token in tokens:
                        sample = self.collector._create_sample(token, "logfile")
                        self.collector.save_samples([sample], 'realtime_raw_samples.json')
                        self.annotator.annotate_samples('realtime_raw_samples.json', 'realtime_annotated_samples.json')
                        all_samples.append(sample)
                        self.logger.info(f"Token JWT coletado e anotado do log: {token}")
            except Exception as e:
                self.logger.error(f"Erro na leitura do log: {e}")
            if stop_after and (time.time() - start_time) > stop_after:
                break
            time.sleep(self.poll_interval)
        return all_samples

    def _extract_jwt_custom(self, msg, custom_fields=None, try_base64=True, try_protobuf=False, protobuf_schema_path=None):
        """
        Extrai JWTs de mensagens em formatos customizados: base64, campos aninhados, opcionalmente protobuf.
        custom_fields: lista de caminhos (ex: ['data.jwt_token', 'payload.tokens'])
        try_base64: tenta decodificar base64 se não encontrar JWT diretamente
        try_protobuf: tenta decodificar usando protobuf (requer schema)
        protobuf_schema_path: caminho do arquivo .proto
        """
        import base64
        results = []
        # 1. Busca direta
        results += self.collector._extract_tokens_from_response(msg)
        # 2. Busca em campos customizados (JSON)
        if custom_fields:
            try:
                obj = json.loads(msg) if isinstance(msg, str) else msg
                for path in custom_fields:
                    parts = path.split('.')
                    val = obj
                    for part in parts:
                        if isinstance(val, dict):
                            val = val.get(part)
                        elif isinstance(val, list) and part.isdigit():
                            val = val[int(part)]
                        else:
                            val = None
                            break
                    if isinstance(val, str):
                        results += self.collector._extract_tokens_from_response(val)
                    elif isinstance(val, list):
                        for v in val:
                            if isinstance(v, str):
                                results += self.collector._extract_tokens_from_response(v)
            except Exception:
                pass
        # 3. Base64
        if try_base64:
            try:
                if isinstance(msg, str):
                    decoded = base64.b64decode(msg + '===').decode('utf-8', errors='ignore')
                    results += self.collector._extract_tokens_from_response(decoded)
            except Exception:
                pass
        # 4. Protobuf (opcional)
        if try_protobuf and protobuf_schema_path:
            try:
                from google.protobuf import json_format
                import importlib.util
                spec = importlib.util.spec_from_file_location('pb_module', protobuf_schema_path)
                pb_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pb_module)
                # Supondo mensagem principal chamada 'MainMessage'
                MainMessage = getattr(pb_module, 'MainMessage', None)
                if MainMessage:
                    msg_bytes = msg if isinstance(msg, bytes) else msg.encode('utf-8')
                    pb_obj = MainMessage()
                    pb_obj.ParseFromString(msg_bytes)
                    pb_json = json_format.MessageToJson(pb_obj)
                    results += self.collector._extract_tokens_from_response(pb_json)
            except Exception:
                pass
        return list(set(results))

    async def monitor_websocket(self, ws_url: str, siem_url: str = None, api_key: str = None, stop_after: int = 60, siem_type: str = "generic", reconnect_delay: int = 5, custom_fields=None, try_base64=True, try_protobuf=False, protobuf_schema_path=None, siem_log_file=None):
        """
        Monitora um WebSocket em tempo real, coleta/anota tokens JWT, envia eventos ao SIEM, lida com múltiplos formatos de mensagem (incluindo base64, campos customizados, protobuf), e salva logs detalhados de envio ao SIEM.
        Reconecta automaticamente em caso de queda.
        """
        start_time = time.time()
        all_samples = []
        siem_logs = []
        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    self.logger.info(f"Conectado ao WebSocket: {ws_url}")
                    while True:
                        if stop_after and (time.time() - start_time) > stop_after:
                            if siem_log_file and siem_logs:
                                with open(siem_log_file, 'w', encoding='utf-8') as f:
                                    json.dump(siem_logs, f, indent=2)
                            return all_samples
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=10)
                            tokens = self._extract_jwt_custom(
                                msg,
                                custom_fields=custom_fields,
                                try_base64=try_base64,
                                try_protobuf=try_protobuf,
                                protobuf_schema_path=protobuf_schema_path
                            )
                            for token in tokens:
                                sample = self.collector._create_sample(token, "websocket")
                                self.collector.save_samples([sample], 'realtime_raw_samples.json')
                                self.annotator.annotate_samples('realtime_raw_samples.json', 'realtime_annotated_samples.json')
                                all_samples.append(sample)
                                self.logger.info(f"Token JWT coletado do WebSocket: {token}")
                                # Envia evento para SIEM se configurado
                                if siem_url:
                                    with open(self.output_dir / 'realtime_annotated_samples.json', 'r') as f:
                                        annotated = json.load(f)
                                        if annotated:
                                            siem_result = send_event_to_siem(annotated[-1], siem_url, api_key, siem_type=siem_type)
                                            siem_logs.append({
                                                'token': token,
                                                'siem_result': siem_result,
                                                'timestamp': time.time()
                                            })
                        except asyncio.TimeoutError:
                            continue
            except Exception as e:
                self.logger.error(f"Erro no WebSocket: {e}. Reconectando em {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
