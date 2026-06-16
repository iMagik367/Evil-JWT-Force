"""
EVIL_JWT_FORCE - AI Engine Module
Core decision-making engine for AI-based attack strategies.

This module serves as the central intelligence system for the EVIL_JWT_FORCE tool,
using heuristics, rules, and past logs to make intelligent decisions about attack vectors,
techniques, and approaches to use against JWT implementations.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
import random
import re
import hashlib
import numpy as np
from collections import Counter, defaultdict
import openai
import requests  # Added to support AI21 Studio API calls

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'ai_engine.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AI_ENGINE')

class AIEngine:
    """
    Main AI decision engine for EVIL_JWT_FORCE.
    
    This class handles the decision-making process for attack strategies,
    analyzes results, and learns from past attacks to improve future attempts.
    """
    
    def __init__(self, config_path: str = 'config/ai_config.json'):
        """
        Initialize the AI Engine with configuration settings.
        
        Args:
            config_path: Path to the AI configuration file
        """
        self.config = self._load_config(config_path)
        self.heuristics = self.config.get('heuristics', {})
        self.rules = self.config.get('rules', [])
        self.learning_data = self._load_learning_data()
        self.success_patterns = self.config.get('success_patterns', [])
        self.current_context = {}
        self.nlp_patterns = self.config.get('nlp_patterns', {})
        self.token_embeddings = {}
        self.attack_history = []
        self.semantic_relationships = defaultdict(list)
        self.confidence_thresholds = self.config.get('confidence_thresholds', {
            'high': 0.85,
            'medium': 0.65,
            'low': 0.45
        })
        
        # Configure OpenAI for deep chain-of-thought reasoning
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_model = self.config.get('openai_model', 'gpt-4')
            self.openai = openai
            logger.info("LLM chain-of-thought enabled with model %s", self.openai_model)
        except Exception as e:
            logger.warning("OpenAI API not available: OpenAI chain-of-thought disabled. %s", str(e))
            self.openai = None
            self.openai_model = None
        
        # Configure AI21 Studio for chain-of-thought if available
        ai21_key = os.getenv('AI21_API_KEY')
        if ai21_key:
            self.ai21_key = ai21_key
            self.ai21_model = self.config.get('ai21_model', 'j2-large')
            self.ai21_url = f"https://api.ai21.com/studio/v1/{self.ai21_model}/complete"
            self.ai21_max_tokens = self.config.get('ai21_max_tokens', 500)
            self.ai21_temperature = self.config.get('ai21_temperature', 0.7)
            logger.info("AI21 Studio chain-of-thought enabled with model %s", self.ai21_model)
        else:
            self.ai21_key = None
        
        logger.info("AI Engine initialized with %d rules, %d heuristics, and %d NLP patterns", 
                   len(self.rules), len(self.heuristics), len(self.nlp_patterns))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'heuristics': {
                'jwt_weakness_probability': 0.7,
                'sql_injection_probability': 0.4,
                'none_alg_success_rate': 0.3,
                'brute_force_success_threshold': 0.2,
                'adaptive_timeout': 30
            },
            'rules': [
                {'condition': 'target_uses_jwt', 'action': 'analyze_jwt_structure', 'priority': 10},
                {'condition': 'jwt_header_alg_is_hs256', 'action': 'attempt_brute_force', 'priority': 8},
                {'condition': 'jwt_no_exp', 'action': 'report_vulnerability', 'priority': 9},
                {'condition': 'response_contains_error', 'action': 'adjust_payload', 'priority': 5}
            ],
            'success_patterns': [
                {'pattern': 'admin: true', 'weight': 0.9},
                {'pattern': 'auth_success', 'weight': 0.8},
                {'pattern': 'logged_in', 'weight': 0.7}
            ],
            'nlp_patterns': {
                'authentication_success': [
                    'authenticated', 'authorized', 'successful login', 'welcome', 'access granted',
                    'session created', 'token valid', 'login successful'
                ],
                'authentication_failure': [
                    'invalid credentials', 'unauthorized', 'access denied', 'login failed',
                    'invalid token', 'expired token', 'signature mismatch'
                ],
                'error_disclosure': [
                    'syntax error', 'database error', 'exception', 'stack trace', 'failed to',
                    'error code', 'unexpected error', 'internal server error'
                ],
                'injection_success': [
                    'sql syntax', 'query failed', 'database exception', 'unexpected result',
                    'data retrieval error', 'query syntax'
                ]
            },
            'confidence_thresholds': {
                'high': 0.85,
                'medium': 0.65,
                'low': 0.45
            },
            'semantic_vectors': {
                'enabled': True,
                'vector_size': 32,
                'min_similarity': 0.7
            },
            'learning_rate': 0.1,
            'decision_threshold': 0.6,
            'adaptive_learning': True,
            'context_awareness': True,
            'pattern_recognition': True,
            'ai21_model': 'j2-large',
            'ai21_max_tokens': 500,
            'ai21_temperature': 0.7
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
        """Load previous learning data or initialize new if not available."""
        learning_file = os.path.join('data', 'ai_learning.json')
        
        try:
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No previous learning data found. Initializing new learning dataset.")
                learning_data = {
                    'attack_success_rates': {},
                    'token_patterns': {},
                    'response_signatures': {},
                    'semantic_clusters': {},
                    'vulnerability_correlations': {},
                    'context_patterns': {},
                    'last_updated': datetime.datetime.now().isoformat()
                }
                os.makedirs(os.path.dirname(learning_file), exist_ok=True)
                with open(learning_file, 'w') as f:
                    json.dump(learning_data, f, indent=2)
                return learning_data
        except Exception as e:
            logger.error("Error loading learning data: %s", str(e))
            return {
                'attack_success_rates': {},
                'token_patterns': {},
                'response_signatures': {},
                'semantic_clusters': {},
                'vulnerability_correlations': {},
                'context_patterns': {}
            }
    
    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analyze a JWT token and determine its characteristics and vulnerabilities.
        
        Args:
            token: The JWT token to analyze
        
        Returns:
            Dictionary with token analysis results
        """
        logger.info("Analyzing token: %s...", token[:20] if len(token) > 20 else token)
        
        # Basic structure validation
        parts = token.split('.')
        if len(parts) != 3:
            return {'valid': False, 'error': 'Invalid token structure', 'vulnerabilities': []}
        
        try:
            # Parse header and payload
            from modules.jwt_utils_simple import decode_token_parts
            token_parts = decode_token_parts(token)
            
            # Generate token fingerprint for tracking
            token_fingerprint = self._generate_token_fingerprint(token_parts)
            
            # Identify potential vulnerabilities
            vulnerabilities = []
            header = token_parts.get('header', {})
            payload = token_parts.get('payload', {})
            
            # Advanced vulnerability detection with confidence levels
            if header.get('alg') == 'none':
                vulnerabilities.append({
                    'type': 'none_algorithm', 
                    'severity': 'high', 
                    'confidence': 0.95,
                    'description': 'Token uses "none" algorithm which bypasses signature verification',
                    'exploitation_difficulty': 'easy'
                })
            elif header.get('alg') in ['HS256', 'HS384', 'HS512']:
                vulnerabilities.append({
                    'type': 'brute_force_possible', 
                    'severity': 'medium',
                    'confidence': 0.85,
                    'description': 'HMAC algorithm used, potentially vulnerable to brute force',
                    'exploitation_difficulty': 'medium'
                })
            
            # Check expiration
            if 'exp' not in payload:
                vulnerabilities.append({
                    'type': 'no_expiration', 
                    'severity': 'medium',
                    'confidence': 0.9,
                    'description': 'Token has no expiration time, potentially usable indefinitely',
                    'exploitation_difficulty': 'easy'
                })
            elif payload.get('exp') and self._is_far_future_timestamp(payload.get('exp')):
                vulnerabilities.append({
                    'type': 'far_future_expiration', 
                    'severity': 'low',
                    'confidence': 0.8,
                    'description': 'Token has very distant expiration time',
                    'exploitation_difficulty': 'n/a'
                })
            
            # Check for sensitive data in payload
            for sensitive_field in ['password', 'secret', 'key', 'token', 'auth', 'credential']:
                if any(sensitive_field in key.lower() for key in payload.keys()):
                    vulnerabilities.append({
                        'type': 'sensitive_data_exposure', 
                        'severity': 'high',
                        'confidence': 0.9,
                        'description': f'Token contains potentially sensitive field: {sensitive_field}',
                        'exploitation_difficulty': 'n/a'
                    })
                    break
            
            # Check for kid parameter (potential for injection)
            if 'kid' in header:
                vulnerabilities.append({
                    'type': 'kid_parameter_present', 
                    'severity': 'medium',
                    'confidence': 0.7,
                    'description': 'Token uses "kid" parameter which may be vulnerable to injection',
                    'exploitation_difficulty': 'medium'
                })
            
            # Check for jku parameter (potential for injection)
            if 'jku' in header:
                vulnerabilities.append({
                    'type': 'jku_parameter_present', 
                    'severity': 'medium',
                    'confidence': 0.75,
                    'description': 'Token uses "jku" parameter which may be vulnerable to URL manipulation',
                    'exploitation_difficulty': 'medium'
                })
            
            # Generate semantic embedding for this token
            self._update_token_embedding(token_fingerprint, token_parts)
            
            # Update learning data with this token pattern
            self._update_learning_data('token_patterns', header.get('alg', 'unknown'), 1)
            
            # Perform contextual analysis
            context_analysis = self._analyze_token_context(token_parts)
            
            return {
                'valid': True,
                'header': header,
                'payload': payload,
                'fingerprint': token_fingerprint,
                'vulnerabilities': vulnerabilities,
                'recommended_attacks': self._get_recommended_attacks(token_parts),
                'context_analysis': context_analysis,
                'confidence_score': self._calculate_confidence_score(vulnerabilities)
            }
            
        except Exception as e:
            logger.error("Error analyzing token: %s", str(e))
            return {'valid': False, 'error': str(e), 'vulnerabilities': []}
    
    def _generate_token_fingerprint(self, token_parts: Dict[str, Any]) -> str:
        """Generate a unique fingerprint for a token based on its structure."""
        try:
            header_keys = sorted(list(token_parts.get('header', {}).keys()))
            payload_keys = sorted(list(token_parts.get('payload', {}).keys()))
            alg = token_parts.get('header', {}).get('alg', 'unknown')
            
            fingerprint_base = f"{alg}:{','.join(header_keys)}:{','.join(payload_keys)}"
            return hashlib.sha256(fingerprint_base.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error generating token fingerprint: {str(e)}")
            return hashlib.sha256(str(token_parts).encode()).hexdigest()[:16]
    
    def _is_far_future_timestamp(self, timestamp: int) -> bool:
        """Check if a timestamp is far in the future (> 10 years)."""
        try:
            current_time = datetime.datetime.now().timestamp()
            ten_years_in_seconds = 10 * 365 * 24 * 60 * 60
            return timestamp > (current_time + ten_years_in_seconds)
        except:
            return False
    
    def _update_token_embedding(self, token_fingerprint: str, token_parts: Dict[str, Any]) -> None:
        """Generate and store a simple semantic embedding for a token."""
        if not self.config.get('semantic_vectors', {}).get('enabled', False):
            return
            
        try:
            # Create a simple embedding based on token characteristics
            # In a production environment, this would use proper NLP embeddings
            header = token_parts.get('header', {})
            payload = token_parts.get('payload', {})
            
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
    
    def _analyze_token_context(self, token_parts: Dict[str, Any]) -> Dict[str, Any]:
        """Perform contextual analysis of the token to identify patterns and context."""
        context = {}
        payload = token_parts.get('payload', {})
        
        # Identify potential context from issuer
        if 'iss' in payload:
            issuer = payload['iss']
            context['issuer_type'] = self._classify_issuer(issuer)
            context['issuer_domain'] = self._extract_domain(issuer)
        
        # Identify user context
        if 'sub' in payload:
            subject = payload['sub']
            context['subject_type'] = self._classify_subject(subject)
            
        # Identify potential application context
        if 'aud' in payload:
            audience = payload['aud']
            context['audience_type'] = self._classify_audience(audience)
            
        # Analyze custom claims to identify application type
        custom_claims = [k for k in payload.keys() if k not in ['iss', 'sub', 'aud', 'exp', 'nbf', 'iat', 'jti']]
        if custom_claims:
            context['application_type'] = self._identify_application_type(custom_claims, payload)
            
        # Determine token usage context
        context['token_usage'] = self._determine_token_usage(token_parts)
        
        return context
    
    def _classify_issuer(self, issuer: str) -> str:
        """Classify the type of issuer based on the issuer string."""
        if not issuer:
            return 'unknown'
            
        issuer_lower = issuer.lower()
        
        if re.search(r'(oauth|oidc|auth0|okta|keycloak|cognito)', issuer_lower):
            return 'identity_provider'
        elif re.search(r'(api|gateway|service)', issuer_lower):
            return 'api_gateway'
        elif re.search(r'(app|application)', issuer_lower):
            return 'application'
        elif re.search(r'^https?://', issuer_lower):
            return 'url_based'
        else:
            return 'custom'
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from a URL if present."""
        if not url:
            return 'unknown'
            
        match = re.search(r'https?://([^/]+)', url)
        if match:
            return match.group(1)
        return 'not_url'
    
    def _classify_subject(self, subject: str) -> str:
        """Classify the type of subject based on the subject string."""
        if not subject:
            return 'unknown'
            
        subject_lower = str(subject).lower()
        
        if re.search(r'^[0-9]+$', subject_lower):
            return 'numeric_id'
        elif re.search(r'@', subject_lower):
            return 'email'
        elif re.search(r'(admin|root|administrator|superuser)', subject_lower):
            return 'administrative'
        elif re.search(r'(service|api|bot)', subject_lower):
            return 'service_account'
        elif re.search(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', subject_lower):
            return 'uuid'
        else:
            return 'username'
    
    def _classify_audience(self, audience: Any) -> str:
        """Classify the type of audience based on the audience value."""
        if not audience:
            return 'unknown'
            
        # Handle list/array audience
        if isinstance(audience, list):
            if len(audience) > 1:
                return 'multiple'
            elif len(audience) == 1:
                audience = audience[0]
            else:
                return 'empty_list'
                
        audience_str = str(audience).lower()
        
        if re.search(r'(api|service|resource)', audience_str):
            return 'api'
        elif re.search(r'(app|application|client)', audience_str):
            return 'application'
        elif re.search(r'^https?://', audience_str):
            return 'url'
        else:
            return 'custom'
    
    def _identify_application_type(self, custom_claims: List[str], payload: Dict[str, Any]) -> str:
        """Identify the type of application based on custom claims."""
        # Look for common patterns in claims
        auth0_claims = ['https://claims', 'permissions', 'roles', 'nickname']
        cognito_claims = ['cognito:groups', 'cognito:username', 'token_use']
        firebase_claims = ['firebase', 'sign_in_provider', 'uid']
        
        auth0_matches = sum(1 for claim in custom_claims if any(ac in claim for ac in auth0_claims))
        cognito_matches = sum(1 for claim in custom_claims if any(cc in claim for cc in cognito_claims))
        firebase_matches = sum(1 for claim in custom_claims if any(fc in claim for fc in firebase_claims))
        
        if auth0_matches >= 2:
            return 'auth0'
        elif cognito_matches >= 2:
            return 'aws_cognito'
        elif firebase_matches >= 2:
            return 'firebase'
        elif 'scope' in custom_claims:
            return 'oauth2'
        elif 'realm_access' in custom_claims or 'resource_access' in custom_claims:
            return 'keycloak'
        elif 'azp' in custom_claims or 'scp' in custom_claims:
            return 'azure_ad'
        elif 'groups' in custom_claims and 'name' in custom_claims:
            return 'generic_identity_provider'
        elif any(claim for claim in custom_claims if 'role' in claim.lower()):
            return 'role_based'
        else:
            return 'custom'
    
    def _determine_token_usage(self, token_parts: Dict[str, Any]) -> str:
        """Determine the likely usage context of the token."""
        header = token_parts.get('header', {})
        payload = token_parts.get('payload', {})
        
        # Check for access token indicators
        if 'scope' in payload or 'scp' in payload:
            return 'access_token'
            
        # Check for ID token indicators
        if any(claim in payload for claim in ['name', 'email', 'given_name', 'family_name']):
            return 'id_token'
            
        # Check for refresh token indicators (rare in JWT)
        if 'refresh' in str(payload).lower():
            return 'refresh_token'
            
        # Check for session token
        if 'session' in str(payload).lower():
            return 'session_token'
            
        return 'general_purpose'
    
    def _calculate_confidence_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate an overall confidence score for the vulnerability assessment."""
        if not vulnerabilities:
            return 0.0
            
        total_confidence = sum(vuln.get('confidence', 0.5) for vuln in vulnerabilities)
        return total_confidence / len(vulnerabilities)
    
    def decide_attack_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide the best attack strategy based on the current context.
        
        Args:
            context: Dictionary containing information about the target
        
        Returns:
            Dictionary with attack strategy information
        """
        self.current_context = context
        
        # Apply rules based on context
        applicable_rules = []
        for rule in self.rules:
            if self._evaluate_condition(rule['condition'], context):
                applicable_rules.append(rule)
        
        # Sort by priority
        applicable_rules.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # Generate attack plan
        attack_plan = {
            'primary_vector': self._select_primary_attack_vector(context),
            'secondary_vectors': self._select_secondary_attack_vectors(context),
            'steps': [rule['action'] for rule in applicable_rules[:3]],
            'estimated_success_rate': self._calculate_success_probability(context),
            'adaptive': True
        }
        
        logger.info("Selected attack strategy: %s (%.2f%% estimated success)", 
                   attack_plan['primary_vector'], 
                   attack_plan['estimated_success_rate'] * 100)
        
        # Generate deep reasoning rationale via LLM
        if self.openai:
            try:
                rationale = self._chain_of_thought(self.current_context, attack_plan)
                attack_plan['rationale'] = rationale
            except Exception:
                pass
        
        return attack_plan
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate if a rule condition is met in the current context."""
        # Simple condition evaluation
        if condition == 'target_uses_jwt' and context.get('has_jwt', False):
            return True
        elif condition == 'jwt_header_alg_is_hs256' and context.get('jwt_alg') == 'HS256':
            return True
        elif condition == 'jwt_no_exp' and not context.get('jwt_has_exp', True):
            return True
        elif condition == 'response_contains_error' and context.get('response_has_error', False):
            return True
        
        return False
    
    def _select_primary_attack_vector(self, context: Dict[str, Any]) -> str:
        """Select the primary attack vector based on context and learning data."""
        if context.get('jwt_alg') == 'none':
            return 'none_algorithm_exploit'
        elif context.get('jwt_alg') == 'HS256':
            return 'brute_force'
        elif not context.get('jwt_has_exp', True):
            return 'token_manipulation'
        elif context.get('allows_header_injection', False):
            return 'header_injection'
        else:
            # Default to JWT fuzzing
            return 'jwt_fuzzing'
    
    def _select_secondary_attack_vectors(self, context: Dict[str, Any]) -> List[str]:
        """Select secondary attack vectors based on context."""
        vectors = []
        
        if context.get('has_api', False):
            vectors.append('api_enumeration')
        
        if context.get('has_web_interface', False):
            vectors.append('parameter_tampering')
        
        if context.get('response_contains_json', False):
            vectors.append('json_injection')
        
        # Add some randomness to exploration
        if random.random() < 0.3:
            vectors.append('header_manipulation')
        
        return vectors
    
    def _calculate_success_probability(self, context: Dict[str, Any]) -> float:
        """Calculate the estimated probability of success for the attack."""
        base_probability = 0.5  # Base chance
        
        # Adjust based on vulnerabilities
        if context.get('jwt_alg') == 'none':
            base_probability += self.heuristics.get('none_alg_success_rate', 0.3)
        elif context.get('jwt_alg') == 'HS256':
            base_probability += 0.2
        
        if not context.get('jwt_has_exp', True):
            base_probability += 0.1
        
        # Cap at 0.9 (90% chance)
        return min(0.9, base_probability)
    
    def _get_recommended_attacks(self, token_parts: Dict[str, Any]) -> List[str]:
        """Get recommended attack methods based on token analysis."""
        recommended = []
        
        header = token_parts.get('header', {})
        payload = token_parts.get('payload', {})
        
        # Check algorithm-based attacks
        alg = header.get('alg', '')
        if alg == 'none':
            recommended.append('none_algorithm_exploit')
        elif alg in ['HS256', 'HS384', 'HS512']:
            recommended.append('brute_force')
        elif alg in ['RS256', 'ES256']:
            recommended.append('key_confusion')
        
        # Check payload-based attacks
        if 'exp' not in payload:
            recommended.append('token_manipulation')
        
        # Add fuzzing as a general approach
        if len(recommended) == 0:
            recommended.append('jwt_fuzzing')
        
        return recommended
    
    def _update_learning_data(self, category: str, key: str, value: int) -> None:
        """Update learning data with new information."""
        if category not in self.learning_data:
            self.learning_data[category] = {}
        
        if key not in self.learning_data[category]:
            self.learning_data[category][key] = 0
        
        self.learning_data[category][key] += value
        
        # Save updated data
        learning_file = os.path.join('data', 'ai_learning.json')
        try:
            os.makedirs(os.path.dirname(learning_file), exist_ok=True)
            with open(learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logger.error("Error saving learning data: %s", str(e))
    
    def process_attack_result(self, attack_type: str, success: bool, details: Dict[str, Any]) -> None:
        """
        Process the result of an attack attempt to improve future decisions.
        
        Args:
            attack_type: Type of attack that was attempted
            success: Whether the attack was successful
            details: Additional details about the attack and result
        """
        logger.info("Processing attack result for %s: %s", attack_type, "Success" if success else "Failure")
        
        # Update success rates for this attack type
        if 'attack_success_rates' not in self.learning_data:
            self.learning_data['attack_success_rates'] = {}
        
        if attack_type not in self.learning_data['attack_success_rates']:
            self.learning_data['attack_success_rates'][attack_type] = {
                'attempts': 0,
                'successes': 0
            }
        
        self.learning_data['attack_success_rates'][attack_type]['attempts'] += 1
        if success:
            self.learning_data['attack_success_rates'][attack_type]['successes'] += 1
        
        # Update specific learning from this attempt
        if 'response_code' in details:
            self._update_learning_data('response_codes', str(details['response_code']), 1)
        
        if 'error_message' in details and details['error_message']:
            self._update_learning_data('error_messages', details['error_message'][:50], 1)
        
        # Save updated data
        self.learning_data['last_updated'] = datetime.datetime.now().isoformat()
        learning_file = os.path.join('data', 'ai_learning.json')
        try:
            with open(learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logger.error("Error saving learning data: %s", str(e))
    
    def get_attack_recommendations(self, token: str, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive attack recommendations for a JWT token.
        
        Args:
            token: The JWT token to analyze
            target_info: Information about the target
            
        Returns:
            Dictionary with attack recommendations
        """
        # Analyze the token
        token_analysis = self.analyze_token(token)
        
        # Prepare context for decision making
        context = target_info.copy()
        
        if token_analysis.get('valid', False):
            header = token_analysis.get('header', {})
            payload = token_analysis.get('payload', {})
            
            context['jwt_alg'] = header.get('alg')
            context['jwt_has_exp'] = 'exp' in payload
            context['has_jwt'] = True
        
        # Decide attack strategy
        attack_strategy = self.decide_attack_strategy(context)
        
        # Compile recommendations
        recommendations = {
            'token_analysis': token_analysis,
            'attack_strategy': attack_strategy,
            'vulnerabilities': token_analysis.get('vulnerabilities', []),
            'recommended_tools': self._recommend_tools(attack_strategy['primary_vector']),
            'estimated_time': self._estimate_attack_time(attack_strategy),
            'confidence': attack_strategy['estimated_success_rate']
        }
        
        # Add deep reasoning rationale for recommendations
        if self.openai:
            try:
                cot_context = target_info.copy()
                cot_context['token_analysis'] = token_analysis
                rationale = self._chain_of_thought(cot_context, recommendations)
                recommendations['rationale'] = rationale
            except Exception:
                pass
        
        return recommendations
    
    def _recommend_tools(self, attack_vector: str) -> List[str]:
        """Recommend specific tools for an attack vector."""
        tool_map = {
            'brute_force': ['jwt_bruteforcer', 'hashcat', 'john'],
            'none_algorithm_exploit': ['jwt_tool', 'burp_jwt_extension'],
            'key_confusion': ['jwt_tool', 'jwt_forgery'],
            'token_manipulation': ['jwt_tool', 'jwt_editor'],
            'header_injection': ['burp_collaborator', 'jwt_tool'],
            'jwt_fuzzing': ['jwt_fuzzer', 'wfuzz']
        }
        
        return tool_map.get(attack_vector, ['jwt_tool'])
    
    def _estimate_attack_time(self, attack_strategy: Dict[str, Any]) -> str:
        """Estimate the time needed for an attack strategy."""
        if attack_strategy['primary_vector'] == 'brute_force':
            return "1-24 hours depending on wordlist size"
        elif attack_strategy['primary_vector'] == 'none_algorithm_exploit':
            return "Less than 5 minutes"
        elif attack_strategy['primary_vector'] == 'key_confusion':
            return "15-30 minutes"
        elif attack_strategy['primary_vector'] == 'token_manipulation':
            return "10-20 minutes"
        else:
            return "Varies based on target response time"

    def _chain_of_thought(self, context: Dict[str, Any], plan: Dict[str, Any]) -> str:
        """Use an LLM to generate chain-of-thought reasoning to refine the plan."""
        # Build a more engaging, step-by-step reasoning prompt
        prompt = (
            f"Você é um especialista em segurança cibernética com vasta experiência em ataques adaptativos coordenados. "
            f"Com base no contexto a seguir: {json.dumps(context)} e no plano inicial: {json.dumps(plan)}, "
            f"forneça um raciocínio detalhado em linguagem natural, passo a passo (chain-of-thought), "
            f"explicando suas decisões, hipóteses e estratégias para cada etapa do processo."
        )
        # First try AI21 Studio if configured
        if self.ai21_key:
            try:
                payload = {
                    "prompt": prompt,
                    "maxTokens": self.ai21_max_tokens,
                    "temperature": self.ai21_temperature
                }
                headers = {
                    "Authorization": f"Bearer {self.ai21_key}",
                    "Content-Type": "application/json"
                }
                r = requests.post(self.ai21_url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
                return data.get("completions", [])[0].get("data", {}).get("text", "")
            except Exception as e:
                logger.error("AI21 chain-of-thought error: %s", str(e))
        # Fallback to OpenAI if configured
        if self.openai:
            try:
                response = self.openai.ChatCompletion.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "Você é um assistente de segurança cibernética avançado, forneça raciocínio aprofundado."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.get("openai_temperature", 0.7),
                    max_tokens=self.config.get("openai_max_tokens", 500)
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error("OpenAI chain-of-thought error: %s", str(e))
        return ""

    def generate_wordlist(self, context):
        """Generate a wordlist based on scraped data from social media, Google, and specific domains."""
        scraped_data = self._scrape_data_for_wordlist()
        wordlist = self._process_scraped_data_to_wordlist(scraped_data)
        return wordlist

    def _scrape_data_for_wordlist(self):
        """Scrape data from social media, Google, and domains like .org and .gov for wordlist generation."""
        # Placeholder for scraping logic
        return "Scraped data from social media, Google, .org, and .gov domains (Note: Actual scraping must be implemented and executed manually in compliance with legal and ethical guidelines)."

    def _process_scraped_data_to_wordlist(self, scraped_data):
        """Process scraped data into a usable wordlist for brute force testing."""
        return ["example_word1", "example_word2", "example_word3"]  # Placeholder wordlist


if __name__ == "__main__":
    # Example usage
    engine = AIEngine()
    
    # Example token for testing
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Analyze token
    analysis = engine.analyze_token(test_token)
    print("Token Analysis:", json.dumps(analysis, indent=2))
    
    # Get attack recommendations
    target_info = {
        'has_api': True,
        'has_web_interface': True,
        'response_contains_json': True,
        'allows_header_injection': False
    }
    
    recommendations = engine.get_attack_recommendations(test_token, target_info)
    print("Attack Recommendations:", json.dumps(recommendations, indent=2)) 