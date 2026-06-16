#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - REST API Module
A RESTful API for the AI-driven JWT security testing framework.
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Add the parent directory to sys.path to import from ai_system
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, 'logs', 'api.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JWT_API')

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import AI system components
try:
    from ai_system.engine import AIEngine
    from ai_module.jwt_predictor import JWTPredictor
    from ai_module.adaptive_fuzzer import AdaptiveFuzzer
    from modules.token_bruteforce import TokenBruteforcer
    from modules.scan_target import TargetScanner
    HAS_AI_MODULES = True
    
    # Initialize AI components
    ai_engine = AIEngine()
    jwt_predictor = JWTPredictor()
    adaptive_fuzzer = AdaptiveFuzzer()
    
    logger.info("AI components initialized successfully")
except ImportError as e:
    logger.error(f"Error importing AI modules: {str(e)}")
    HAS_AI_MODULES = False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'ai_modules': HAS_AI_MODULES
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_token():
    """Analyze a JWT token"""
    if not HAS_AI_MODULES:
        return jsonify({'error': 'AI modules not available'}), 503
    
    data = request.json
    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400
    
    token = data.get('token')
    
    try:
        # Analyze token
        analysis = ai_engine.analyze_token(token)
        
        # Get attack recommendations
        target_info = {
            'has_api': data.get('has_api', True),
            'has_web_interface': data.get('has_web_interface', True),
            'response_contains_json': data.get('response_contains_json', True),
            'allows_header_injection': data.get('allows_header_injection', False)
        }
        
        recommendations = ai_engine.get_attack_recommendations(token, target_info)
        
        # Combine results
        result = {
            'analysis': analysis,
            'recommendations': recommendations
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing token: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def scan_target():
    """Scan a target URL for JWT tokens and vulnerabilities"""
    if not HAS_AI_MODULES:
        return jsonify({'error': 'AI modules not available'}), 503
    
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data.get('url')
    
    try:
        # Create scanner and run scan
        scanner = TargetScanner(url)
        scan_results = scanner.scan()
        
        return jsonify(scan_results)
    except Exception as e:
        logger.error(f"Error scanning target: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bruteforce', methods=['POST'])
def bruteforce_token():
    """Attempt to bruteforce a JWT token"""
    if not HAS_AI_MODULES:
        return jsonify({'error': 'AI modules not available'}), 503
    
    data = request.json
    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400
    
    token = data.get('token')
    wordlist = data.get('wordlist')
    timeout = data.get('timeout', 60)
    
    try:
        # Check if wordlist exists
        if not wordlist or not os.path.exists(wordlist):
            # Generate wordlist with predictor
            logger.info("Generating wordlist with JWTPredictor")
            generated_wordlist = jwt_predictor.generate_wordlist(token, max_words=1000)
            
            # Save generated wordlist to temporary file
            temp_wordlist = os.path.join(parent_dir, 'data', 'temp_wordlist.txt')
            with open(temp_wordlist, 'w') as f:
                f.write('\n'.join(generated_wordlist))
            
            wordlist = temp_wordlist
        
        # Create bruteforcer and run with timeout
        bruteforcer = TokenBruteforcer(token)
        result = bruteforcer.bruteforce_with_timeout(wordlist, timeout=timeout)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error bruteforcing token: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fuzz', methods=['POST'])
def fuzz_token():
    """Generate mutations for a JWT token"""
    if not HAS_AI_MODULES:
        return jsonify({'error': 'AI modules not available'}), 503
    
    data = request.json
    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400
    
    token = data.get('token')
    limit = data.get('limit', 20)
    
    try:
        # Generate mutations
        mutations = adaptive_fuzzer.generate_mutations(token, limit=limit)
        
        return jsonify({
            'token': token,
            'mutations': mutations,
            'count': len(mutations)
        })
    except Exception as e:
        logger.error(f"Error fuzzing token: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_secrets():
    """Predict potential secrets for a JWT token"""
    if not HAS_AI_MODULES:
        return jsonify({'error': 'AI modules not available'}), 503
    
    data = request.json
    if not data or 'token' not in data:
        return jsonify({'error': 'Token is required'}), 400
    
    token = data.get('token')
    max_words = data.get('max_words', 100)
    target_info = data.get('target_info', {})
    
    try:
        # Set target info if provided
        if target_info:
            jwt_predictor.set_target_info(target_info)
        
        # Generate wordlist
        wordlist = jwt_predictor.generate_wordlist(token, max_words=max_words)
        
        return jsonify({
            'token': token,
            'wordlist': wordlist,
            'count': len(wordlist)
        })
    except Exception as e:
        logger.error(f"Error predicting secrets: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(os.path.join(parent_dir, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(parent_dir, 'data'), exist_ok=True)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 