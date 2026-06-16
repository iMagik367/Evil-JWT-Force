"""
EVIL_JWT_FORCE - Strategy Selector Module
This module is responsible for selecting the optimal attack strategy based on 
the target context, previous attack results, and AI recommendations.
"""

import os
import json
import logging
import random
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'strategy_selector.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('STRATEGY_SELECTOR')

class StrategySelector:
    """
    Selects and prioritizes attack strategies based on target analysis, 
    previous attack history, and probability of success.
    """
    
    def __init__(self, config_path: str = 'config/strategy_config.json'):
        """
        Initialize the Strategy Selector with configuration settings.
        
        Args:
            config_path: Path to the strategy configuration file
        """
        self.config = self._load_config(config_path)
        self.attack_history = {}
        self.current_strategy = None
        self.available_strategies = self._load_strategies()
        self.exploitation_rate = self.config.get('exploitation_rate', 0.7)
        self.exploration_rate = 1.0 - self.exploitation_rate
        self.strategy_effectiveness = {}
        self.target_vulnerabilities = defaultdict(list)
        self.learning_rate = self.config.get('learning_rate', 0.1)
        
        # Initialize strategy effectiveness from history
        self._initialize_effectiveness_scores()
        
        logger.info("Strategy Selector initialized with %d available strategies", 
                   len(self.available_strategies))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'strategy_weights': {
                'jwt_bruteforce': 0.8,
                'jwt_fuzzing': 0.7,
                'sql_injection': 0.6,
                'jwt_none_attack': 0.9,
                'jwt_key_confusion': 0.7,
                'jwt_header_injection': 0.5,
                'osint_based_attack': 0.4,
                'parameter_tampering': 0.5,
                'nested_payload_attack': 0.6,
                'jwk_injection_attack': 0.7,
                'timestamp_manipulation': 0.6,
                'kid_manipulation': 0.7,
                'path_traversal': 0.5
            },
            'exploitation_rate': 0.7,
            'learning_rate': 0.1,
            'fallback_strategy': 'jwt_fuzzing',
            'max_attempts_per_strategy': 3,
            'success_threshold': 0.3,
            'adaptive_learning': {
                'enabled': True,
                'success_boost': 1.2,
                'failure_penalty': 0.8,
                'context_weight': 1.5
            },
            'vulnerability_weights': {
                'none_algorithm': 0.9,
                'brute_force_possible': 0.7,
                'no_expiration': 0.6,
                'no_issued_at': 0.6,
                'no_not_before': 0.6,
                'weak_algorithm': 0.7,
                'kid_parameter_present': 0.7,
                'jku_parameter_present': 0.7,
                'sensitive_data_exposure': 0.5,
                'far_future_expiration': 0.4
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
    
    def _load_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load the available attack strategies and their descriptions."""
        strategies = {
            'jwt_bruteforce': {
                'name': 'JWT Bruteforce Attack',
                'description': 'Attempts to crack the JWT secret using dictionary attacks',
                'module': 'core.bruteforce',
                'function': 'perform_bruteforce',
                'requirements': ['wordlist'],
                'applicable_when': ['jwt_uses_hs256', 'jwt_uses_hs384', 'jwt_uses_hs512'],
                'weight': self.config.get('strategy_weights', {}).get('jwt_bruteforce', 0.8),
                'fallbacks': ['jwt_fuzzing', 'jwt_none_attack']
            },
            'jwt_fuzzing': {
                'name': 'JWT Fuzzing',
                'description': 'Tests various JWT modifications to bypass security checks',
                'module': 'core.fuzz_jwt',
                'function': 'perform_fuzzing',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('jwt_fuzzing', 0.7),
                'fallbacks': ['jwt_none_attack', 'jwt_key_confusion']
            },
            'sql_injection': {
                'name': 'SQL Injection via JWT',
                'description': 'Attempts SQL injection through JWT payload fields',
                'module': 'core.sql_injector',
                'function': 'perform_sql_injection',
                'requirements': ['sql_payloads'],
                'applicable_when': ['jwt_has_database_fields', 'target_likely_uses_sql'],
                'weight': self.config.get('strategy_weights', {}).get('sql_injection', 0.6),
                'fallbacks': ['parameter_tampering']
            },
            'jwt_none_attack': {
                'name': 'JWT "none" Algorithm Attack',
                'description': 'Attempts to exploit JWT implementations that accept the "none" algorithm',
                'module': 'core.alg_attacks',
                'function': 'perform_none_attack',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('jwt_none_attack', 0.9),
                'fallbacks': ['jwt_key_confusion']
            },
            'jwt_key_confusion': {
                'name': 'JWT Key Confusion Attack',
                'description': 'Attempts to exploit JWT implementations with RSA/HMAC confusion',
                'module': 'core.alg_attacks',
                'function': 'perform_key_confusion',
                'requirements': ['public_key'],
                'applicable_when': ['jwt_uses_rs256', 'jwt_uses_es256'],
                'weight': self.config.get('strategy_weights', {}).get('jwt_key_confusion', 0.7),
                'fallbacks': ['jwt_fuzzing']
            },
            'jwt_header_injection': {
                'name': 'JWT Header Injection',
                'description': 'Attempts to inject malicious headers in JWT',
                'module': 'core.header_attacks',
                'function': 'perform_header_injection',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('jwt_header_injection', 0.5),
                'fallbacks': ['parameter_tampering']
            },
            'osint_based_attack': {
                'name': 'OSINT-based Attack',
                'description': 'Uses OSINT data to generate targeted wordlists and attack vectors',
                'module': 'modules.osint_enhanced',
                'function': 'perform_osint_attack',
                'requirements': ['target_domain'],
                'applicable_when': ['has_target_info'],
                'weight': self.config.get('strategy_weights', {}).get('osint_based_attack', 0.4),
                'fallbacks': ['jwt_bruteforce']
            },
            'parameter_tampering': {
                'name': 'Parameter Tampering',
                'description': 'Tests various parameter modifications to bypass security checks',
                'module': 'core.param_attacks',
                'function': 'perform_parameter_tampering',
                'requirements': [],
                'applicable_when': ['has_web_interface', 'has_api'],
                'weight': self.config.get('strategy_weights', {}).get('parameter_tampering', 0.5),
                'fallbacks': ['jwt_fuzzing']
            },
            'nested_payload_attack': {
                'name': 'Nested Payload Attack',
                'description': 'Creates nested objects in JWT payload to exploit parser vulnerabilities',
                'module': 'core.payload_attacks',
                'function': 'perform_nested_payload_attack',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('nested_payload_attack', 0.6),
                'fallbacks': ['jwt_fuzzing']
            },
            'jwk_injection_attack': {
                'name': 'JWK Injection Attack',
                'description': 'Injects malicious JWK data into JWT header',
                'module': 'core.header_attacks',
                'function': 'perform_jwk_injection',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('jwk_injection_attack', 0.7),
                'fallbacks': ['jwt_header_injection']
            },
            'timestamp_manipulation': {
                'name': 'Timestamp Manipulation',
                'description': 'Manipulates JWT timestamp claims to bypass time-based validations',
                'module': 'core.payload_attacks',
                'function': 'perform_timestamp_manipulation',
                'requirements': [],
                'applicable_when': ['has_jwt'],
                'weight': self.config.get('strategy_weights', {}).get('timestamp_manipulation', 0.6),
                'fallbacks': ['jwt_fuzzing']
            },
            'kid_manipulation': {
                'name': 'KID Parameter Manipulation',
                'description': 'Exploits the "kid" header parameter to perform path traversal or injection',
                'module': 'core.header_attacks',
                'function': 'perform_kid_manipulation',
                'requirements': [],
                'applicable_when': ['jwt_has_kid'],
                'weight': self.config.get('strategy_weights', {}).get('kid_manipulation', 0.7),
                'fallbacks': ['jwt_header_injection']
            },
            'path_traversal': {
                'name': 'Path Traversal via JWT',
                'description': 'Attempts path traversal through JWT header parameters',
                'module': 'core.header_attacks',
                'function': 'perform_path_traversal',
                'requirements': [],
                'applicable_when': ['jwt_has_kid', 'jwt_has_jku'],
                'weight': self.config.get('strategy_weights', {}).get('path_traversal', 0.5),
                'fallbacks': ['jwt_header_injection']
            }
        }
        
        return strategies
    
    def _initialize_effectiveness_scores(self) -> None:
        """Initialize strategy effectiveness scores from history."""
        try:
            history_file = os.path.join('data', 'attack_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                
                if 'strategy_effectiveness' in history_data:
                    self.strategy_effectiveness = history_data['strategy_effectiveness']
                    logger.info("Loaded effectiveness scores for %d strategies", 
                              len(self.strategy_effectiveness))
        except Exception as e:
            logger.error(f"Error loading effectiveness scores: {str(e)}")
    
    def select_strategy(self, context: Dict[str, Any], ai_recommendations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Select the optimal attack strategy based on the current context and AI recommendations.
        
        Args:
            context: Information about the target and attack context
            ai_recommendations: Optional recommendations from the AI engine
            
        Returns:
            Dictionary containing the selected strategy
        """
        logger.info("Selecting strategy based on context and AI recommendations")
        
        # Filter applicable strategies based on context
        applicable_strategies = self._filter_applicable_strategies(context)
        
        if not applicable_strategies:
            logger.warning("No applicable strategies found. Using fallback strategy.")
            fallback = self.config.get('fallback_strategy', 'jwt_fuzzing')
            return self._prepare_strategy_response(fallback)
        
        # Adjust weights based on AI recommendations if available
        if ai_recommendations:
            applicable_strategies = self._adjust_weights_from_ai(applicable_strategies, ai_recommendations)
        
        # Use exploitation vs exploration to decide strategy selection approach
        if random.random() < self.exploitation_rate:
            # Exploitation: Pick the strategy with the highest weight
            selected_strategy_name = max(applicable_strategies.items(), 
                                        key=lambda x: x[1]['weight'])[0]
            logger.info("Exploitation: Selected strategy '%s' with weight %.2f", 
                       selected_strategy_name, applicable_strategies[selected_strategy_name]['weight'])
        else:
            # Exploration: Weighted random selection
            strategies = list(applicable_strategies.keys())
            weights = [s['weight'] for s in applicable_strategies.values()]
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight > 0:
                normalized_weights = [w/total_weight for w in weights]
            else:
                normalized_weights = [1.0/len(weights)] * len(weights)
            
            selected_strategy_name = random.choices(strategies, weights=normalized_weights, k=1)[0]
            logger.info("Exploration: Selected strategy '%s' with weight %.2f", 
                       selected_strategy_name, applicable_strategies[selected_strategy_name]['weight'])
        
        # Record the strategy selection
        self._record_strategy_selection(selected_strategy_name, context)
        
        return self._prepare_strategy_response(selected_strategy_name)
    
    def select_optimal_strategy(self, token_analysis: Dict[str, Any], context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the optimal attack strategy based on token analysis and context analysis.
        
        This is a higher-level method that integrates with the main system and uses
        both token analysis and context analysis to make a more informed decision.
        
        Args:
            token_analysis: Analysis of the JWT token
            context_analysis: Contextual analysis of the target
            
        Returns:
            Dictionary containing the selected strategy and execution plan
        """
        logger.info("Selecting optimal strategy based on token and context analysis")
        
        # Create a combined context from token and context analysis
        combined_context = self._create_combined_context(token_analysis, context_analysis)
        
        # Extract AI recommendations from token analysis if available
        ai_recommendations = None
        if 'recommended_attacks' in token_analysis:
            ai_recommendations = {
                'recommended_strategies': token_analysis['recommended_attacks'],
                'confidence': token_analysis.get('confidence_score', 0.5)
            }
        
        # Select the strategy
        strategy = self.select_strategy(combined_context, ai_recommendations)
        
        # Enhance the strategy with additional information
        enhanced_strategy = self._enhance_strategy_with_context(strategy, token_analysis, context_analysis)
        
        # Determine if bruteforce should be attempted
        enhanced_strategy['should_bruteforce'] = self._should_attempt_bruteforce(token_analysis, context_analysis)
        
        # Add vulnerability-specific recommendations
        enhanced_strategy['vulnerability_specific_actions'] = self._get_vulnerability_specific_actions(token_analysis)
        
        # Add execution plan
        enhanced_strategy['execution_plan'] = self._create_execution_plan(enhanced_strategy, token_analysis)
        
        # Add confidence score
        enhanced_strategy['confidence_score'] = self._calculate_strategy_confidence(enhanced_strategy, token_analysis)
        
        return enhanced_strategy
    
    def _create_combined_context(self, token_analysis: Dict[str, Any], context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a combined context from token and context analysis."""
        combined = {
            'has_jwt': True  # We know we have a JWT if we're analyzing it
        }
        
        # Add token algorithm information
        if 'header' in token_analysis and 'alg' in token_analysis['header']:
            alg = token_analysis['header']['alg'].lower()
            combined[f'jwt_uses_{alg}'] = True
        
        # Add vulnerability information
        if 'vulnerabilities' in token_analysis:
            for vuln in token_analysis['vulnerabilities']:
                vuln_type = vuln.get('type', '')
                if vuln_type == 'none_algorithm':
                    combined['jwt_vulnerable_to_none'] = True
                elif vuln_type == 'brute_force_possible':
                    combined['jwt_vulnerable_to_bruteforce'] = True
                elif vuln_type == 'no_expiration':
                    combined['jwt_no_expiration'] = True
                elif vuln_type == 'kid_parameter_present':
                    combined['jwt_has_kid'] = True
                elif vuln_type == 'jku_parameter_present':
                    combined['jwt_has_jku'] = True
        
        # Add header parameter information
        if 'header' in token_analysis:
            header = token_analysis['header']
            if 'kid' in header:
                combined['jwt_has_kid'] = True
            if 'jku' in header:
                combined['jwt_has_jku'] = True
            if 'jwk' in header:
                combined['jwt_has_jwk'] = True
        
        # Add context information
        if 'token_usage' in context_analysis:
            combined['token_usage'] = context_analysis['token_usage']
        if 'issuer_type' in context_analysis:
            combined['issuer_type'] = context_analysis['issuer_type']
        if 'application_type' in context_analysis:
            combined['application_type'] = context_analysis['application_type']
        
        # Add risk score for strategy weighting
        if 'risk_score' in context_analysis:
            combined['token_risk_score'] = context_analysis['risk_score']

        # Add compliance flags as context flags
        if 'compliance_flags' in context_analysis:
            for flag in context_analysis['compliance_flags']:
                combined[f'token_flag_{flag}'] = True

        return combined
    
    def _enhance_strategy_with_context(self, strategy: Dict[str, Any], 
                                     token_analysis: Dict[str, Any], 
                                     context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance the selected strategy with contextual information."""
        enhanced = strategy.copy()
        
        # Add token information
        if 'header' in token_analysis:
            enhanced['token_algorithm'] = token_analysis['header'].get('alg', 'unknown')
        
        # Add vulnerability information
        if 'vulnerabilities' in token_analysis:
            enhanced['vulnerabilities'] = [v['type'] for v in token_analysis['vulnerabilities']]
            
            # Set severity based on highest vulnerability severity
            severities = [v.get('severity', 'low') for v in token_analysis['vulnerabilities']]
            if 'high' in severities:
                enhanced['severity'] = 'high'
            elif 'medium' in severities:
                enhanced['severity'] = 'medium'
            else:
                enhanced['severity'] = 'low'
        
        # Add context information
        if 'token_usage' in context_analysis:
            enhanced['token_usage'] = context_analysis['token_usage']
        if 'issuer_type' in context_analysis:
            enhanced['issuer_type'] = context_analysis['issuer_type']
        
        return enhanced
    
    def _should_attempt_bruteforce(self, token_analysis: Dict[str, Any], 
                                 context_analysis: Dict[str, Any]) -> bool:
        """Determine if bruteforce should be attempted based on analysis."""
        # Check if algorithm is suitable for bruteforce
        if 'header' in token_analysis and 'alg' in token_analysis['header']:
            alg = token_analysis['header']['alg'].lower()
            if alg in ['hs256', 'hs384', 'hs512']:
                # Check for vulnerabilities that suggest bruteforce
                if 'vulnerabilities' in token_analysis:
                    for vuln in token_analysis['vulnerabilities']:
                        if vuln.get('type') == 'brute_force_possible':
                            return True
        
        return False
    
    def _get_vulnerability_specific_actions(self, token_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get specific actions based on identified vulnerabilities."""
        actions = []
        
        if 'vulnerabilities' in token_analysis:
            for vuln in token_analysis['vulnerabilities']:
                vuln_type = vuln.get('type', '')
                
                if vuln_type == 'none_algorithm':
                    actions.append({
                        'action': 'try_none_algorithm',
                        'description': 'Try setting algorithm to "none"',
                        'priority': 'high'
                    })
                elif vuln_type == 'no_expiration':
                    actions.append({
                        'action': 'manipulate_timestamps',
                        'description': 'Manipulate or remove expiration claims',
                        'priority': 'medium'
                    })
                elif vuln_type == 'kid_parameter_present':
                    actions.append({
                        'action': 'manipulate_kid',
                        'description': 'Try path traversal or SQL injection via kid parameter',
                        'priority': 'high'
                    })
                elif vuln_type == 'jku_parameter_present':
                    actions.append({
                        'action': 'manipulate_jku',
                        'description': 'Point jku to attacker-controlled URL',
                        'priority': 'high'
                    })
        
        return actions
    
    def _create_execution_plan(self, strategy: Dict[str, Any], 
                             token_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a step-by-step execution plan for the selected strategy."""
        plan = []
        
        # Add steps based on strategy type
        strategy_name = strategy.get('name', '').lower()
        
        if 'none' in strategy_name:
            plan.append({
                'step': 1,
                'action': 'modify_algorithm',
                'params': {'alg': 'none'},
                'description': 'Set algorithm to "none"'
            })
            plan.append({
                'step': 2,
                'action': 'remove_signature',
                'description': 'Remove or empty the signature part'
            })
            
        elif 'bruteforce' in strategy_name:
            plan.append({
                'step': 1,
                'action': 'generate_wordlist',
                'description': 'Generate or select wordlist'
            })
            plan.append({
                'step': 2,
                'action': 'perform_bruteforce',
                'params': {'timeout': 60, 'max_attempts': 10000},
                'description': 'Attempt to crack the secret'
            })
            
        elif 'fuzzing' in strategy_name:
            plan.append({
                'step': 1,
                'action': 'generate_mutations',
                'params': {'limit': 20},
                'description': 'Generate token mutations'
            })
            plan.append({
                'step': 2,
                'action': 'test_mutations',
                'description': 'Test mutations against target'
            })
            plan.append({
                'step': 3,
                'action': 'analyze_responses',
                'description': 'Analyze responses for vulnerabilities'
            })
            
        # Add vulnerability-specific steps
        if 'vulnerabilities' in token_analysis:
            for vuln in token_analysis['vulnerabilities']:
                vuln_type = vuln.get('type', '')
                
                if vuln_type == 'kid_parameter_present' and not any('kid' in step.get('description', '').lower() for step in plan):
                    plan.append({
                        'step': len(plan) + 1,
                        'action': 'test_kid_injection',
                        'params': {'payloads': ['../../../dev/null', '1=1', 'non_existing_key']},
                        'description': 'Test kid parameter injection'
                    })
        
        return plan
    
    def _calculate_strategy_confidence(self, strategy: Dict[str, Any], 
                                     token_analysis: Dict[str, Any]) -> float:
        """Calculate a confidence score for the selected strategy."""
        base_confidence = 0.5  # Start with 50% confidence
        
        # Adjust based on strategy effectiveness history
        strategy_name = strategy.get('id', '')
        if strategy_name in self.strategy_effectiveness:
            base_confidence = self.strategy_effectiveness[strategy_name]
        
        # Adjust based on vulnerabilities
        if 'vulnerabilities' in token_analysis:
            vulnerability_weights = self.config.get('vulnerability_weights', {})
            for vuln in token_analysis['vulnerabilities']:
                vuln_type = vuln.get('type', '')
                if vuln_type in vulnerability_weights:
                    # Boost confidence if strategy targets this vulnerability
                    if (vuln_type == 'none_algorithm' and 'none' in strategy.get('name', '').lower()) or \
                       (vuln_type == 'brute_force_possible' and 'bruteforce' in strategy.get('name', '').lower()) or \
                       (vuln_type == 'kid_parameter_present' and 'kid' in strategy.get('name', '').lower()):
                        base_confidence += vulnerability_weights[vuln_type] * 0.2
        
        # Cap at 0.95 (95% confidence)
        return min(0.95, base_confidence)
    
    def _filter_applicable_strategies(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Filter strategies that are applicable in the current context."""
        applicable = {}
        
        for strategy_name, strategy_info in self.available_strategies.items():
            # Check if all requirements are met
            requirements_met = all(req in context for req in strategy_info['requirements'])
            
            # Check if the strategy is applicable in the current context
            applicable_conditions = strategy_info['applicable_when']
            conditions_met = any(context.get(cond, False) for cond in applicable_conditions)
            
            if requirements_met and conditions_met:
                applicable[strategy_name] = strategy_info.copy()
        
        logger.info("Filtered %d applicable strategies from %d total strategies", 
                   len(applicable), len(self.available_strategies))
        
        return applicable
    
    def _adjust_weights_from_ai(self, strategies: Dict[str, Dict[str, Any]], 
                              ai_recommendations: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Adjust strategy weights based on AI recommendations."""
        adjusted_strategies = strategies.copy()
        
        # Get recommended attack vectors from AI
        recommended_vectors = ai_recommendations.get('recommended_attacks', [])
        
        # Map of attack vectors to strategy names
        vector_to_strategy = {
            'brute_force': 'jwt_bruteforce',
            'none_algorithm_exploit': 'jwt_none_attack',
            'token_manipulation': 'jwt_fuzzing',
            'key_confusion': 'jwt_key_confusion',
            'header_injection': 'jwt_header_injection',
            'sql_injection': 'sql_injection',
            'osint': 'osint_based_attack',
            'parameter_tampering': 'parameter_tampering'
        }
        
        # Adjust weights based on AI recommendations
        for vector in recommended_vectors:
            if vector in vector_to_strategy:
                strategy_name = vector_to_strategy[vector]
                if strategy_name in adjusted_strategies:
                    # Increase weight for recommended strategies
                    adjusted_strategies[strategy_name]['weight'] *= 1.5
                    logger.info("Increased weight for AI-recommended strategy '%s'", strategy_name)
        
        # Normalize weights if needed
        total_weight = sum(s['weight'] for s in adjusted_strategies.values())
        if total_weight > 0:
            for strategy in adjusted_strategies.values():
                strategy['weight'] /= total_weight
                strategy['weight'] *= len(adjusted_strategies)  # Scale back to similar range
        
        return adjusted_strategies
    
    def _record_strategy_selection(self, strategy_name: str, context: Dict[str, Any]) -> None:
        """Record the selected strategy in attack history."""
        timestamp = datetime.now().isoformat()
        
        if strategy_name not in self.attack_history:
            self.attack_history[strategy_name] = []
        
        # Record minimal context information
        minimal_context = {
            'timestamp': timestamp,
            'target_type': context.get('target_type', 'unknown'),
            'jwt_alg': context.get('jwt_alg', 'unknown'),
            'success': None  # Will be updated after execution
        }
        
        self.attack_history[strategy_name].append(minimal_context)
        self.current_strategy = strategy_name
        
        # Log the selection
        logger.info("Selected strategy '%s' recorded in attack history", strategy_name)
    
    def _prepare_strategy_response(self, strategy_name: str) -> Dict[str, Any]:
        """Prepare the response with the selected strategy information."""
        if strategy_name not in self.available_strategies:
            # Fallback to a default strategy if the selected one is not available
            strategy_name = self.config.get('fallback_strategy', 'jwt_fuzzing')
            logger.warning("Selected strategy '%s' not available. Using fallback '%s'", 
                          strategy_name, self.config.get('fallback_strategy'))
        
        strategy = self.available_strategies[strategy_name]
        
        return {
            'strategy_name': strategy_name,
            'display_name': strategy['name'],
            'description': strategy['description'],
            'module': strategy['module'],
            'function': strategy['function'],
            'requirements': strategy['requirements'],
            'fallbacks': strategy['fallbacks'],
            'weight': strategy['weight']
        }
    
    def update_strategy_result(self, strategy_name: str, success: bool, 
                             execution_time: float, details: Dict[str, Any]) -> None:
        """
        Update the result of an executed strategy to improve future selections.
        
        Args:
            strategy_name: Name of the executed strategy
            success: Whether the strategy was successful
            execution_time: Time taken to execute the strategy in seconds
            details: Additional details about the execution result
        """
        if strategy_name not in self.attack_history or not self.attack_history[strategy_name]:
            logger.warning("No history record found for strategy '%s'", strategy_name)
            return
        
        # Update the last execution result
        self.attack_history[strategy_name][-1]['success'] = success
        self.attack_history[strategy_name][-1]['execution_time'] = execution_time
        self.attack_history[strategy_name][-1].update(details)
        
        # Adjust the strategy weight based on the result
        if strategy_name in self.available_strategies:
            learning_rate = self.config.get('learning_rate', 0.1)
            current_weight = self.available_strategies[strategy_name]['weight']
            
            if success:
                # Increase weight if successful
                new_weight = current_weight + learning_rate * (1 - current_weight)
            else:
                # Decrease weight if unsuccessful
                new_weight = current_weight - learning_rate * current_weight
            
            # Ensure weight stays in valid range
            new_weight = max(0.1, min(1.0, new_weight))
            self.available_strategies[strategy_name]['weight'] = new_weight
            
            logger.info("Updated weight for strategy '%s': %.2f -> %.2f", 
                       strategy_name, current_weight, new_weight)
        
        # Save the updated attack history
        self._save_attack_history()
    
    def _save_attack_history(self) -> None:
        """Save the attack history to a file."""
        history_file = os.path.join('data', 'strategy_history.json')
        
        try:
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(self.attack_history, f, indent=2)
            logger.info("Attack history saved to %s", history_file)
        except Exception as e:
            logger.error("Error saving attack history: %s", str(e))
    
    def get_fallback_strategy(self, failed_strategy: str) -> Dict[str, Any]:
        """
        Get a fallback strategy when the current strategy fails.
        
        Args:
            failed_strategy: The name of the strategy that failed
            
        Returns:
            Dictionary containing the fallback strategy information
        """
        if failed_strategy not in self.available_strategies:
            logger.warning("Failed strategy '%s' not found in available strategies", failed_strategy)
            fallback = self.config.get('fallback_strategy', 'jwt_fuzzing')
            return self._prepare_strategy_response(fallback)
        
        # Get fallback strategies for the failed strategy
        fallbacks = self.available_strategies[failed_strategy].get('fallbacks', [])
        
        if not fallbacks:
            # Use default fallback if no specific fallbacks defined
            logger.info("No fallbacks defined for '%s'. Using default fallback.", failed_strategy)
            fallback = self.config.get('fallback_strategy', 'jwt_fuzzing')
            return self._prepare_strategy_response(fallback)
        
        # Check if we've already tried the maximum number of attempts for this strategy
        strategy_attempts = 0
        for entry in self.attack_history.get(failed_strategy, []):
            if entry.get('success') is False:
                strategy_attempts += 1
        
        max_attempts = self.config.get('max_attempts_per_strategy', 3)
        if strategy_attempts >= max_attempts:
            # Too many failed attempts, choose a fallback
            fallback = fallbacks[0]  # Use the first fallback
            logger.info("Max attempts (%d) reached for '%s'. Using fallback '%s'.", 
                       max_attempts, failed_strategy, fallback)
            return self._prepare_strategy_response(fallback)
        
        # Otherwise, suggest trying the same strategy with modified parameters
        logger.info("Suggesting retry of '%s' with modified parameters.", failed_strategy)
        response = self._prepare_strategy_response(failed_strategy)
        response['is_retry'] = True
        response['modified_parameters'] = True
        return response


if __name__ == "__main__":
    # Example usage
    selector = StrategySelector()
    
    # Example context
    context = {
        'has_jwt': True,
        'jwt_alg': 'HS256',
        'jwt_has_exp': True,
        'wordlist': '/path/to/wordlist.txt',
        'target_type': 'web_application',
        'has_api': True
    }
    
    # Example AI recommendations
    ai_recommendations = {
        'recommended_attacks': ['brute_force', 'token_manipulation']
    }
    
    # Select strategy
    selected_strategy = selector.select_strategy(context, ai_recommendations)
    print("Selected strategy:", json.dumps(selected_strategy, indent=2))
    
    # Update strategy result
    selector.update_strategy_result(
        selected_strategy['strategy_name'],
        success=True,
        execution_time=45.2,
        details={'found_secret': 'password123'}
    )
    
    # Get fallback strategy
    fallback = selector.get_fallback_strategy(selected_strategy['strategy_name'])
    print("Fallback strategy:", json.dumps(fallback, indent=2)) 