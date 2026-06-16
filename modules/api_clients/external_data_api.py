import os
import json
import requests
from pathlib import Path
from config.config_loader import load_config

# Load API keys from configuration
top_config = load_config()
external_keys = top_config.get('external_apis', {})

class IPStackAPI:
    @staticmethod
    def get_location(ip: str) -> dict:
        """Retorna geolocalização para o IP fornecido."""
        key = external_keys.get('ipstack_key', '')
        url = f"http://api.ipstack.com/{ip}?access_key={key}"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            # Cache response
            cache_dir = Path('output/api_cache/ipstack')
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_dir / f"{ip}.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            return {'error': str(e)}

class MarketStackAPI:
    @staticmethod
    def get_stock(symbol: str) -> dict:
        """Retorna dados de cotação para o símbolo de ação fornecido."""
        key = external_keys.get('marketstack_key', '')
        url = f"http://api.marketstack.com/v1/eod?symbols={symbol}&access_key={key}"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            cache_dir = Path('output/api_cache/marketstack')
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_dir / f"{symbol}.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            return {'error': str(e)}

class WeatherStackAPI:
    @staticmethod
    def get_weather(location: str) -> dict:
        """Retorna informações climáticas para a localização fornecida (cidade)."""
        key = external_keys.get('weatherstack_key', '')
        url = f"http://api.weatherstack.com/current?access_key={key}&query={location}"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            cache_dir = Path('output/api_cache/weatherstack')
            cache_dir.mkdir(parents=True, exist_ok=True)
            filename = location.replace(' ', '_') + '.json'
            with open(cache_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            return {'error': str(e)}

class FixerAPI:
    @staticmethod
    def get_conversion(from_currency: str, to_currency: str) -> dict:
        """Retorna taxa de conversão entre duas moedas."""
        key = external_keys.get('fixer_key', '')
        url = f"http://data.fixer.io/api/convert?access_key={key}&from={from_currency}&to={to_currency}&amount=1"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            cache_dir = Path('output/api_cache/fixer')
            cache_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{from_currency}_{to_currency}.json"
            with open(cache_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            return {'error': str(e)}

class NumVerifyAPI:
    @staticmethod
    def validate(phone_number: str) -> dict:
        """Valida número de telefone e retorna detalhes."""
        key = external_keys.get('numverify_key', '')
        url = f"http://apilayer.net/api/validate?access_key={key}&number={phone_number}"
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            cache_dir = Path('output/api_cache/numverify')
            cache_dir.mkdir(parents=True, exist_ok=True)
            filename = phone_number.replace('+','') + '.json'
            with open(cache_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        except Exception as e:
            return {'error': str(e)} 