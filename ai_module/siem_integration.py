import requests
import logging

def send_event_to_siem(event: dict, siem_url: str, api_key: str = None, siem_type: str = "generic"):
    """
    Envia um evento (dict) para um SIEM via HTTP POST.
    Suporta: Splunk, ELK, QRadar, Graylog, generic.
    Retorna dict com sucesso, status_code, response_text, error_msg.
    """
    headers = {'Content-Type': 'application/json'}
    if api_key:
        if siem_type.lower() == "splunk":
            headers['Authorization'] = f'Splunk {api_key}'
        elif siem_type.lower() == "qradar":
            headers['SEC'] = api_key
        else:
            headers['Authorization'] = f'Bearer {api_key}'
    try:
        # Adapta o formato do evento conforme o SIEM
        if siem_type.lower() == "elk":
            data = {'@timestamp': event.get('annotated_at'), 'event': event}
        elif siem_type.lower() == "graylog":
            data = {"short_message": event.get('description', 'JWT Event'), "host": "jwt-analyzer", **event}
        else:
            data = event
        resp = requests.post(siem_url, json=data, headers=headers, timeout=5)
        resp.raise_for_status()
        logging.info(f"Evento enviado ao SIEM ({siem_type}) com sucesso: {resp.status_code}")
        return {
            'success': True,
            'status_code': resp.status_code,
            'response_text': resp.text,
            'error_msg': None
        }
    except Exception as e:
        logging.error(f"Falha ao enviar evento ao SIEM ({siem_type}): {e}")
        return {
            'success': False,
            'status_code': None,
            'response_text': None,
            'error_msg': str(e)
        }
