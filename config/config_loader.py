import yaml
import os

def load_config():
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)
    
    # External APIs (IPStack, MarketStack, WeatherStack, Fixer, NumVerify)
    ext = config.get('external_apis', {})
    config['external_apis'] = {
        'ipstack_key': os.getenv('IPSTACK_KEY', ext.get('ipstack_key', '')),
        'marketstack_key': os.getenv('MARKETSTACK_KEY', ext.get('marketstack_key', '')),
        'weatherstack_key': os.getenv('WEATHERSTACK_KEY', ext.get('weatherstack_key', '')),
        'fixer_key': os.getenv('FIXER_KEY', ext.get('fixer_key', '')),
        'numverify_key': os.getenv('NUMVERIFY_KEY', ext.get('numverify_key', '')),
        'receitaws_key': os.getenv('RECEITAWS_KEY', ext.get('receitaws_key', '')),
        'census_gov_key': os.getenv('CENSUS_GOV_KEY', ext.get('census_gov_key', '')),
        'veriphone_key': os.getenv('VERIPHONE_KEY', ext.get('veriphone_key', '')),
        'haveibeenpwned_key': os.getenv('HAVEIBEENPWNED_KEY', ext.get('haveibeenpwned_key', ''))
    }
    
    config['pentestgpt'] = {
        'api_key': os.getenv('PENTESTGPT_API_KEY', 'sua_chave_aqui'),
        'endpoint': 'https://api.pentestgpt.com/v1'
    }
    return config

def load_ai_config():
    return {
        'pentestgpt_key': os.getenv('PENTESTGPT_API_KEY', '')
    }

def load_headers_template():
    """Carrega o template de headers definido em config.yaml"""
    cfg = load_config()
    return cfg.get('headers_template', {})