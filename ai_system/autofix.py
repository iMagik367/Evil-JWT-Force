"""
EVIL_JWT_FORCE - Auto Fix Module
This module attempts to automatically fix errors, broken routes, and failed attacks.

It uses a combination of predefined heuristics and learning from past failures to
suggest corrections and alternative approaches when attacks fail.
"""

import os
import json
import logging
import re
import traceback
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'autofix.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AUTOFIX')

class AutoFix:
    """
    Automatic error detection and correction system for EVIL_JWT_FORCE.
    
    This class handles error recovery, retry strategies, and automatic fixes
    for common issues that may occur during JWT attacks.
    """
    
    def __init__(self, config_path: str = 'config/autofix_config.json'):
        """
        Initialize the AutoFix module with configuration settings.
        
        Args:
            config_path: Path to the AutoFix configuration file
        """
        self.config = self._load_config(config_path)
        self.error_patterns = self.config.get('error_patterns', {})
        self.fix_templates = self.config.get('fix_templates', {})
        self.error_history = self._load_error_history()
        self.max_fix_attempts = self.config.get('max_fix_attempts', 3)
        
        logger.info("AutoFix module initialized with %d error patterns and %d fix templates", 
                   len(self.error_patterns), len(self.fix_templates))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'error_patterns': {
                'connection_timeout': r"Connection timed out|Read timed out|ConnectTimeout",
                'connection_refused': r"Connection refused|Failed to establish a connection",
                'http_404': r"404 Not Found|resource not found",
                'http_403': r"403 Forbidden|Access denied|Forbidden",
                'http_401': r"401 Unauthorized|Authentication failed|Unauthorized",
                'invalid_jwt': r"Invalid token|JWT verification failed|signature verification failed",
                'expired_jwt': r"Token expired|JWT has expired|exp claim expired",
                'rate_limited': r"Rate limit exceeded|Too many requests|429 Too Many Requests",
                'invalid_params': r"Invalid parameters|Missing required parameter|Bad request",
                'server_error': r"Internal server error|500 Internal Server Error|server failed"
            },
            'fix_templates': {
                'connection_timeout': [
                    {'action': 'increase_timeout', 'params': {'timeout': 30}},
                    {'action': 'retry_with_backoff', 'params': {'max_retries': 5, 'backoff_factor': 2}}
                ],
                'connection_refused': [
                    {'action': 'check_target_availability', 'params': {}},
                    {'action': 'try_alternative_port', 'params': {'ports': [80, 443, 8080, 8443]}}
                ],
                'http_404': [
                    {'action': 'check_endpoint_path', 'params': {}},
                    {'action': 'try_common_jwt_endpoints', 'params': {}}
                ],
                'http_403': [
                    {'action': 'add_common_headers', 'params': {}},
                    {'action': 'try_different_user_agent', 'params': {}}
                ],
                'http_401': [
                    {'action': 'refresh_token', 'params': {}},
                    {'action': 'try_default_credentials', 'params': {}}
                ],
                'invalid_jwt': [
                    {'action': 'verify_token_format', 'params': {}},
                    {'action': 'try_alternative_signature', 'params': {'algs': ['HS256', 'none']}}
                ],
                'expired_jwt': [
                    {'action': 'update_token_timestamp', 'params': {'extend_by': 3600}},
                    {'action': 'remove_exp_claim', 'params': {}}
                ],
                'rate_limited': [
                    {'action': 'add_delay_between_requests', 'params': {'delay': 5}},
                    {'action': 'rotate_ip_address', 'params': {}}
                ],
                'invalid_params': [
                    {'action': 'check_required_parameters', 'params': {}},
                    {'action': 'use_default_parameters', 'params': {}}
                ],
                'server_error': [
                    {'action': 'simplify_request', 'params': {}},
                    {'action': 'try_safe_parameters', 'params': {}}
                ]
            },
            'max_fix_attempts': 3,
            'learning_rate': 0.1,
            'success_threshold': 0.6
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
    
    def _load_error_history(self) -> Dict[str, Any]:
        """Load error history from file or initialize new if not available."""
        history_file = os.path.join('data', 'error_history.json')
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
            else:
                logger.info("No previous error history found. Initializing new error history.")
                error_history = {
                    'errors': {},
                    'fixes': {},
                    'success_rates': {},
                    'last_updated': datetime.now().isoformat()
                }
                os.makedirs(os.path.dirname(history_file), exist_ok=True)
                with open(history_file, 'w') as f:
                    json.dump(error_history, f, indent=2)
                return error_history
        except Exception as e:
            logger.error("Error loading error history: %s", str(e))
            return {
                'errors': {},
                'fixes': {},
                'success_rates': {}
            }
    
    def detect_error_type(self, error_message: str) -> Optional[str]:
        """
        Detect the type of error based on the error message.
        
        Args:
            error_message: The error message to analyze
            
        Returns:
            The error type if detected, None otherwise
        """
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                logger.info("Detected error type '%s' from message: %s", error_type, error_message[:100])
                return error_type
        
        logger.warning("Could not detect error type from message: %s", error_message[:100])
        return None
    
    def suggest_fixes(self, error_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest fixes for a given error type.
        
        Args:
            error_type: The type of error to fix
            context: The context in which the error occurred
            
        Returns:
            List of suggested fixes
        """
        if error_type not in self.fix_templates:
            logger.warning("No fix templates available for error type '%s'", error_type)
            return []
        
        # Get available fixes for this error type
        available_fixes = self.fix_templates[error_type]
        
        # Check error history to prioritize previously successful fixes
        prioritized_fixes = self._prioritize_fixes(error_type, available_fixes)
        
        logger.info("Suggesting %d fixes for error type '%s'", len(prioritized_fixes), error_type)
        return prioritized_fixes
    
    def _prioritize_fixes(self, error_type: str, available_fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize fixes based on past success rates."""
        if error_type not in self.error_history.get('success_rates', {}):
            # No history for this error type, return original order
            return available_fixes
        
        # Get success rates for this error type
        success_rates = self.error_history['success_rates'][error_type]
        
        # Create a copy of fixes to reorder
        prioritized = available_fixes.copy()
        
        # Sort by success rate (descending)
        prioritized.sort(key=lambda fix: success_rates.get(fix['action'], 0), reverse=True)
        
        return prioritized
    
    def apply_fix(self, fix: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a fix to the given context.
        
        Args:
            fix: The fix to apply
            context: The context to apply the fix to
            
        Returns:
            Updated context with the fix applied
        """
        action = fix.get('action')
        params = fix.get('params', {})
        
        logger.info("Applying fix '%s' with parameters: %s", action, params)
        
        # Create a copy of the context to modify
        updated_context = context.copy()
        
        try:
            # Apply the fix based on the action type
            if action == 'increase_timeout':
                updated_context['timeout'] = params.get('timeout', 30)
            
            elif action == 'retry_with_backoff':
                updated_context['max_retries'] = params.get('max_retries', 5)
                updated_context['backoff_factor'] = params.get('backoff_factor', 2)
                updated_context['retry_enabled'] = True
            
            elif action == 'check_target_availability':
                # This would typically call an external function to check availability
                updated_context['check_availability'] = True
            
            elif action == 'try_alternative_port':
                if 'current_port_index' not in updated_context:
                    updated_context['current_port_index'] = 0
                
                ports = params.get('ports', [80, 443, 8080, 8443])
                if updated_context['current_port_index'] < len(ports):
                    port = ports[updated_context['current_port_index']]
                    updated_context['port'] = port
                    updated_context['current_port_index'] += 1
            
            elif action == 'check_endpoint_path':
                updated_context['verify_endpoint'] = True
            
            elif action == 'try_common_jwt_endpoints':
                common_endpoints = [
                    '/api/auth', '/api/token', '/api/login', '/auth', '/token', 
                    '/login', '/api/v1/auth', '/api/v1/token', '/api/v2/auth'
                ]
                
                if 'current_endpoint_index' not in updated_context:
                    updated_context['current_endpoint_index'] = 0
                
                if updated_context['current_endpoint_index'] < len(common_endpoints):
                    endpoint = common_endpoints[updated_context['current_endpoint_index']]
                    updated_context['endpoint'] = endpoint
                    updated_context['current_endpoint_index'] += 1
            
            elif action == 'add_common_headers':
                if 'headers' not in updated_context:
                    updated_context['headers'] = {}
                
                # Add common headers that might help with authentication
                updated_context['headers'].update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive'
                })
            
            elif action == 'try_different_user_agent':
                if 'headers' not in updated_context:
                    updated_context['headers'] = {}
                
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1',
                    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
                ]
                
                if 'current_ua_index' not in updated_context:
                    updated_context['current_ua_index'] = 0
                
                if updated_context['current_ua_index'] < len(user_agents):
                    ua = user_agents[updated_context['current_ua_index']]
                    updated_context['headers']['User-Agent'] = ua
                    updated_context['current_ua_index'] += 1
            
            elif action == 'refresh_token':
                updated_context['refresh_token'] = True
            
            elif action == 'try_default_credentials':
                default_creds = [
                    {'username': 'admin', 'password': 'admin'},
                    {'username': 'admin', 'password': 'password'},
                    {'username': 'user', 'password': 'password'},
                    {'username': 'test', 'password': 'test'},
                    {'username': 'guest', 'password': 'guest'}
                ]
                
                if 'current_creds_index' not in updated_context:
                    updated_context['current_creds_index'] = 0
                
                if updated_context['current_creds_index'] < len(default_creds):
                    creds = default_creds[updated_context['current_creds_index']]
                    updated_context['credentials'] = creds
                    updated_context['current_creds_index'] += 1
            
            elif action == 'verify_token_format':
                updated_context['verify_token'] = True
            
            elif action == 'try_alternative_signature':
                algs = params.get('algs', ['HS256', 'none', 'RS256'])
                
                if 'current_alg_index' not in updated_context:
                    updated_context['current_alg_index'] = 0
                
                if updated_context['current_alg_index'] < len(algs):
                    alg = algs[updated_context['current_alg_index']]
                    updated_context['jwt_alg'] = alg
                    updated_context['current_alg_index'] += 1
            
            elif action == 'update_token_timestamp':
                extend_by = params.get('extend_by', 3600)  # Default to 1 hour
                updated_context['extend_token_by'] = extend_by
            
            elif action == 'remove_exp_claim':
                updated_context['remove_exp'] = True
            
            elif action == 'add_delay_between_requests':
                delay = params.get('delay', 5)
                updated_context['request_delay'] = delay
            
            elif action == 'rotate_ip_address':
                updated_context['rotate_ip'] = True
            
            elif action == 'check_required_parameters':
                updated_context['verify_params'] = True
            
            elif action == 'use_default_parameters':
                updated_context['use_defaults'] = True
            
            elif action == 'simplify_request':
                updated_context['simplify'] = True
            
            elif action == 'try_safe_parameters':
                updated_context['safe_mode'] = True
            
            else:
                logger.warning("Unknown fix action: %s", action)
            
            # Record the applied fix in the context
            if 'applied_fixes' not in updated_context:
                updated_context['applied_fixes'] = []
            
            updated_context['applied_fixes'].append({
                'action': action,
                'params': params,
                'timestamp': datetime.now().isoformat()
            })
            
            # Record the fix attempt
            self._record_fix_attempt(action, error_type=context.get('error_type'))
            
        except Exception as e:
            logger.error("Error applying fix '%s': %s", action, str(e))
            logger.error(traceback.format_exc())
        
        return updated_context
    
    def _record_fix_attempt(self, action: str, error_type: Optional[str] = None) -> None:
        """Record a fix attempt in the error history."""
        if 'fixes' not in self.error_history:
            self.error_history['fixes'] = {}
        
        if action not in self.error_history['fixes']:
            self.error_history['fixes'][action] = {
                'attempts': 0,
                'successes': 0,
                'last_attempt': None
            }
        
        self.error_history['fixes'][action]['attempts'] += 1
        self.error_history['fixes'][action]['last_attempt'] = datetime.now().isoformat()
        
        # Also record by error type if provided
        if error_type:
            if 'errors' not in self.error_history:
                self.error_history['errors'] = {}
            
            if error_type not in self.error_history['errors']:
                self.error_history['errors'][error_type] = {
                    'occurrences': 0,
                    'fixes': {}
                }
            
            self.error_history['errors'][error_type]['occurrences'] += 1
            
            if 'fixes' not in self.error_history['errors'][error_type]:
                self.error_history['errors'][error_type]['fixes'] = {}
            
            if action not in self.error_history['errors'][error_type]['fixes']:
                self.error_history['errors'][error_type]['fixes'][action] = {
                    'attempts': 0,
                    'successes': 0
                }
            
            self.error_history['errors'][error_type]['fixes'][action]['attempts'] += 1
        
        # Save the updated error history
        self._save_error_history()
    
    def update_fix_result(self, action: str, success: bool, error_type: Optional[str] = None) -> None:
        """
        Update the result of a fix attempt to improve future suggestions.
        
        Args:
            action: The fix action that was applied
            success: Whether the fix was successful
            error_type: The type of error that was being fixed
        """
        logger.info("Updating fix result: action=%s, success=%s, error_type=%s", 
                   action, success, error_type)
        
        if 'fixes' not in self.error_history or action not in self.error_history['fixes']:
            logger.warning("No history record found for fix action '%s'", action)
            return
        
        # Update general fix success
        if success:
            self.error_history['fixes'][action]['successes'] += 1
        
        # Update error-specific fix success if error type provided
        if error_type:
            if ('errors' in self.error_history and 
                error_type in self.error_history['errors'] and 
                'fixes' in self.error_history['errors'][error_type] and
                action in self.error_history['errors'][error_type]['fixes']):
                
                if success:
                    self.error_history['errors'][error_type]['fixes'][action]['successes'] += 1
                
                # Calculate and update success rate
                attempts = self.error_history['errors'][error_type]['fixes'][action]['attempts']
                successes = self.error_history['errors'][error_type]['fixes'][action]['successes']
                
                if 'success_rates' not in self.error_history:
                    self.error_history['success_rates'] = {}
                
                if error_type not in self.error_history['success_rates']:
                    self.error_history['success_rates'][error_type] = {}
                
                if attempts > 0:
                    success_rate = successes / attempts
                    self.error_history['success_rates'][error_type][action] = success_rate
        
        # Save the updated error history
        self._save_error_history()
    
    def _save_error_history(self) -> None:
        """Save the error history to a file."""
        history_file = os.path.join('data', 'error_history.json')
        self.error_history['last_updated'] = datetime.now().isoformat()
        
        try:
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(self.error_history, f, indent=2)
        except Exception as e:
            logger.error("Error saving error history: %s", str(e))
    
    def handle_error(self, error_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an error by detecting its type and suggesting fixes.
        
        Args:
            error_message: The error message to handle
            context: The context in which the error occurred
            
        Returns:
            Dictionary with error handling information
        """
        # Generate a hash of the error message for tracking
        error_hash = hashlib.md5(error_message.encode()).hexdigest()
        
        # Detect the error type
        error_type = self.detect_error_type(error_message)
        
        # Create error handling information
        error_info = {
            'error_hash': error_hash,
            'error_message': error_message,
            'error_type': error_type,
            'timestamp': datetime.now().isoformat(),
            'has_suggestions': False,
            'suggestions': [],
            'updated_context': context.copy()
        }
        
        # If we could detect the error type, suggest fixes
        if error_type:
            suggested_fixes = self.suggest_fixes(error_type, context)
            
            if suggested_fixes:
                error_info['has_suggestions'] = True
                error_info['suggestions'] = suggested_fixes
                
                # Apply the first suggested fix
                if suggested_fixes:
                    error_info['updated_context'] = self.apply_fix(suggested_fixes[0], context)
                    error_info['applied_fix'] = suggested_fixes[0]['action']
            
            # Record the error occurrence
            self._record_error_occurrence(error_type, error_hash, error_message)
        
        return error_info
    
    def _record_error_occurrence(self, error_type: str, error_hash: str, error_message: str) -> None:
        """Record an error occurrence in the error history."""
        if 'errors' not in self.error_history:
            self.error_history['errors'] = {}
        
        if error_type not in self.error_history['errors']:
            self.error_history['errors'][error_type] = {
                'occurrences': 0,
                'examples': [],
                'fixes': {}
            }
        
        self.error_history['errors'][error_type]['occurrences'] += 1
        
        # Store a limited number of examples
        examples = self.error_history['errors'][error_type].get('examples', [])
        
        # Only add if we don't already have this exact error
        if not any(e.get('hash') == error_hash for e in examples):
            # Keep only the last 10 examples
            if len(examples) >= 10:
                examples.pop(0)
            
            examples.append({
                'hash': error_hash,
                'message': error_message[:200],  # Store only the first 200 chars
                'timestamp': datetime.now().isoformat()
            })
            
            self.error_history['errors'][error_type]['examples'] = examples
        
        # Save the updated error history
        self._save_error_history()
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about fixes and their success rates.
        
        Returns:
            Dictionary with fix statistics
        """
        stats = {
            'total_errors': 0,
            'total_fixes_attempted': 0,
            'total_fixes_succeeded': 0,
            'error_types': {},
            'fix_success_rates': {},
            'most_common_errors': [],
            'most_successful_fixes': []
        }
        
        # Calculate error statistics
        if 'errors' in self.error_history:
            for error_type, error_data in self.error_history['errors'].items():
                occurrences = error_data.get('occurrences', 0)
                stats['total_errors'] += occurrences
                
                stats['error_types'][error_type] = {
                    'occurrences': occurrences,
                    'fixes_attempted': 0,
                    'fixes_succeeded': 0
                }
                
                # Calculate fix statistics for this error type
                for fix_action, fix_data in error_data.get('fixes', {}).items():
                    attempts = fix_data.get('attempts', 0)
                    successes = fix_data.get('successes', 0)
                    
                    stats['error_types'][error_type]['fixes_attempted'] += attempts
                    stats['error_types'][error_type]['fixes_succeeded'] += successes
                    stats['total_fixes_attempted'] += attempts
                    stats['total_fixes_succeeded'] += successes
        
        # Calculate success rates
        if 'success_rates' in self.error_history:
            stats['fix_success_rates'] = self.error_history['success_rates']
        
        # Get most common errors
        if 'errors' in self.error_history:
            error_counts = [(et, ed.get('occurrences', 0)) 
                            for et, ed in self.error_history['errors'].items()]
            error_counts.sort(key=lambda x: x[1], reverse=True)
            stats['most_common_errors'] = [{'type': et, 'count': c} for et, c in error_counts[:5]]
        
        # Get most successful fixes
        success_rates = []
        if 'success_rates' in self.error_history:
            for error_type, rates in self.error_history['success_rates'].items():
                for action, rate in rates.items():
                    success_rates.append((error_type, action, rate))
        
        success_rates.sort(key=lambda x: x[2], reverse=True)
        stats['most_successful_fixes'] = [
            {'error_type': et, 'action': a, 'success_rate': r} 
            for et, a, r in success_rates[:5]
        ]
        
        return stats


if __name__ == "__main__":
    # Example usage
    autofix = AutoFix()
    
    # Example error message
    error_message = "JWT verification failed: signature verification failed"
    
    # Example context
    context = {
        'target_url': 'https://example.com/api/auth',
        'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        'method': 'POST',
        'timeout': 10
    }
    
    # Handle the error
    result = autofix.handle_error(error_message, context)
    print("Error handling result:", json.dumps(result, indent=2))
    
    # Mark the fix as successful
    if result['has_suggestions'] and 'applied_fix' in result:
        autofix.update_fix_result(
            result['applied_fix'],
            success=True,
            error_type=result['error_type']
        )
    
    # Get fix statistics
    stats = autofix.get_fix_statistics()
    print("Fix statistics:", json.dumps(stats, indent=2)) 