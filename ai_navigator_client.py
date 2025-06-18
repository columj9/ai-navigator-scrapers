"""
AI Navigator API Client with JWT Authentication
Handles authentication, token refresh, and API calls to the AI Navigator backend.
"""

import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

class AINavigatorClient:
    def __init__(self, base_url: str = "https://ai-nav.onrender.com/api"):
        self.base_url = base_url.rstrip('/')
        self.admin_email = "columj9+admin@gmail.com"
        self.admin_password = "testtest"
        self.access_token = None
        self.token_expiry = None
        self.logger = logging.getLogger(__name__)
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with current access token"""
        if not self._is_token_valid():
            self._refresh_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Add 5 minute buffer before expiry
        return datetime.now() < (self.token_expiry - timedelta(minutes=5))
    
    def _refresh_token(self) -> bool:
        """Login and refresh the JWT token"""
        try:
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password
            }
            
            response = requests.post(
                f"{self.base_url.replace('/api', '')}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                # Assume token expires in 1 hour if not specified
                expires_in = data.get('expires_in', 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully refreshed AI Navigator API token")
                return True
            else:
                self.logger.error(f"Failed to login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error refreshing token: {str(e)}")
            return False
    
    def create_entity(self, entity_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new entity via POST /entities"""
        try:
            response = requests.post(
                f"{self.base_url}/entities",
                json=entity_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Successfully created entity: {entity_data.get('name', 'Unknown')}")
                return response.json()
            else:
                self.logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
                self.logger.error(f"Entity data: {json.dumps(entity_data, indent=2)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return None
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        try:
            response = requests.get(
                f"{self.base_url}/categories",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get categories: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        try:
            response = requests.get(
                f"{self.base_url}/tags",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get tags: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting tags: {str(e)}")
            return []
    
    def get_features(self) -> List[Dict[str, Any]]:
        """Get all features"""
        try:
            response = requests.get(
                f"{self.base_url}/features",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get features: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting features: {str(e)}")
            return []
    
    def check_entity_exists(self, website_url: str) -> Optional[Dict[str, Any]]:
        """Check if entity with given website URL already exists"""
        try:
            # Note: This assumes there's a search/filter endpoint
            # You may need to adjust based on actual API structure
            response = requests.get(
                f"{self.base_url}/entities",
                params={"website_url": website_url},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                entities = response.json()
                if isinstance(entities, list) and entities:
                    return entities[0]  # Return first match
                elif isinstance(entities, dict) and entities.get('data'):
                    data = entities['data']
                    return data[0] if data else None
            
            return None
                
        except Exception as e:
            self.logger.error(f"Error checking entity existence: {str(e)}")
            return None