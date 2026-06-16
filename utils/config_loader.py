import os
from typing import Dict, Any
from .config_encryptor import ConfigEncryptor

class ConfigLoader:
    _instance = None
    _config_cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.encryptor = ConfigEncryptor()
            self.initialized = True
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys from encrypted config file"""
        if self._config_cache is None:
            config_path = os.path.join('config', 'config.enc')
            if not os.path.exists(config_path):
                raise FileNotFoundError("Encrypted config file not found")
            
            self._config_cache = self.encryptor.decrypt_config(config_path)
        
        # Extract only API keys
        api_keys = {}
        for key in ['openai_key', 'shodan_key', 'veriphone_key']:
            if key in self._config_cache:
                api_keys[key] = self._config_cache[key]
        
        return api_keys
    
    def get_config(self) -> Dict[str, Any]:
        """Get full decrypted config"""
        if self._config_cache is None:
            config_path = os.path.join('config', 'config.enc')
            if not os.path.exists(config_path):
                raise FileNotFoundError("Encrypted config file not found")
            
            self._config_cache = self.encryptor.decrypt_config(config_path)
        
        return self._config_cache
    
    def clear_cache(self):
        """Clear the config cache"""
        self._config_cache = None

# Global instance
config_loader = ConfigLoader()

def get_api_keys() -> Dict[str, str]:
    """Global function to get API keys"""
    return config_loader.get_api_keys()

def get_config() -> Dict[str, Any]:
    """Global function to get full config"""
    return config_loader.get_config() 