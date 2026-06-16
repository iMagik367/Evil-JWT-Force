"""
EVIL_JWT_FORCE - Context Analyzer Module
This module analyzes HTTP responses and target context to adapt attack strategies.

It uses pattern recognition and heuristics to identify vulnerabilities, authentication
mechanisms, and response behaviors that can be exploited.
"""

import os
import json
import logging
import re
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'context_analyzer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CONTEXT_ANALYZER')

class ContextAnalyzer:
    """
    Analyzes HTTP responses and target context to optimize attack strategies.
    
    This class identifies patterns in responses, detects authentication mechanisms,
    and extracts information that can be used to adapt attack strategies.
    """
    
    def __init__(self, config_path: str = 'config/analyzer_config.json'):
        """
        Initialize the Context Analyzer with configuration settings.
        
        Args:
            config_path: Path to the analyzer configuration file
        """
        self.config = self._load_config(config_path)
        self.response_patterns = self.config.get('response_patterns', {})
        self.jwt_patterns = self.config.get('jwt_patterns', {})
        self.context_history = {}
        self.target_signatures = {}
        self.current_target = None
        
        # Advanced language learning data stores
        self.token_fingerprints: Dict[str, str] = {}
        self.token_semantic_vectors: Dict[str, List[float]] = {}
        
        logger.info("Context Analyzer initialized with %d response patterns and %d JWT patterns", 
                   len(self.response_patterns), len(self.jwt_patterns))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'response_patterns': {
                'auth_success': r"(authentication successful|login successful|auth[:\s]+true|\"token\")",
                'auth_failure': r"(authentication failed|invalid credentials|incorrect password|auth[:\s]+false)",
                'jwt_token': r"(jwt|token|access_token|id_token)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)",
                'error_message': r"(error|exception|warning)[\"']?\s*[:=]\s*[\"']?([^\"'}\]]+)",
                'sql_error': r"(SQL syntax|mysql_fetch|mysqli_|ODBC|ORA-\d{5}|PostgreSQL|syntax error at|unclosed quotation mark)",
                'server_info': r"(apache|nginx|iis|tomcat|node\.js|php|asp\.net|ruby|python|django|flask|express)",
                'csrf_token': r"(csrf|xsrf)[_-]?token[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9+/=_-]+)",
                'api_version': r"(api[_-]?version|version)[\"']?\s*[:=]\s*[\"']?([0-9\.]+)"
            },
            'jwt_patterns': {
                'weak_algorithm': {
                    'pattern': '"alg"\\s*:\\s*"(none|HS256)"',
                    'description': "Uses either 'none' algorithm or HS256 which may be vulnerable to brute force"
                },
                'missing_exp': {
                    'pattern': '(?!"exp")',
                    'description': "JWT does not contain expiration claim"
                },
                'sensitive_data': {
                    'pattern': '"(password|secret|key|credential)"\\s*:',
                    'description': "JWT contains sensitive data in payload"
                },
                'admin_role': {
                    'pattern': '"(role|admin|isAdmin|is_admin)"\\s*:\\s*("admin"|true)',
                    'description': "JWT contains admin role indicator"
                }
            },
            'response_flags': {
                'has_auth_mechanism': False,
                'uses_jwt': False,
                'has_csrf': False,
                'has_api': False,
                'shows_errors': False,
                'leaks_server_info': False
            },
            'signature_weight': {
                'headers': 0.4,
                'response_format': 0.3,
                'error_format': 0.2,
                'auth_method': 0.1
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
    
    def analyze_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an HTTP response to extract useful information.
        
        Args:
            response: Dictionary containing HTTP response data
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing HTTP response from %s", response.get('url', 'unknown'))
        
        # Initialize analysis results
        analysis = {
            'url': response.get('url', ''),
            'status_code': response.get('status_code', 0),
            'response_time': response.get('response_time', 0),
            'content_type': response.get('headers', {}).get('Content-Type', ''),
            'server': response.get('headers', {}).get('Server', ''),
            'patterns_found': {},
            'jwt_analysis': {},
            'context_flags': self.config.get('response_flags', {}).copy(),
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract response body
        response_body = response.get('body', '')
        if not response_body:
            logger.warning("Empty response body")
            return analysis
        
        # Check for response patterns
        for pattern_name, pattern in self.response_patterns.items():
            matches = re.findall(pattern, response_body, re.IGNORECASE)
            if matches:
                analysis['patterns_found'][pattern_name] = matches
                logger.info("Found pattern '%s' in response", pattern_name)
                
                # Set context flags based on patterns
                if pattern_name == 'auth_success' or pattern_name == 'auth_failure':
                    analysis['context_flags']['has_auth_mechanism'] = True
                elif pattern_name == 'jwt_token':
                    analysis['context_flags']['uses_jwt'] = True
                    # Extract and analyze JWT tokens
                    for match in matches:
                        if isinstance(match, tuple) and len(match) > 1:
                            jwt_token = match[1]
                            jwt_analysis = self.analyze_jwt(jwt_token)
                            if jwt_analysis:
                                analysis['jwt_analysis'][jwt_token] = jwt_analysis
                elif pattern_name == 'csrf_token':
                    analysis['context_flags']['has_csrf'] = True
                elif pattern_name == 'api_version':
                    analysis['context_flags']['has_api'] = True
                elif pattern_name == 'error_message' or pattern_name == 'sql_error':
                    analysis['context_flags']['shows_errors'] = True
                elif pattern_name == 'server_info':
                    analysis['context_flags']['leaks_server_info'] = True
        
        # Generate signature for this response
        signature = self._generate_response_signature(response)
        analysis['signature'] = signature
        
        # Store in target signatures if we have a current target
        if self.current_target:
            if self.current_target not in self.target_signatures:
                self.target_signatures[self.current_target] = []
            
            self.target_signatures[self.current_target].append({
                'url': response.get('url', ''),
                'signature': signature,
                'timestamp': datetime.now().isoformat()
            })
        
        # Generate recommendations based on analysis
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def analyze_jwt(self, token: str) -> Dict[str, Any]:
        """
        Analyze a JWT token to identify vulnerabilities and characteristics.
        
        Args:
            token: The JWT token to analyze
            
        Returns:
            Dictionary with JWT analysis results
        """
        try:
            # Basic validation of JWT format
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid JWT format: %s", token[:20])
                return {'valid': False, 'error': 'Invalid JWT format'}
            
            # Decode header and payload
            try:
                header_json = base64.b64decode(self._add_padding(parts[0])).decode('utf-8')
                payload_json = base64.b64decode(self._add_padding(parts[1])).decode('utf-8')
                
                header = json.loads(header_json)
                payload = json.loads(payload_json)
            except Exception as e:
                logger.warning("Error decoding JWT parts: %s", str(e))
                return {'valid': False, 'error': f'Error decoding JWT: {str(e)}'}
            
            # Initialize analysis
            analysis = {
                'valid': True,
                'header': header,
                'payload': payload,
                'algorithm': header.get('alg', 'unknown'),
                'vulnerabilities': [],
                'claims': list(payload.keys())
            }
            
            # Check for vulnerabilities based on patterns
            for vuln_name, vuln_info in self.jwt_patterns.items():
                pattern = vuln_info['pattern']
                
                # Check header
                if re.search(pattern, header_json, re.IGNORECASE):
                    analysis['vulnerabilities'].append({
                        'type': vuln_name,
                        'location': 'header',
                        'description': vuln_info['description']
                    })
                
                # Check payload
                if re.search(pattern, payload_json, re.IGNORECASE):
                    analysis['vulnerabilities'].append({
                        'type': vuln_name,
                        'location': 'payload',
                        'description': vuln_info['description']
                    })
            
            # Check specific vulnerabilities
            if header.get('alg') == 'none':
                analysis['vulnerabilities'].append({
                    'type': 'none_algorithm',
                    'location': 'header',
                    'description': "Uses 'none' algorithm which may bypass signature verification"
                })
            
            if 'exp' not in payload:
                analysis['vulnerabilities'].append({
                    'type': 'no_expiration',
                    'location': 'payload',
                    'description': "Token does not expire"
                })
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing JWT: %s", str(e))
            return {'valid': False, 'error': str(e)}
    
    def _add_padding(self, encoded: str) -> str:
        """Add padding to base64 encoded string."""
        padding_needed = len(encoded) % 4
        if padding_needed:
            encoded += '=' * (4 - padding_needed)
        return encoded
    
    def _generate_response_signature(self, response: Dict[str, Any]) -> str:
        """Generate a signature for the response to identify similar endpoints."""
        # Extract components for signature
        status = response.get('status_code', 0)
        headers = sorted(response.get('headers', {}).keys())
        content_type = response.get('headers', {}).get('Content-Type', '')
        
        # Create a string representation of the response characteristics
        signature_parts = [
            f"status:{status}",
            f"headers:{','.join(headers)}",
            f"content-type:{content_type}"
        ]
        
        # Add content structure hint (without specific values)
        body = response.get('body', '')
        if body:
            if content_type and 'json' in content_type.lower():
                try:
                    # For JSON, include the keys structure
                    json_data = json.loads(body)
                    if isinstance(json_data, dict):
                        signature_parts.append(f"json-keys:{','.join(sorted(json_data.keys()))}")
                except:
                    pass
            elif content_type and 'html' in content_type.lower():
                # For HTML, add a hint about form presence
                if '<form' in body.lower():
                    signature_parts.append("has-form:true")
                
                if 'login' in body.lower() or 'signin' in body.lower():
                    signature_parts.append("has-login:true")
        
        # Create signature string and hash it
        signature_str = "|".join(signature_parts)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on the response analysis."""
        recommendations = []
        
        # Check if JWT is used
        if analysis['context_flags']['uses_jwt']:
            recommendations.append({
                'type': 'jwt_analysis',
                'description': 'JWT tokens detected, analyze them for vulnerabilities',
                'priority': 'high'
            })
            
            # Check for specific JWT vulnerabilities
            for token, jwt_analysis in analysis.get('jwt_analysis', {}).items():
                for vuln in jwt_analysis.get('vulnerabilities', []):
                    if vuln['type'] == 'none_algorithm':
                        recommendations.append({
                            'type': 'alg_none_attack',
                            'description': "Try 'none' algorithm attack on JWT",
                            'priority': 'high',
                            'token': token[:20] + '...'
                        })
                    elif vuln['type'] == 'no_expiration':
                        recommendations.append({
                            'type': 'token_manipulation',
                            'description': 'JWT has no expiration, try token manipulation',
                            'priority': 'medium',
                            'token': token[:20] + '...'
                        })
        
        # Check for authentication mechanism
        if analysis['context_flags']['has_auth_mechanism']:
            recommendations.append({
                'type': 'auth_test',
                'description': 'Authentication mechanism detected, test for weaknesses',
                'priority': 'high'
            })
        
        # Check for error messages
        if analysis['context_flags']['shows_errors']:
            recommendations.append({
                'type': 'error_analysis',
                'description': 'Error messages detected, analyze for information disclosure',
                'priority': 'medium'
            })
            
            # Check for SQL errors specifically
            if 'sql_error' in analysis.get('patterns_found', {}):
                recommendations.append({
                    'type': 'sql_injection',
                    'description': 'SQL error detected, try SQL injection attacks',
                    'priority': 'high'
                })
        
        # Check for server information
        if analysis['context_flags']['leaks_server_info']:
            recommendations.append({
                'type': 'server_analysis',
                'description': 'Server information leaked, check for known vulnerabilities',
                'priority': 'medium'
            })
        
        # Check for CSRF protection
        if analysis['context_flags']['has_csrf']:
            recommendations.append({
                'type': 'csrf_analysis',
                'description': 'CSRF token detected, analyze token generation pattern',
                'priority': 'low'
            })
        
        return recommendations
    
    def set_target(self, target_url: str) -> None:
        """
        Set the current target for context tracking.
        
        Args:
            target_url: The base URL of the target
        """
        self.current_target = target_url
        logger.info("Set current target to: %s", target_url)
        
        # Initialize context history for this target if needed
        if target_url not in self.context_history:
            self.context_history[target_url] = {
                'first_seen': datetime.now().isoformat(),
                'responses': [],
                'endpoints': set(),
                'auth_endpoints': set(),
                'tokens': {},
                'vulnerabilities': []
            }
    
    def update_context_history(self, url: str, analysis: Dict[str, Any]) -> None:
        """
        Update the context history with new response analysis.
        
        Args:
            url: The URL of the analyzed response
            analysis: The analysis results
        """
        if not self.current_target or self.current_target not in self.context_history:
            logger.warning("No current target set or target not in context history")
            return
        
        # Add endpoint to known endpoints
        self.context_history[self.current_target]['endpoints'].add(url)
        
        # Check if this is an auth endpoint
        if analysis['context_flags']['has_auth_mechanism']:
            self.context_history[self.current_target]['auth_endpoints'].add(url)
        
        # Store tokens
        for token, jwt_analysis in analysis.get('jwt_analysis', {}).items():
            self.context_history[self.current_target]['tokens'][token] = jwt_analysis
        
        # Store vulnerabilities
        for token_analysis in analysis.get('jwt_analysis', {}).values():
            for vuln in token_analysis.get('vulnerabilities', []):
                self.context_history[self.current_target]['vulnerabilities'].append({
                    'type': 'jwt_vulnerability',
                    'subtype': vuln['type'],
                    'description': vuln['description'],
                    'url': url,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Store limited response history
        response_summary = {
            'url': url,
            'status_code': analysis['status_code'],
            'patterns_found': list(analysis.get('patterns_found', {}).keys()),
            'timestamp': analysis['timestamp']
        }
        
        responses = self.context_history[self.current_target]['responses']
        responses.append(response_summary)
        
        # Keep only the last 50 responses
        if len(responses) > 50:
            self.context_history[self.current_target]['responses'] = responses[-50:]
    
    def get_target_summary(self, target_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of the target context.
        
        Args:
            target_url: The target URL to summarize, defaults to current target
            
        Returns:
            Dictionary with target summary
        """
        if not target_url and self.current_target:
            target_url = self.current_target
        
        if not target_url or target_url not in self.context_history:
            logger.warning("Target not found in context history: %s", target_url)
            return {'error': 'Target not found in context history'}
        
        context = self.context_history[target_url]
        
        # Generate summary
        summary = {
            'target_url': target_url,
            'first_seen': context['first_seen'],
            'endpoints_count': len(context['endpoints']),
            'auth_endpoints_count': len(context['auth_endpoints']),
            'tokens_count': len(context['tokens']),
            'vulnerabilities_count': len(context['vulnerabilities']),
            'vulnerabilities_summary': self._summarize_vulnerabilities(context['vulnerabilities']),
            'last_response': context['responses'][-1] if context['responses'] else None,
            'response_codes_summary': self._summarize_response_codes(context['responses'])
        }
        
        return summary
    
    def _summarize_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize vulnerabilities by type."""
        summary = {}
        
        for vuln in vulnerabilities:
            vuln_type = f"{vuln['type']}:{vuln.get('subtype', 'unknown')}"
            if vuln_type in summary:
                summary[vuln_type] += 1
            else:
                summary[vuln_type] = 1
        
        return summary
    
    def _summarize_response_codes(self, responses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize response status codes."""
        summary = {}
        
        for response in responses:
            status = str(response.get('status_code', 'unknown'))
            if status in summary:
                summary[status] += 1
            else:
                summary[status] = 1
        
        return summary
    
    def get_similar_endpoints(self, signature: str) -> List[Dict[str, Any]]:
        """
        Find endpoints with similar signatures.
        
        Args:
            signature: The response signature to match
            
        Returns:
            List of similar endpoints
        """
        similar_endpoints = []
        
        for target, signatures in self.target_signatures.items():
            for sig_info in signatures:
                if sig_info['signature'] == signature and sig_info['url'] not in [e['url'] for e in similar_endpoints]:
                    similar_endpoints.append({
                        'url': sig_info['url'],
                        'target': target,
                        'timestamp': sig_info['timestamp']
                    })
        
        return similar_endpoints
    
    def analyze_token_context(self, token: str, token_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the context of a JWT token to provide deeper insights.
        
        Args:
            token: The JWT token to analyze
            token_analysis: Optional pre-existing token analysis
            
        Returns:
            Dictionary with contextual analysis of the token
        """
        logger.info("Analyzing token context for JWT: %s...", token[:20])
        
        # Initialize context analysis
        context = {
            'token_usage': 'unknown',
            'issuer_type': 'unknown',
            'application_type': 'unknown',
            'security_level': 'unknown',
            'purpose': 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        # If no token analysis provided, analyze the token
        if not token_analysis:
            token_analysis = self.analyze_jwt(token)
            
        if not token_analysis or not token_analysis.get('valid', False):
            logger.warning("Invalid token or analysis")
            context['error'] = "Invalid token or analysis"
            return context
            
        # Extract payload and header
        payload = token_analysis.get('payload', {})
        header = token_analysis.get('header', {})
        
        # Determine token usage based on claims
        context['token_usage'] = self._determine_token_usage(payload, header)
        
        # Determine issuer type
        if 'iss' in payload:
            context['issuer_type'] = self._determine_issuer_type(payload['iss'])
            
            # Extract domain from issuer if it's a URL
            if isinstance(payload['iss'], str) and ('http://' in payload['iss'] or 'https://' in payload['iss']):
                import re
                domain_match = re.search(r'https?://([^/]+)', payload['iss'])
                if domain_match:
                    context['issuer_domain'] = domain_match.group(1)
        
        # Determine application type
        context['application_type'] = self._determine_application_type(payload, header)
        
        # Determine security level
        context['security_level'] = self._determine_security_level(token_analysis)
        
        # Determine token purpose
        context['purpose'] = self._determine_token_purpose(payload)
        
        # Identify potential frameworks
        context['potential_framework'] = self._identify_token_framework(payload, header)
        
        # Check for suspicious patterns
        context['suspicious_patterns'] = self._check_suspicious_patterns(payload, header)
        
        # Estimate token age and lifetime
        age_info = self._estimate_token_age(payload)
        if age_info:
            context.update(age_info)
            
        # Generate fingerprint and semantic vector for enhanced context analysis
        fingerprint = self._generate_token_fingerprint(payload, header)
        context['fingerprint'] = fingerprint
        self.token_fingerprints[token] = fingerprint

        semantic_vector = self._generate_semantic_vector(token)
        context['semantic_vector'] = semantic_vector
        self.token_semantic_vectors[token] = semantic_vector

        # Compute similarity with historical token contexts
        similarities = {}
        for prev_token, prev_vector in self.token_semantic_vectors.items():
            if prev_token != token:
                sim_score = self._calculate_context_similarity(semantic_vector, prev_vector)
                similarities[prev_token] = sim_score
        if similarities:
            sorted_sims = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            context['similarity_with_previous_tokens'] = sorted_sims[:5]

        # Calculate risk score based on token analysis and suspicious patterns
        risk_score = self._calculate_risk_score(token_analysis, context.get('suspicious_patterns', []), context.get('similarity_with_previous_tokens', []))
        context['risk_score'] = risk_score

        # Check compliance with organizational policies and best practices
        compliance_flags = self._check_policy_compliance(payload, header, token_analysis)
        context['compliance_flags'] = compliance_flags

        # Adjust risk score based on compliance flags
        for flag in compliance_flags:
            if flag == 'weak_algorithm':
                context['risk_score'] += 0.2
            elif flag == 'none_algorithm':
                context['risk_score'] += 0.5
            elif flag.startswith('no_'):
                context['risk_score'] += 0.1
        # Cap the risk score at 1.0
        context['risk_score'] = min(context['risk_score'], 1.0)

        return context
    
    def _determine_token_usage(self, payload: Dict[str, Any], header: Dict[str, Any]) -> str:
        """Determine how the token is being used based on its claims."""
        # Check for common authentication token patterns
        if 'sub' in payload or 'user_id' in payload or 'uid' in payload:
            return 'authentication'
            
        # Check for authorization token patterns
        if any(k in payload for k in ['scope', 'authorities', 'roles', 'permissions', 'groups']):
            return 'authorization'
            
        # Check for session token patterns
        if 'session_id' in payload or 'sid' in payload:
            return 'session'
            
        # Check for API token patterns
        if 'client_id' in payload or 'api_key' in payload:
            return 'api'
            
        # Check for refresh token patterns
        if 'refresh' in payload or payload.get('token_type') == 'refresh':
            return 'refresh'
            
        # Check for single sign-on token patterns
        if 'azp' in payload or 'aud' in payload and isinstance(payload['aud'], list) and len(payload['aud']) > 1:
            return 'sso'
            
        # Check for access token patterns (default for many JWT implementations)
        if 'exp' in payload and 'iat' in payload:
            return 'access'
            
        # Default if no specific pattern is recognized
        return 'unknown'
    
    def _determine_issuer_type(self, issuer: Any) -> str:
        """Determine the type of issuer based on the 'iss' claim."""
        if not issuer:
            return 'unknown'
            
        if not isinstance(issuer, str):
            return 'non_standard'
            
        issuer_lower = issuer.lower()
        
        # Check for common identity providers
        if any(idp in issuer_lower for idp in ['auth0', 'okta', 'cognito', 'azure', 'microsoft', 'google', 'firebase', 'aws']):
            for idp in ['auth0', 'okta', 'cognito', 'azure', 'microsoft', 'google', 'firebase', 'aws']:
                if idp in issuer_lower:
                    return f'idp_{idp}'
            
        # Check if it's a URL
        if issuer.startswith('http://') or issuer.startswith('https://'):
            # Check for localhost or internal domains
            if 'localhost' in issuer_lower or '127.0.0.1' in issuer or '192.168.' in issuer:
                return 'development'
                
            # Check for subdomains that suggest identity providers
            if any(sub in issuer_lower for sub in ['auth.', 'login.', 'sso.', 'identity.', 'accounts.']):
                return 'identity_service'
                
            # Check for API gateways
            if any(api in issuer_lower for api in ['api.', 'gateway.', 'apis.']):
                return 'api_gateway'
                
            return 'web_service'
        
        # Check for simple string identifiers
        if len(issuer) < 20 and issuer.isalnum():
            return 'application_id'
            
        return 'custom'
    
    def _determine_application_type(self, payload: Dict[str, Any], header: Dict[str, Any]) -> str:
        """Determine the type of application based on token claims and structure."""
        # Check for mobile app specific claims
        if any(k in payload for k in ['device_id', 'platform', 'app_version', 'os_version']):
            return 'mobile_app'
            
        # Check for single page application (SPA) patterns
        if 'nonce' in payload and 'aud' in payload and 'origin' in payload:
            return 'single_page_app'
            
        # Check for microservice patterns
        if 'service' in payload or 'microservice' in payload:
            return 'microservice'
            
        # Check for IoT device patterns
        if any(k in payload for k in ['device_id', 'hw_id', 'serial', 'thing_id']):
            return 'iot_device'
            
        # Check for API specific patterns
        if 'scope' in payload and isinstance(payload.get('scope'), str) and ' ' in payload['scope']:
            return 'oauth_api'
            
        # Check for B2B integration patterns
        if 'organization' in payload or 'org_id' in payload or 'tenant' in payload:
            return 'b2b_integration'
            
        # Check for web app patterns (most common)
        if 'sub' in payload and 'exp' in payload and 'iat' in payload:
            return 'web_app'
            
        # Default if no specific pattern is recognized
        return 'generic_service'
    
    def _determine_security_level(self, token_analysis: Dict[str, Any]) -> str:
        """Determine the security level of the token based on its analysis."""
        # Start with a default security level
        security_level = 'medium'
        
        # Extract header and vulnerabilities
        header = token_analysis.get('header', {})
        vulnerabilities = token_analysis.get('vulnerabilities', [])
        payload = token_analysis.get('payload', {})
        
        # Check for critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.get('type') in [
            'none_algorithm', 'missing_exp', 'weak_algorithm'
        ]]
        
        if critical_vulns:
            return 'low'
            
        # Check algorithm strength
        alg = header.get('alg', '').upper()
        
        # None algorithm is very insecure
        if alg == 'NONE':
            return 'very_low'
            
        # HMAC algorithms with SHA-256 or stronger are generally secure
        if alg in ['HS256', 'HS384', 'HS512']:
            security_level = 'medium'
            
        # RSA and ECDSA are generally more secure than HMAC
        if alg in ['RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512', 'PS256', 'PS384', 'PS512']:
            security_level = 'high'
            
        # Check for expiration and issued at claims
        if 'exp' not in payload:
            security_level = 'low'  # No expiration is a security risk
        elif 'iat' in payload and 'exp' in payload:
            # Calculate token lifetime
            try:
                lifetime = payload['exp'] - payload['iat']
                if lifetime > 86400 * 30:  # More than 30 days
                    security_level = min(security_level, 'medium')  # Long-lived tokens are less secure
                if lifetime > 86400 * 365:  # More than a year
                    security_level = 'low'  # Very long-lived tokens are a security risk
            except (TypeError, ValueError):
                pass
                
        # Check for additional security features
        if 'jti' in payload:  # JWT ID helps prevent replay attacks
            security_level = max(security_level, 'medium')
            
        if 'nbf' in payload:  # Not Before claim adds time-based security
            security_level = max(security_level, 'medium')
            
        # Kid parameter without proper validation can lead to vulnerabilities
        if 'kid' in header and any(v.get('type') == 'kid_parameter_present' for v in vulnerabilities):
            security_level = min(security_level, 'medium')
            
        return security_level
    
    def _determine_token_purpose(self, payload: Dict[str, Any]) -> str:
        """Determine the purpose of the token based on its claims."""
        # Check for common claim patterns that indicate purpose
        
        # Access tokens typically have scopes or permissions
        if 'scope' in payload or 'permissions' in payload or 'authorities' in payload:
            return 'access_token'
            
        # ID tokens typically have user identity information
        if all(claim in payload for claim in ['sub', 'name']) or 'email' in payload:
            return 'id_token'
            
        # Refresh tokens often explicitly state their type
        if payload.get('token_type') == 'refresh' or 'refresh_token' in payload:
            return 'refresh_token'
            
        # Session tokens typically have session information
        if 'session_id' in payload or 'sid' in payload:
            return 'session_token'
            
        # API tokens typically have API-specific claims
        if 'client_id' in payload and 'api' in str(payload):
            return 'api_token'
            
        # Service-to-service tokens often have service identifiers
        if 'service' in payload or 'client_assertion' in payload:
            return 'service_token'
            
        # One-time tokens for specific actions
        if 'action' in payload or 'one_time' in payload or 'otp' in payload:
            return 'action_token'
            
        # Default to access token as most common purpose
        if 'exp' in payload and 'iat' in payload:
            return 'access_token'
            
        return 'unknown'
    
    def _identify_token_framework(self, payload: Dict[str, Any], header: Dict[str, Any]) -> str:
        """Identify the framework used to generate the token."""
        # Convert payload and header to strings for easier pattern matching
        payload_str = str(payload).lower()
        header_str = str(header).lower()
        
        # Check for Auth0 specific patterns
        if 'auth0' in payload_str or ('iss' in payload and 'auth0.com' in str(payload['iss'])):
            return 'auth0'
            
        # Check for AWS Cognito patterns
        if 'cognito' in payload_str or 'aws' in payload_str or ('iss' in payload and 'cognito-idp' in str(payload['iss'])):
            return 'aws_cognito'
            
        # Check for Firebase/Google patterns
        if ('firebase' in payload_str or 
            ('iss' in payload and ('securetoken.google.com' in str(payload['iss']) or 'accounts.google.com' in str(payload['iss'])))):
            return 'firebase_google'
            
        # Check for Microsoft/Azure patterns
        if ('microsoft' in payload_str or 'azure' in payload_str or 
            ('iss' in payload and ('login.microsoftonline.com' in str(payload['iss']) or 'sts.windows.net' in str(payload['iss'])))):
            return 'microsoft_azure'
            
        # Check for Okta patterns
        if 'okta' in payload_str or ('iss' in payload and 'okta.com' in str(payload['iss'])):
            return 'okta'
            
        # Check for Keycloak patterns
        if 'keycloak' in payload_str or 'realm_access' in payload or 'resource_access' in payload:
            return 'keycloak'
            
        # Check for Spring Security patterns
        if 'authorities' in payload or 'scope' in payload and isinstance(payload.get('scope'), list):
            return 'spring_security'
            
        # Check for Auth0 patterns
        if 'gty' in payload and payload['gty'] == 'client-credentials':
            return 'auth0'
            
        # Check for JWT.io patterns
        if header.get('alg') == 'HS256' and len(payload) <= 3 and 'sub' in payload and 'name' in payload:
            return 'jwt_io_example'
            
        # Check for Node.js jsonwebtoken library default patterns
        if header.get('alg') == 'HS256' and header.get('typ') == 'JWT' and 'iat' in payload and len(header) == 2:
            return 'node_jsonwebtoken'
            
        # Check for .NET JWT patterns
        if 'nbf' in payload and 'exp' in payload and 'iss' in payload and 'aud' in payload:
            return 'dotnet_jwt'
            
        # Default if no specific framework is recognized
        return 'generic_jwt'
    
    def _check_suspicious_patterns(self, payload: Dict[str, Any], header: Dict[str, Any]) -> List[str]:
        """Check for suspicious patterns in the token."""
        suspicious_patterns = []
        
        # Check for 'none' algorithm
        if header.get('alg', '').lower() == 'none':
            suspicious_patterns.append('none_algorithm')
            
        # Check for missing expiration
        if 'exp' not in payload:
            suspicious_patterns.append('no_expiration')
            
        # Check for very long expiration
        if 'exp' in payload and 'iat' in payload:
            try:
                lifetime = int(payload['exp']) - int(payload['iat'])
                if lifetime > 86400 * 365:  # More than a year
                    suspicious_patterns.append('excessive_lifetime')
            except (TypeError, ValueError):
                pass
                
        # Check for suspicious admin claims
        admin_indicators = ['admin', 'root', 'superuser', 'administrator']
        for key, value in payload.items():
            if 'role' in key.lower() or 'admin' in key.lower() or 'permission' in key.lower():
                if any(admin in str(value).lower() for admin in admin_indicators):
                    suspicious_patterns.append('admin_role_claim')
                    break
                    
        # Check for suspicious header parameters
        if 'kid' in header:
            # Check for potential command injection in 'kid' parameter
            kid_value = str(header['kid'])
            if any(char in kid_value for char in ['..', ';', '|', '&', '$', '`', "'"]):
                suspicious_patterns.append('kid_injection_attempt')
                
        # Check for jwk header parameter (potential jwk injection)
        if 'jwk' in header:
            suspicious_patterns.append('jwk_header_present')
            
        # Check for jku header parameter (potential jku injection)
        if 'jku' in header:
            suspicious_patterns.append('jku_header_present')
            
        # Check for x5u header parameter (potential x5u injection)
        if 'x5u' in header:
            suspicious_patterns.append('x5u_header_present')
            
        # Check for potential SQL injection patterns in any claim
        sql_patterns = ["'", "OR 1=1", "--;", "/*", "UNION", "SELECT", "DROP", "DELETE", "UPDATE"]
        for key, value in payload.items():
            if isinstance(value, str) and any(pattern in value for pattern in sql_patterns):
                suspicious_patterns.append('sql_injection_pattern')
                break
                
        # Check for sensitive data in payload
        sensitive_keys = ['password', 'secret', 'key', 'token', 'credential', 'api_key', 'private']
        for key in payload.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                suspicious_patterns.append('sensitive_data_in_payload')
                break
                
        return suspicious_patterns
    
    def _estimate_token_age(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the age and lifetime of the token."""
        result = {}
        
        # Check if we have the necessary claims
        if 'iat' not in payload:
            return result
            
        try:
            # Get current time
            current_time = int(datetime.now().timestamp())
            
            # Calculate token age
            issued_at = int(payload['iat'])
            token_age_seconds = current_time - issued_at
            
            result['token_age_seconds'] = token_age_seconds
            result['token_age_minutes'] = token_age_seconds / 60
            result['token_age_hours'] = token_age_seconds / 3600
            result['token_age_days'] = token_age_seconds / 86400
            
            # Determine if token is expired
            if 'exp' in payload:
                expiration = int(payload['exp'])
                result['expires_in_seconds'] = expiration - current_time
                result['is_expired'] = result['expires_in_seconds'] < 0
                
                # Calculate total lifetime
                result['total_lifetime_seconds'] = expiration - issued_at
                result['total_lifetime_minutes'] = result['total_lifetime_seconds'] / 60
                result['total_lifetime_hours'] = result['total_lifetime_seconds'] / 3600
                result['total_lifetime_days'] = result['total_lifetime_seconds'] / 86400
                
                # Calculate percentage of lifetime used
                if result['total_lifetime_seconds'] > 0:
                    result['lifetime_percentage_used'] = min(100, (token_age_seconds / result['total_lifetime_seconds']) * 100)
                
            # Check for not-before claim
            if 'nbf' in payload:
                not_before = int(payload['nbf'])
                result['active_in_seconds'] = current_time - not_before
                result['is_active'] = result['active_in_seconds'] >= 0
                
        except (TypeError, ValueError) as e:
            logger.warning(f"Error estimating token age: {str(e)}")
            
        return result
    
    def analyze_target_context(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the context of a target to provide insights for attack strategies.
        
        Args:
            target_data: Dictionary containing information about the target
            
        Returns:
            Dictionary with contextual analysis of the target
        """
        logger.info("Analyzing target context")
        
        # Initialize context analysis
        context = {
            'target_type': 'unknown',
            'authentication_type': 'unknown',
            'technologies': [],
            'potential_vulnerabilities': [],
            'security_posture': 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract target URL if available
        if 'url' in target_data:
            self.set_target(target_data['url'])
            context['target_url'] = target_data['url']
            
        # Determine target type
        if 'technologies' in target_data:
            techs = target_data['technologies']
            context['technologies'] = techs
            
            # Web application frameworks
            web_frameworks = ['django', 'flask', 'express', 'spring', 'rails', 'laravel', 'asp.net']
            if any(fw in str(techs).lower() for fw in web_frameworks):
                context['target_type'] = 'web_application'
                
            # API frameworks
            api_frameworks = ['rest', 'graphql', 'grpc', 'soap', 'api']
            if any(fw in str(techs).lower() for fw in api_frameworks):
                context['target_type'] = 'api_service'
                
            # Mobile backends
            mobile_indicators = ['mobile', 'android', 'ios', 'react-native', 'flutter']
            if any(ind in str(techs).lower() for ind in mobile_indicators):
                context['target_type'] = 'mobile_backend'
                
        # Determine authentication type
        if 'headers' in target_data:
            headers = target_data['headers']
            auth_header = headers.get('Authorization', '')
            
            if auth_header.startswith('Bearer '):
                context['authentication_type'] = 'jwt_bearer'
            elif auth_header.startswith('Basic '):
                context['authentication_type'] = 'basic_auth'
            elif auth_header.startswith('Digest '):
                context['authentication_type'] = 'digest_auth'
            elif auth_header.startswith('OAuth '):
                context['authentication_type'] = 'oauth'
                
        # Check for JWT usage
        if 'response_contains_json' in target_data and target_data['response_contains_json']:
            context['data_format'] = 'json'
            
        if 'uses_jwt' in target_data and target_data['uses_jwt']:
            context['uses_jwt'] = True
            
        # Identify potential vulnerabilities
        vulnerabilities = []
        
        if target_data.get('allows_header_injection', False):
            vulnerabilities.append({
                'type': 'header_injection',
                'severity': 'high',
                'description': 'Target allows header injection'
            })
            
        if target_data.get('shows_detailed_errors', False):
            vulnerabilities.append({
                'type': 'information_disclosure',
                'severity': 'medium',
                'description': 'Target shows detailed error messages'
            })
            
        if 'response_codes' in target_data:
            if 500 in target_data['response_codes']:
                vulnerabilities.append({
                    'type': 'server_error',
                    'severity': 'medium',
                    'description': 'Target returns 500 internal server errors'
                })
                
        context['potential_vulnerabilities'] = vulnerabilities
        
        # Determine security posture
        if vulnerabilities:
            high_severity = any(v['severity'] == 'high' for v in vulnerabilities)
            if high_severity:
                context['security_posture'] = 'weak'
            else:
                context['security_posture'] = 'moderate'
        else:
            context['security_posture'] = 'strong'
            
        return context
    
    def identify_potential_vulnerabilities(self, target_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify potential vulnerabilities in a target based on context analysis.
        
        Args:
            target_data: Dictionary containing information about the target
            
        Returns:
            List of potential vulnerabilities with details
        """
        vulnerabilities = []
        
        # Check for JWT-related vulnerabilities
        if target_data.get('uses_jwt', False):
            # Check for 'none' algorithm vulnerability
            if 'jwt_token' in target_data:
                token = target_data['jwt_token']
                token_analysis = self.analyze_jwt(token)
                
                if token_analysis.get('valid', False):
                    # Check algorithm
                    if token_analysis.get('algorithm', '').lower() == 'none':
                        vulnerabilities.append({
                            'type': 'jwt_none_algorithm',
                            'severity': 'critical',
                            'description': 'JWT uses "none" algorithm which can bypass signature verification',
                            'exploitation_likelihood': 'high',
                            'mitigation': 'Reject tokens with "none" algorithm'
                        })
                    
                    # Check for missing expiration
                    if 'exp' not in token_analysis.get('payload', {}):
                        vulnerabilities.append({
                            'type': 'jwt_no_expiration',
                            'severity': 'high',
                            'description': 'JWT has no expiration claim, making it valid indefinitely',
                            'exploitation_likelihood': 'medium',
                            'mitigation': 'Add expiration claims to all tokens'
                        })
                    
                    # Check for weak algorithm
                    if token_analysis.get('algorithm', '') == 'HS256':
                        vulnerabilities.append({
                            'type': 'jwt_weak_algorithm',
                            'severity': 'medium',
                            'description': 'JWT uses HS256 which may be vulnerable to brute force if secret is weak',
                            'exploitation_likelihood': 'medium',
                            'mitigation': 'Use stronger algorithms like RS256 or ES256'
                        })
                    
                    # Check for kid parameter
                    if 'kid' in token_analysis.get('header', {}):
                        vulnerabilities.append({
                            'type': 'jwt_kid_parameter',
                            'severity': 'medium',
                            'description': 'JWT uses "kid" parameter which may be vulnerable to injection attacks',
                            'exploitation_likelihood': 'medium',
                            'mitigation': 'Validate "kid" parameter properly'
                        })
            else:
                # Generic JWT vulnerabilities if we don't have a token to analyze
                vulnerabilities.append({
                    'type': 'jwt_usage',
                    'severity': 'info',
                    'description': 'Target uses JWT for authentication/authorization',
                    'exploitation_likelihood': 'unknown',
                    'mitigation': 'Ensure proper JWT implementation and validation'
                })
        
        # Check for error disclosure vulnerabilities
        if target_data.get('shows_detailed_errors', False):
            vulnerabilities.append({
                'type': 'information_disclosure',
                'severity': 'medium',
                'description': 'Target shows detailed error messages that may reveal implementation details',
                'exploitation_likelihood': 'medium',
                'mitigation': 'Use generic error messages in production'
            })
        
        # Check for header injection vulnerabilities
        if target_data.get('allows_header_injection', False):
            vulnerabilities.append({
                'type': 'header_injection',
                'severity': 'high',
                'description': 'Target allows header injection which may lead to various attacks',
                'exploitation_likelihood': 'high',
                'mitigation': 'Validate and sanitize all headers'
            })
        
        # Check for server information disclosure
        if target_data.get('leaks_server_info', False):
            vulnerabilities.append({
                'type': 'server_info_disclosure',
                'severity': 'low',
                'description': 'Target leaks server information which may help attackers',
                'exploitation_likelihood': 'low',
                'mitigation': 'Remove server headers or use generic values'
            })
        
        # Check for SQL injection vulnerabilities
        if 'response_patterns' in target_data and 'sql_error' in target_data['response_patterns']:
            vulnerabilities.append({
                'type': 'sql_injection',
                'severity': 'critical',
                'description': 'Target may be vulnerable to SQL injection attacks',
                'exploitation_likelihood': 'high',
                'mitigation': 'Use parameterized queries and input validation'
            })
        
        return vulnerabilities

    # Advanced language learning methods
    def _generate_token_fingerprint(self, payload: Dict[str, Any], header: Dict[str, Any]) -> str:
        """Generate a consistent fingerprint for the token based on its payload and header."""
        data_str = json.dumps({'payload': payload, 'header': header}, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _generate_semantic_vector(self, token: str) -> List[float]:
        """Generate a lightweight semantic vector representation of the token."""
        segments = token.split('.')
        vector = []
        for seg in segments:
            seg_hash = int(hashlib.sha256(seg.encode()).hexdigest(), 16)
            vector.append((seg_hash % 1000) / 1000.0)
        return vector

    def _calculate_context_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two semantic vectors."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        if not mag1 or not mag2:
            return 0.0
        return dot / (mag1 * mag2)

    def _calculate_risk_score(self, token_analysis: Dict[str, Any], suspicious_patterns: List[str], similarity_with_previous_tokens: List[Tuple[str, float]]) -> float:
        """Calculate a risk score based on token analysis and suspicious patterns."""
        # Start with a base score
        risk_score = 0.5
        
        # Add points for each suspicious pattern
        for pattern in suspicious_patterns:
            risk_score += 0.1
        
        # Add points for similarity with previous tokens
        for token, similarity in similarity_with_previous_tokens:
            risk_score += similarity * 0.05
        
        return risk_score

    def _check_policy_compliance(self, payload: Dict[str, Any], header: Dict[str, Any], token_analysis: Dict[str, Any]) -> List[str]:
        """Check compliance with organizational policies and best practices."""
        compliance_flags = []
        
        # Check for sensitive data in payload
        sensitive_keys = ['password', 'secret', 'key', 'token', 'credential', 'api_key', 'private']
        for key in payload.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                compliance_flags.append('sensitive_data_in_payload')
                break
        
        # Check for expiration
        if 'exp' not in payload:
            compliance_flags.append('no_expiration')
        
        # Check for weak algorithm
        if token_analysis.get('algorithm', '') == 'HS256':
            compliance_flags.append('weak_algorithm')

        # Check for missing issued at claim
        if 'iat' not in payload:
            compliance_flags.append('no_issued_at')

        # Check for missing not before claim
        if 'nbf' not in payload:
            compliance_flags.append('no_not_before')

        # Check for none algorithm
        if token_analysis.get('algorithm', '').lower() == 'none':
            compliance_flags.append('none_algorithm')

        return compliance_flags


if __name__ == "__main__":
    # Example usage
    analyzer = ContextAnalyzer()
    
    # Set target
    analyzer.set_target('https://example.com')
    
    # Example response with JWT
    response = {
        'url': 'https://example.com/api/login',
        'status_code': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Server': 'nginx/1.18.0'
        },
        'body': '{"status":"success","message":"Authentication successful","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}',
        'response_time': 0.234
    }
    
    # Analyze response
    analysis = analyzer.analyze_response(response)
    print("Response Analysis:", json.dumps(analysis, indent=2))
    
    # Extract JWT token from response
    import re
    jwt_pattern = r'\"token\":\"([^\"]+)\"'
    match = re.search(jwt_pattern, response['body'])
    if match:
        token = match.group(1)
        
        # Analyze token
        token_analysis = analyzer.analyze_jwt(token)
        print("\nToken Analysis:", json.dumps(token_analysis, indent=2))
        
        # Analyze token context
        token_context = analyzer.analyze_token_context(token, token_analysis)
        print("\nToken Context Analysis:", json.dumps(token_context, indent=2))
        
        # Check for suspicious patterns
        if token_context['suspicious_patterns']:
            print("\nSuspicious patterns detected:", token_context['suspicious_patterns'])
    
    # Update context history
    analyzer.update_context_history(response['url'], analysis)
    
    # Get target summary
    summary = analyzer.get_target_summary()
    print("\nTarget Summary:", json.dumps(summary, indent=2))
    
    # Example target data for vulnerability analysis
    target_data = {
        'url': 'https://example.com',
        'uses_jwt': True,
        'jwt_token': token if 'token' in locals() else None,
        'shows_detailed_errors': True,
        'allows_header_injection': False,
        'technologies': ['nginx', 'node.js', 'express', 'mongodb'],
        'response_patterns': {
            'sql_error': ['syntax error']
        }
    }
    
    # Identify potential vulnerabilities
    vulnerabilities = analyzer.identify_potential_vulnerabilities(target_data)
    print("\nPotential Vulnerabilities:", json.dumps(vulnerabilities, indent=2))
    
    # Analyze target context
    target_context = analyzer.analyze_target_context(target_data)
    print("\nTarget Context Analysis:", json.dumps(target_context, indent=2)) 