import requests
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class OSINTScraper:
    """OSINT data collection and analysis tool."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EVIL_JWT_FORCE/1.0",
            "Accept": "application/json"
        })
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def search_domain(self, domain: str) -> Dict[str, Any]:
        """Search for information about a domain."""
        try:
            # Use multiple OSINT sources
            results = {
                "domain": domain,
                "ip_addresses": [],
                "subdomains": [],
                "emails": [],
                "technologies": [],
                "metadata": {}
            }
            
            # Add basic domain info
            try:
                response = self.session.get(f"https://dns.google/resolve?name={domain}")
                if response.status_code == 200:
                    data = response.json()
                    if "Answer" in data:
                        for answer in data["Answer"]:
                            if answer["type"] == 1:  # A record
                                results["ip_addresses"].append(answer["data"])
            except Exception as e:
                logger.error(f"Error getting DNS info: {e}")
            
            # Add subdomain enumeration
            try:
                response = self.session.get(f"https://crt.sh/?q={domain}&output=json")
                if response.status_code == 200:
                    data = response.json()
                    for entry in data:
                        if "name_value" in entry:
                            results["subdomains"].append(entry["name_value"])
            except Exception as e:
                logger.error(f"Error getting subdomains: {e}")
            
            # Remove duplicates
            results["subdomains"] = list(set(results["subdomains"]))
            results["ip_addresses"] = list(set(results["ip_addresses"]))
            
            return results
            
        except Exception as e:
            logger.error(f"OSINT search failed: {e}")
            return {"error": str(e)}
    
    def search_email(self, email: str) -> Dict[str, Any]:
        """Search for information about an email address."""
        try:
            results = {
                "email": email,
                "breaches": [],
                "pastes": [],
                "metadata": {}
            }
            
            # Check for breaches
            if self.api_key:
                try:
                    response = self.session.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}")
                    if response.status_code == 200:
                        results["breaches"] = response.json()
                except Exception as e:
                    logger.error(f"Error checking breaches: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Email search failed: {e}")
            return {"error": str(e)}
    
    def search_ip(self, ip: str) -> Dict[str, Any]:
        """Search for information about an IP address."""
        try:
            results = {
                "ip": ip,
                "location": {},
                "asn": {},
                "reputation": {},
                "metadata": {}
            }
            
            # Get IP info
            try:
                response = self.session.get(f"https://ipapi.co/{ip}/json/")
                if response.status_code == 200:
                    data = response.json()
                    results["location"] = {
                        "country": data.get("country_name"),
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude")
                    }
                    results["asn"] = {
                        "asn": data.get("asn"),
                        "organization": data.get("org")
                    }
            except Exception as e:
                logger.error(f"Error getting IP info: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"IP search failed: {e}")
            return {"error": str(e)}