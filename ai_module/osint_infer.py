"""
EVIL_JWT_FORCE - OSINT Inference Module
This module uses NLP and inference techniques to generate new keywords and patterns
based on collected OSINT data.
"""

import os
import sys
import json
import logging
import re
import random
import string
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'osint_infer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OSINT_INFER')

class OSINTInfer:
    """
    Generates new keywords and patterns using NLP techniques on OSINT data.
    
    This class analyzes collected OSINT data, extracts relevant information,
    and generates potential passwords, secrets, and patterns that might be used
    by the target organization.
    """
    
    def __init__(self, config_path: str = 'config/osint_infer_config.json'):
        """
        Initialize the OSINT inference engine with configuration settings.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.word_patterns = self.config.get('word_patterns', {})
        self.common_separators = self.config.get('common_separators', [])
        self.blacklisted_terms = self.config.get('blacklisted_terms', [])
        self.common_prefixes = self.config.get('common_prefixes', [])
        self.common_suffixes = self.config.get('common_suffixes', [])
        self.date_patterns = self.config.get('date_patterns', [])
        self.collected_data = {}
        self.inferred_keywords = set()
        
        logger.info("OSINT Inference engine initialized with %d word patterns", 
                   len(self.word_patterns))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults if file not found."""
        default_config = {
            'word_patterns': {
                'company_name': 5,
                'product_name': 4,
                'domain_name': 4,
                'founder_name': 3,
                'location': 2,
                'technology': 3,
                'industry': 2,
                'motto': 1,
                'year_founded': 3
            },
            'common_separators': [
                '', '-', '_', '.', '!', '@', '#', '$', '1', '123', '2022', '2023', '2024'
            ],
            'blacklisted_terms': [
                'the', 'and', 'inc', 'corp', 'incorporated', 'corporation', 'company',
                'ltd', 'limited', 'llc', 'a', 'an', 'of', 'in', 'for', 'to', 'with'
            ],
            'common_prefixes': [
                'admin', 'root', 'user', 'system', 'api', 'app', 'web', 'dev', 'prod',
                'test', 'stage', 'jwt', 'token', 'auth', 'secure', 'key', 'secret', 'pass'
            ],
            'common_suffixes': [
                'admin', 'key', 'secret', 'token', 'password', 'pass', 'api', 'app',
                '123', '1234', '12345', 'dev', 'prod', 'test', 'stage', '2022', '2023', '2024'
            ],
            'date_patterns': [
                '%Y', '%y', '%m%d', '%d%m', '%Y%m', '%m%Y',
                '%Y%m%d', '%d%m%Y', '%m%d%Y'
            ],
            'max_word_combinations': 3,
            'max_keywords': 1000,
            'min_keyword_length': 3,
            'max_keyword_length': 64
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
    
    def set_osint_data(self, data: Dict[str, Any]) -> None:
        """
        Set the collected OSINT data.
        
        Args:
            data: Dictionary containing OSINT data about the target
        """
        self.collected_data = data
        logger.info("OSINT data set with %d fields", len(data))
        
        # Clear previously inferred keywords
        self.inferred_keywords = set()
    
    def extract_key_terms(self) -> Dict[str, List[str]]:
        """
        Extract key terms from the OSINT data.
        
        Returns:
            Dictionary with categorized key terms
        """
        key_terms = {}
        
        # Process company name
        if 'company_name' in self.collected_data:
            company_name = self.collected_data['company_name']
            key_terms['company_name'] = self._extract_words(company_name)
        
        # Process domain name
        if 'domain' in self.collected_data:
            domain = self.collected_data['domain']
            # Extract domain without TLD
            domain_parts = domain.split('.')
            if len(domain_parts) > 1:
                key_terms['domain_name'] = self._extract_words(domain_parts[0])
        
        # Process product names
        if 'products' in self.collected_data:
            products = self.collected_data['products']
            if isinstance(products, list):
                key_terms['product_name'] = []
                for product in products:
                    key_terms['product_name'].extend(self._extract_words(product))
            elif isinstance(products, str):
                key_terms['product_name'] = self._extract_words(products)
        
        # Process technologies
        if 'technologies' in self.collected_data:
            techs = self.collected_data['technologies']
            if isinstance(techs, list):
                key_terms['technology'] = []
                for tech in techs:
                    key_terms['technology'].extend(self._extract_words(tech))
            elif isinstance(techs, str):
                key_terms['technology'] = self._extract_words(techs)
        
        # Process founders
        if 'founders' in self.collected_data:
            founders = self.collected_data['founders']
            if isinstance(founders, list):
                key_terms['founder_name'] = []
                for founder in founders:
                    key_terms['founder_name'].extend(self._extract_words(founder))
            elif isinstance(founders, str):
                key_terms['founder_name'] = self._extract_words(founders)
        
        # Process other fields
        for field, weight in self.word_patterns.items():
            if field in self.collected_data and field not in key_terms:
                value = self.collected_data[field]
                if isinstance(value, str):
                    key_terms[field] = self._extract_words(value)
                elif isinstance(value, list):
                    key_terms[field] = []
                    for item in value:
                        if isinstance(item, str):
                            key_terms[field].extend(self._extract_words(item))
        
        logger.info("Extracted key terms from OSINT data: %d categories", len(key_terms))
        return key_terms
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text."""
        if not text:
            return []
        
        # Clean the text and split into words
        text = re.sub(r'[^\w\s-]', ' ', text.lower())
        words = text.split()
        
        # Filter out blacklisted terms and short words
        filtered_words = [
            word for word in words
            if word not in self.blacklisted_terms and len(word) >= 3
        ]
        
        # Also split by common separators like hyphen and underscore
        split_words = []
        for word in filtered_words:
            if '-' in word:
                split_words.extend(word.split('-'))
            elif '_' in word:
                split_words.extend(word.split('_'))
        
        # Combine and deduplicate
        all_words = filtered_words + split_words
        return list(set(all_words))
    
    def generate_keywords(self, max_keywords: Optional[int] = None) -> List[str]:
        """
        Generate keywords based on the OSINT data.
        
        Args:
            max_keywords: Maximum number of keywords to generate
            
        Returns:
            List of generated keywords
        """
        if not self.collected_data:
            logger.warning("No OSINT data available for keyword generation")
            return []
        
        if not max_keywords:
            max_keywords = self.config.get('max_keywords', 1000)
        
        # Extract key terms
        key_terms = self.extract_key_terms()
        
        # Generate base keywords
        keywords = set()
        
        # Add individual key terms with high weights
        for term_type, terms in key_terms.items():
            weight = self.word_patterns.get(term_type, 1)
            if weight >= 3:  # Only add high-weight terms as standalone keywords
                for term in terms:
                    if len(term) >= self.config.get('min_keyword_length', 3):
                        keywords.add(term)
        
        # Generate combinations of key terms
        combinations = self._generate_term_combinations(key_terms)
        keywords.update(combinations)
        
        # Add prefixed and suffixed versions
        prefixed = self._add_prefixes(keywords)
        suffixed = self._add_suffixes(keywords)
        keywords.update(prefixed)
        keywords.update(suffixed)
        
        # Add date variations if founding year is available
        if 'year_founded' in self.collected_data:
            year = str(self.collected_data['year_founded'])
            date_variants = self._generate_date_variants(keywords, year)
            keywords.update(date_variants)
        
        # Apply transformations (leetspeak, capitalization, etc.)
        transformed = self._apply_transformations(keywords)
        keywords.update(transformed)
        
        # Filter by length
        min_length = self.config.get('min_keyword_length', 3)
        max_length = self.config.get('max_keyword_length', 64)
        filtered_keywords = {
            kw for kw in keywords
            if min_length <= len(kw) <= max_length
        }
        
        # Store inferred keywords
        self.inferred_keywords = filtered_keywords
        
        # Convert to list and limit to max_keywords
        keyword_list = list(filtered_keywords)
        if len(keyword_list) > max_keywords:
            # Sort by length (shorter first) to prioritize more common patterns
            keyword_list.sort(key=len)
            keyword_list = keyword_list[:max_keywords]
        
        logger.info("Generated %d keywords from OSINT data", len(keyword_list))
        return keyword_list
    
    def _generate_term_combinations(self, key_terms: Dict[str, List[str]]) -> Set[str]:
        """Generate combinations of key terms."""
        combinations = set()
        max_combinations = self.config.get('max_word_combinations', 3)
        
        # Get all terms flattened with their weights
        weighted_terms = []
        for term_type, terms in key_terms.items():
            weight = self.word_patterns.get(term_type, 1)
            for term in terms:
                weighted_terms.append((term, weight))
        
        # Sort by weight (highest first)
        weighted_terms.sort(key=lambda x: x[1], reverse=True)
        
        # Take top terms to reduce combinatorial explosion
        top_terms = [t[0] for t in weighted_terms[:20]]
        
        # Generate combinations with separators
        for term1 in top_terms:
            # Single term with separators
            for sep in self.common_separators:
                combinations.add(f"{term1}{sep}")
            
            # Two terms
            if max_combinations >= 2:
                for term2 in top_terms:
                    if term1 != term2:
                        for sep in self.common_separators:
                            combinations.add(f"{term1}{sep}{term2}")
            
            # Three terms
            if max_combinations >= 3:
                for term2 in top_terms:
                    if term1 != term2:
                        for term3 in top_terms:
                            if term1 != term3 and term2 != term3:
                                for sep in self.common_separators:
                                    combinations.add(f"{term1}{sep}{term2}{sep}{term3}")
        
        return combinations
    
    def _add_prefixes(self, keywords: Set[str]) -> Set[str]:
        """Add common prefixes to keywords."""
        prefixed = set()
        
        for keyword in keywords:
            for prefix in self.common_prefixes:
                for sep in self.common_separators:
                    prefixed.add(f"{prefix}{sep}{keyword}")
        
        return prefixed
    
    def _add_suffixes(self, keywords: Set[str]) -> Set[str]:
        """Add common suffixes to keywords."""
        suffixed = set()
        
        for keyword in keywords:
            for suffix in self.common_suffixes:
                for sep in self.common_separators:
                    suffixed.add(f"{keyword}{sep}{suffix}")
        
        return suffixed
    
    def _generate_date_variants(self, keywords: Set[str], year: str) -> Set[str]:
        """Generate date variations of keywords."""
        date_variants = set()
        
        # Add standalone year
        date_variants.add(year)
        date_variants.add(year[-2:])  # Last two digits
        
        # Get current year and derived years
        current_year = datetime.now().year
        founding_year = int(year)
        years = [year, str(current_year)]
        
        # Add +/- 1 year for common patterns
        for y in range(current_year - 2, current_year + 2):
            if y != current_year and y != founding_year:
                years.append(str(y))
        
        # Create date combinations
        for keyword in keywords:
            for y in years:
                for sep in self.common_separators:
                    date_variants.add(f"{keyword}{sep}{y}")
                    date_variants.add(f"{y}{sep}{keyword}")
        
        return date_variants
    
    def _apply_transformations(self, keywords: Set[str]) -> Set[str]:
        """Apply transformations to keywords."""
        transformed = set()
        
        for keyword in keywords:
            # Capitalization variants
            transformed.add(keyword.lower())
            transformed.add(keyword.upper())
            transformed.add(keyword.capitalize())
            
            # Leetspeak transformation
            leet_mapping = {
                'a': '4', 'e': '3', 'i': '1', 'o': '0',
                's': '5', 't': '7', 'b': '8', 'g': '9'
            }
            
            leet_word = keyword.lower()
            for char, leet_char in leet_mapping.items():
                leet_word = leet_word.replace(char, leet_char)
            
            if leet_word != keyword.lower():
                transformed.add(leet_word)
            
            # Common number appendages
            for num in ['1', '123', '1234', '12345']:
                transformed.add(f"{keyword}{num}")
        
        return transformed
    
    def prioritize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Prioritize keywords based on likely relevance.
        
        Args:
            keywords: List of keywords to prioritize
            
        Returns:
            Prioritized list of keywords
        """
        scored_keywords = []
        
        company_name = self.collected_data.get('company_name', '').lower()
        domain = self.collected_data.get('domain', '').lower()
        year_founded = str(self.collected_data.get('year_founded', ''))
        
        for keyword in keywords:
            score = 0
            kw_lower = keyword.lower()
            
            # Relevance to company name
            if company_name and company_name in kw_lower:
                score += 10
            elif company_name and any(part in kw_lower for part in company_name.split()):
                score += 5
            
            # Relevance to domain
            if domain:
                domain_base = domain.split('.')[0]
                if domain_base in kw_lower:
                    score += 8
            
            # Contains year
            if year_founded and year_founded in keyword:
                score += 7
            elif year_founded and year_founded[-2:] in keyword:
                score += 3
            
            # Presence of security-related terms
            security_terms = ['admin', 'root', 'password', 'secret', 'key', 'token', 'auth', 'jwt']
            for term in security_terms:
                if term in kw_lower:
                    score += 4
            
            # Length factor (prefer medium length)
            length = len(keyword)
            if 8 <= length <= 16:
                score += 3
            elif 5 <= length <= 20:
                score += 1
            elif length > 30:
                score -= 2
            
            # Common patterns boost
            if any(sep in keyword for sep in ['123', 'admin', 'pass']):
                score += 2
            
            scored_keywords.append((keyword, score))
        
        # Sort by score (highest first)
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the keywords
        return [kw for kw, score in scored_keywords]
    
    def infer_jwts(self) -> List[Dict[str, Any]]:
        """
        Infer potential JWT structures based on OSINT data.
        
        Returns:
            List of potential JWT structures
        """
        jwt_structures = []
        
        if not self.collected_data:
            logger.warning("No OSINT data available for JWT inference")
            return jwt_structures
        
        # Extract key information
        company_name = self.collected_data.get('company_name', '')
        domain = self.collected_data.get('domain', '')
        products = self.collected_data.get('products', [])
        if isinstance(products, str):
            products = [products]
        
        # Generate common JWT issuers
        issuers = []
        if domain:
            issuers.extend([
                f"https://{domain}",
                f"https://api.{domain}",
                f"https://auth.{domain}",
                domain
            ])
        
        if company_name:
            issuers.append(company_name)
        
        # Generate common subject patterns
        subjects = []
        if 'user_format' in self.collected_data:
            subjects.append(self.collected_data['user_format'])
        else:
            subjects.extend([
                "{user_id}",
                "{username}",
                "user:{user_id}",
                "{email}"
            ])
        
        # Generate audience patterns
        audiences = []
        if domain:
            audiences.extend([
                f"https://{domain}",
                f"https://app.{domain}",
                f"https://api.{domain}"
            ])
        
        for product in products:
            audiences.append(product)
        
        # Generate common JWT structures
        for issuer in issuers:
            for subject in subjects:
                structure = {
                    'header': {
                        'alg': 'HS256',
                        'typ': 'JWT'
                    },
                    'payload': {
                        'iss': issuer,
                        'sub': subject,
                        'exp': 'timestamp + 3600',
                        'iat': 'timestamp'
                    },
                    'keywords': []
                }
                
                # Add audience if available
                if audiences:
                    structure['payload']['aud'] = audiences[0]
                
                # Add potential secret keywords
                keywords = self.generate_keywords(20)
                structure['keywords'] = keywords[:10]
                
                jwt_structures.append(structure)
        
        # Generate structures with kid header parameter
        for issuer in issuers[:1]:  # Just use the first issuer for kid examples
            structure = {
                'header': {
                    'alg': 'HS256',
                    'typ': 'JWT',
                    'kid': '1'  # Vulnerable to path traversal
                },
                'payload': {
                    'iss': issuer,
                    'sub': subjects[0],
                    'exp': 'timestamp + 3600',
                    'iat': 'timestamp'
                },
                'keywords': [],
                'notes': 'Contains kid header parameter which might be vulnerable to path traversal or SQL injection'
            }
            
            # Add potential secret keywords
            keywords = self.generate_keywords(20)
            structure['keywords'] = keywords[:10]
            
            jwt_structures.append(structure)
        
        logger.info("Inferred %d potential JWT structures", len(jwt_structures))
        return jwt_structures
    
    def infer_attack_vectors(self) -> Dict[str, Any]:
        """
        Infer potential attack vectors based on OSINT data.
        
        Returns:
            Dictionary with inferred attack vectors
        """
        attack_vectors = {
            'jwt_secrets': [],
            'jwt_structures': [],
            'api_endpoints': [],
            'parameters': {},
            'user_formats': []
        }
        
        # Generate JWT secrets
        keywords = self.generate_keywords(50)
        prioritized = self.prioritize_keywords(keywords)
        attack_vectors['jwt_secrets'] = prioritized[:30]  # Top 30 most likely secrets
        
        # Generate JWT structures
        attack_vectors['jwt_structures'] = self.infer_jwts()
        
        # Infer API endpoints
        if 'domain' in self.collected_data:
            domain = self.collected_data['domain']
            attack_vectors['api_endpoints'] = [
                f"https://api.{domain}/auth",
                f"https://api.{domain}/login",
                f"https://api.{domain}/token",
                f"https://api.{domain}/users",
                f"https://api.{domain}/v1/auth",
                f"https://{domain}/api/auth",
                f"https://{domain}/api/login",
                f"https://{domain}/api/token"
            ]
        
        # Infer user formats
        if 'email_format' in self.collected_data:
            email_format = self.collected_data['email_format']
            username = email_format.split('@')[0]
            attack_vectors['user_formats'].append(username)
        else:
            attack_vectors['user_formats'] = [
                'admin',
                'administrator',
                'root',
                'user',
                'test',
                'demo'
            ]
        
        # Add company-specific user formats
        if 'company_name' in self.collected_data:
            company = self.collected_data['company_name'].lower()
            company_words = self._extract_words(company)
            for word in company_words:
                attack_vectors['user_formats'].append(f"admin_{word}")
                attack_vectors['user_formats'].append(word)
        
        # Infer parameters
        attack_vectors['parameters'] = {
            'jwt': ['token', 'jwt', 'access_token', 'id_token', 'Authorization'],
            'auth': ['username', 'email', 'password', 'pass', 'key', 'apikey', 'api_key'],
            'user': ['user_id', 'uid', 'id', 'user', 'username', 'email']
        }
        
        logger.info("Inferred attack vectors from OSINT data")
        return attack_vectors
    
    def save_keywords(self, filename: str, keywords: Optional[List[str]] = None) -> bool:
        """
        Save generated keywords to a file.
        
        Args:
            filename: Path to save the wordlist
            keywords: Optional list of keywords to save (uses inferred keywords if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if keywords is None:
                if not self.inferred_keywords:
                    self.generate_keywords()
                keywords = list(self.inferred_keywords)
            
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filename, 'w') as f:
                for keyword in keywords:
                    f.write(f"{keyword}\n")
            
            logger.info("Saved %d keywords to %s", len(keywords), filename)
            return True
        except Exception as e:
            logger.error("Error saving keywords to %s: %s", filename, str(e))
            return False


if __name__ == "__main__":
    # Example usage
    osint_inferrer = OSINTInfer()
    
    # Set sample OSINT data
    sample_data = {
        'company_name': 'Acme Corporation',
        'domain': 'acme.com',
        'products': ['Rocket', 'Anvil', 'Magnet'],
        'technologies': ['Python', 'JavaScript', 'AWS'],
        'founders': ['John Smith', 'Jane Doe'],
        'year_founded': 2015,
        'industry': 'Manufacturing',
        'motto': 'Innovation for everyone',
        'email_format': 'firstname.lastname@acme.com'
    }
    
    osint_inferrer.set_osint_data(sample_data)
    
    # Generate and display keywords
    keywords = osint_inferrer.generate_keywords(50)
    print(f"Generated {len(keywords)} keywords")
    print("Top 10 keywords:", keywords[:10])
    
    # Prioritize keywords
    prioritized = osint_inferrer.prioritize_keywords(keywords)
    print("\nTop 10 prioritized keywords:", prioritized[:10])
    
    # Infer JWT structures
    jwt_structures = osint_inferrer.infer_jwts()
    print(f"\nInferred {len(jwt_structures)} JWT structures")
    print("Example JWT structure:", json.dumps(jwt_structures[0], indent=2))
    
    # Infer attack vectors
    attack_vectors = osint_inferrer.infer_attack_vectors()
    print("\nInferred attack vectors:")
    print(f"- JWT secrets: {len(attack_vectors['jwt_secrets'])}")
    print(f"- JWT structures: {len(attack_vectors['jwt_structures'])}")
    print(f"- API endpoints: {len(attack_vectors['api_endpoints'])}")
    print(f"- User formats: {len(attack_vectors['user_formats'])}")
    
    # Save keywords to file
    osint_inferrer.save_keywords('output/osint_keywords.txt', prioritized) 