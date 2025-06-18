"""
Data Enrichment Service using Perplexity API
Enhances basic scraped data with additional information about AI tools.
"""

import requests
import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import json

class DataEnrichmentService:
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.logger = logging.getLogger(__name__)
        
    def _call_perplexity(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make a call to Perplexity API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate, factual information about AI tools and software. Always provide specific, actionable details when available."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                self.logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling Perplexity API: {str(e)}")
            return None
    
    def enrich_tool_data(self, tool_name: str, website_url: str, basic_description: str = "") -> Dict[str, Any]:
        """Enrich basic tool information with detailed data"""
        
        # Create a comprehensive prompt for data enrichment
        prompt = f"""
        Please provide detailed information about the AI tool "{tool_name}" (website: {website_url}).
        
        Provide the following information in JSON format:
        {{
            "short_description": "Brief 1-2 sentence description",
            "description": "Detailed description (3-5 sentences)",
            "key_features": ["feature1", "feature2", "feature3"],
            "use_cases": ["use case 1", "use case 2", "use case 3"],
            "pricing_model": "FREE|FREEMIUM|PAID|SUBSCRIPTION",
            "price_range": "FREE|LOW|MEDIUM|HIGH",
            "pricing_details": "Specific pricing information if available",
            "target_audience": ["audience1", "audience2"],
            "categories": ["category1", "category2"],
            "tags": ["tag1", "tag2", "tag3"],
            "has_free_tier": true/false,
            "api_access": true/false,
            "mobile_support": true/false,
            "integrations": ["integration1", "integration2"],
            "founded_year": 2023,
            "employee_count_range": "1-10|11-50|51-200|201-500|500+",
            "funding_stage": "Pre-seed|Seed|Series A|Series B|Series C|Public|Unknown"
        }}
        
        Only include information you can verify or that is commonly known. Use "Unknown" or null for uncertain information.
        """
        
        response = self._call_perplexity(prompt, max_tokens=1500)
        
        if response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    enriched_data = json.loads(json_match.group())
                    self.logger.info(f"Successfully enriched data for {tool_name}")
                    return enriched_data
                else:
                    self.logger.warning(f"Could not extract JSON from Perplexity response for {tool_name}")
                    return self._fallback_enrichment(tool_name, website_url, basic_description)
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response for {tool_name}: {str(e)}")
                return self._fallback_enrichment(tool_name, website_url, basic_description)
        
        return self._fallback_enrichment(tool_name, website_url, basic_description)
    
    def _fallback_enrichment(self, tool_name: str, website_url: str, basic_description: str) -> Dict[str, Any]:
        """Provide basic fallback data when API enrichment fails"""
        domain = urlparse(website_url).netloc.lower()
        
        # Basic categorization based on tool name patterns
        categories = []
        tags = []
        
        name_lower = tool_name.lower()
        if any(word in name_lower for word in ['chat', 'gpt', 'ai']):
            categories.append('AI Assistant')
            tags.extend(['AI', 'Assistant'])
        
        if any(word in name_lower for word in ['write', 'content', 'copy']):
            categories.append('Content Creation')
            tags.extend(['Writing', 'Content'])
            
        if any(word in name_lower for word in ['image', 'photo', 'visual']):
            categories.append('Image Generation')
            tags.extend(['Image', 'Visual'])
        
        return {
            "short_description": basic_description or f"AI tool for enhanced productivity and automation",
            "description": basic_description or f"{tool_name} is an AI-powered tool designed to improve workflow efficiency and productivity.",
            "key_features": ["AI-powered", "User-friendly interface", "Productivity enhancement"],
            "use_cases": ["Business automation", "Personal productivity", "Creative tasks"],
            "pricing_model": "FREEMIUM",
            "price_range": "MEDIUM",
            "pricing_details": "Visit website for current pricing",
            "target_audience": ["Professionals", "Businesses"],
            "categories": categories if categories else ["AI Tools"],
            "tags": tags if tags else ["AI", "Productivity"],
            "has_free_tier": True,
            "api_access": False,
            "mobile_support": False,
            "integrations": [],
            "founded_year": None,
            "employee_count_range": "Unknown",
            "funding_stage": "Unknown"
        }
    
    def get_company_info(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Get company-specific information"""
        prompt = f"""
        Provide company information for "{tool_name}" (website: {website_url}) in JSON format:
        {{
            "founded_year": 2023,
            "employee_count_range": "1-10|11-50|51-200|201-500|500+",
            "funding_stage": "Pre-seed|Seed|Series A|Series B|Series C|Public|Unknown",
            "location_summary": "City, Country or Remote",
            "social_links": {{
                "twitter": "handle_without_@",
                "linkedin": "company/profile-name"
            }}
        }}
        
        Only include verified information. Use null for unknown fields.
        """
        
        response = self._call_perplexity(prompt, max_tokens=500)
        
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {
            "founded_year": None,
            "employee_count_range": "Unknown", 
            "funding_stage": "Unknown",
            "location_summary": "Unknown",
            "social_links": {}
        }