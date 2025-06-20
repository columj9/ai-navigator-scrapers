"""
Comprehensive Data Enhancement System
Extracts maximum possible information for the world's best AI tool directory
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
import time
from bs4 import BeautifulSoup
import json

class ComprehensiveDataEnhancer:
    def __init__(self, perplexity_api_key: str):
        self.api_key = perplexity_api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })
    
    def clean_url(self, url: str) -> str:
        """
        Clean URLs by removing tracking parameters and affiliate codes
        Ensures professional, clean links for the database
        """
        if not url:
            return url
        
        try:
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            tracking_params = {
                'ref', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'source', 'campaign', 'medium', 'referrer', 'affiliate', 'partner',
                'fbclid', 'gclid', 'msclkid', 'twclid', '_ga', '_gl', 'mc_eid',
                'futuretools', 'producthunt', 'betalist', 'indiehackers'
            }
            
            if parsed.query:
                query_params = parse_qs(parsed.query, keep_blank_values=False)
                
                # Keep only essential parameters (not tracking)
                clean_params = {}
                for key, values in query_params.items():
                    key_lower = key.lower()
                    
                    # Skip tracking parameters
                    if key_lower in tracking_params:
                        continue
                    
                    # Skip parameters that look like tracking
                    if any(track in key_lower for track in ['utm_', 'ref', 'source', 'campaign']):
                        continue
                    
                    # Keep essential parameters (like product IDs, page numbers, etc.)
                    clean_params[key] = values
                
                # Rebuild clean query string
                clean_query = urlencode(clean_params, doseq=True) if clean_params else ''
                
                # Reconstruct clean URL
                clean_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc, 
                    parsed.path,
                    parsed.params,
                    clean_query,
                    ''  # Remove fragment
                ))
                
                # Remove trailing slashes for consistency
                if clean_url.endswith('/') and len(clean_url) > 8:  # Keep https://
                    clean_url = clean_url.rstrip('/')
                
                self.logger.info(f"Cleaned URL: {url} → {clean_url}")
                return clean_url
            
            return url.rstrip('/')
            
        except Exception as e:
            self.logger.warning(f"Error cleaning URL {url}: {str(e)}")
            return url
    
    def extract_comprehensive_data(self, tool_name: str, website_url: str, basic_description: str = "") -> Dict[str, Any]:
        """
        Extract the most comprehensive data possible for world-class AI tool directory
        """
        clean_website_url = self.clean_url(website_url)
        
        # Multi-stage comprehensive data extraction
        comprehensive_data = {}
        
        # Stage 1: Core Tool Information (Enhanced)
        core_data = self._extract_core_enhanced_data(tool_name, clean_website_url, basic_description)
        comprehensive_data.update(core_data)
        
        # Stage 2: Market Intelligence & Competitive Analysis
        market_data = self._extract_market_intelligence(tool_name, clean_website_url)
        comprehensive_data.update(market_data)
        
        # Stage 3: Technical Deep Dive
        technical_data = self._extract_technical_details(tool_name, clean_website_url)
        comprehensive_data.update(technical_data)
        
        # Stage 4: User Experience & Community Data
        community_data = self._extract_community_metrics(tool_name, clean_website_url)
        comprehensive_data.update(community_data)
        
        # Stage 5: Business Intelligence
        business_data = self._extract_business_intelligence(tool_name, clean_website_url)
        comprehensive_data.update(business_data)
        
        # Stage 6: Quality & Trust Indicators
        quality_data = self._extract_quality_indicators(tool_name, clean_website_url)
        comprehensive_data.update(quality_data)
        
        return comprehensive_data
    
    def _extract_core_enhanced_data(self, tool_name: str, website_url: str, basic_description: str) -> Dict[str, Any]:
        """Extract enhanced core information with maximum detail"""
        
        prompt = f"""
        Provide comprehensive core information about "{tool_name}" (website: {website_url}) in JSON format.
        Research thoroughly and provide maximum detail:
        
        {{
            "short_description": "Compelling 1-2 sentence value proposition that sells the tool",
            "description": "Detailed 6-8 sentence description covering functionality, unique benefits, target users, and competitive advantages",
            "detailed_description": "Comprehensive 3-4 paragraph description covering all aspects of the tool",
            "key_features": ["specific feature 1", "specific feature 2", "specific feature 3", "specific feature 4", "specific feature 5", "specific feature 6"],
            "advanced_features": ["advanced feature 1", "advanced feature 2", "advanced feature 3"],
            "unique_selling_points": ["unique advantage 1", "unique advantage 2", "unique advantage 3"],
            "use_cases": ["specific use case 1", "specific use case 2", "specific use case 3", "specific use case 4", "specific use case 5"],
            "detailed_use_cases": [
                {{"title": "Use Case 1", "description": "Detailed description", "benefits": ["benefit1", "benefit2"]}},
                {{"title": "Use Case 2", "description": "Detailed description", "benefits": ["benefit1", "benefit2"]}}
            ],
            "target_audience": ["primary audience 1", "primary audience 2", "secondary audience 1", "secondary audience 2"],
            "audience_segments": {{
                "primary": ["main user type 1", "main user type 2"],
                "secondary": ["secondary user type 1", "secondary user type 2"],
                "company_sizes": ["startups", "small business", "enterprise"]
            }},
            "categories": ["primary category", "secondary category"],
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
            "industry_verticals": ["healthcare", "finance", "marketing", "education"],
            "problem_solved": "What main problem does this tool solve?",
            "value_proposition": "What unique value does it provide?",
            "competitive_advantages": ["advantage 1", "advantage 2", "advantage 3"]
        }}
        
        Be extremely detailed and comprehensive. Include everything valuable for users choosing AI tools.
        """
        
        return self._call_perplexity_structured(prompt, "core_data")
    
    def _extract_market_intelligence(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Extract market positioning and competitive intelligence"""
        
        prompt = f"""
        Provide comprehensive market intelligence for "{tool_name}" (website: {website_url}):
        
        {{
            "market_position": "leader|challenger|niche|emerging",
            "market_segment": "specific market segment description",
            "competitor_analysis": {{
                "main_competitors": ["competitor 1", "competitor 2", "competitor 3"],
                "competitive_advantages": ["advantage over competitor 1", "advantage over competitor 2"],
                "differentiators": ["key differentiator 1", "key differentiator 2"]
            }},
            "alternative_tools": ["alternative 1", "alternative 2", "alternative 3", "alternative 4"],
            "comparison_points": ["comparison factor 1", "comparison factor 2", "comparison factor 3"],
            "market_trends": ["relevant trend 1", "relevant trend 2"],
            "growth_indicators": ["growth signal 1", "growth signal 2"],
            "user_adoption": "early|growing|mature|declining",
            "market_size": "TAM/market size information if available",
            "geographical_presence": ["region 1", "region 2", "region 3"]
        }}
        """
        
        return self._call_perplexity_structured(prompt, "market_intelligence")
    
    def _extract_technical_details(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Extract comprehensive technical information"""
        
        prompt = f"""
        Provide detailed technical information for "{tool_name}" (website: {website_url}):
        
        {{
            "technical_specs": {{
                "deployment_options": ["cloud", "on-premise", "hybrid", "edge"],
                "platform_compatibility": ["web", "windows", "mac", "linux", "ios", "android"],
                "supported_languages": ["english", "spanish", "french", "german", "chinese"],
                "programming_languages": ["python", "javascript", "java"],
                "frameworks_used": ["react", "tensorflow", "pytorch"],
                "databases_supported": ["postgresql", "mongodb", "mysql"],
                "cloud_providers": ["aws", "gcp", "azure"],
                "api_specifications": {{
                    "rest_api": true/false,
                    "graphql": true/false,
                    "webhooks": true/false,
                    "rate_limits": "rate limit information",
                    "authentication": ["oauth2", "api_key", "jwt"]
                }}
            }},
            "integration_ecosystem": {{
                "native_integrations": ["integration 1", "integration 2", "integration 3", "integration 4"],
                "zapier_integrations": true/false,
                "webhook_support": true/false,
                "api_ecosystem": ["ecosystem 1", "ecosystem 2"],
                "third_party_connectors": ["connector 1", "connector 2"]
            }},
            "performance_metrics": {{
                "response_time": "typical response time",
                "uptime_sla": "uptime guarantee",
                "scalability": "scalability information",
                "processing_capacity": "capacity limits"
            }},
            "data_handling": {{
                "data_privacy": "privacy policy summary",
                "data_retention": "data retention policy", 
                "data_portability": "export capabilities",
                "gdpr_compliance": true/false,
                "hipaa_compliance": true/false,
                "soc2_compliance": true/false
            }}
        }}
        """
        
        return self._call_perplexity_structured(prompt, "technical_details")
    
    def _extract_community_metrics(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Extract user community and social proof data"""
        
        prompt = f"""
        Provide comprehensive community and user data for "{tool_name}" (website: {website_url}):
        
        {{
            "user_metrics": {{
                "user_count": "estimated number of users",
                "growth_rate": "user growth information",
                "user_satisfaction": "satisfaction metrics",
                "retention_rate": "user retention information"
            }},
            "social_proof": {{
                "customer_testimonials": [
                    {{"quote": "testimonial text", "author": "author name", "company": "company name"}},
                    {{"quote": "testimonial text", "author": "author name", "company": "company name"}}
                ],
                "case_studies": ["case study 1", "case study 2"],
                "awards_recognition": ["award 1", "award 2"],
                "media_coverage": ["publication 1", "publication 2"],
                "industry_endorsements": ["endorsement 1", "endorsement 2"]
            }},
            "community_engagement": {{
                "community_size": "size of user community",
                "community_platforms": ["discord", "slack", "reddit", "forum"],
                "documentation_quality": "poor|fair|good|excellent",
                "tutorial_availability": ["video tutorials", "written guides", "interactive demos"],
                "community_support": "level of community support",
                "developer_activity": "frequency of updates and engagement"
            }},
            "review_aggregation": {{
                "overall_rating": "4.5/5",
                "review_count": "number of reviews",
                "review_sources": ["g2", "capterra", "trustpilot", "product hunt"],
                "sentiment_analysis": "positive|mixed|negative",
                "common_praise": ["praise point 1", "praise point 2"],
                "common_criticisms": ["criticism 1", "criticism 2"]
            }}
        }}
        """
        
        return self._call_perplexity_structured(prompt, "community_metrics")
    
    def _extract_business_intelligence(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Extract comprehensive business and financial intelligence"""
        
        prompt = f"""
        Provide detailed business intelligence for "{tool_name}" (website: {website_url}):
        
        {{
            "business_model": {{
                "revenue_model": "saas|marketplace|transaction|advertising|freemium",
                "monetization_strategy": "how the company makes money",
                "pricing_strategy": "pricing approach and philosophy"
            }},
            "financial_data": {{
                "funding_history": [
                    {{"round": "Series A", "amount": "$5M", "date": "2023", "investors": ["investor 1", "investor 2"]}},
                    {{"round": "Seed", "amount": "$1M", "date": "2022", "investors": ["investor 1"]}}
                ],
                "total_funding": "total amount raised",
                "valuation": "last known valuation",
                "revenue_estimates": "estimated revenue range",
                "profitability": "profitable|break-even|burning"
            }},
            "company_intelligence": {{
                "founded_year": 2023,
                "headquarters": "City, Country",
                "employee_count": "1-10|11-50|51-200|201-500|501-1000|1001-5000|5000+",
                "key_personnel": [
                    {{"name": "CEO Name", "role": "CEO", "background": "brief background"}},
                    {{"name": "CTO Name", "role": "CTO", "background": "brief background"}}
                ],
                "advisory_board": ["advisor 1", "advisor 2"],
                "company_culture": "culture description",
                "hiring_trends": "hiring|stable|downsizing"
            }},
            "partnerships": {{
                "strategic_partners": ["partner 1", "partner 2"],
                "technology_partners": ["tech partner 1", "tech partner 2"],
                "channel_partners": ["channel partner 1", "channel partner 2"],
                "investor_connections": ["connected company 1", "connected company 2"]
            }}
        }}
        """
        
        return self._call_perplexity_structured(prompt, "business_intelligence")
    
    def _extract_quality_indicators(self, tool_name: str, website_url: str) -> Dict[str, Any]:
        """Extract quality, trust, and reliability indicators"""
        
        prompt = f"""
        Provide comprehensive quality and trust indicators for "{tool_name}" (website: {website_url}):
        
        {{
            "quality_metrics": {{
                "product_maturity": "beta|stable|mature|enterprise",
                "update_frequency": "daily|weekly|monthly|quarterly",
                "feature_velocity": "how quickly new features are added",
                "bug_fix_responsiveness": "how quickly bugs are fixed",
                "backward_compatibility": "approach to maintaining compatibility"
            }},
            "trust_indicators": {{
                "security_measures": ["encryption", "2fa", "sso", "penetration testing"],
                "compliance_certifications": ["soc2", "gdpr", "hipaa", "iso27001"],
                "transparency_score": "high|medium|low",
                "privacy_practices": "privacy policy summary",
                "data_governance": "data handling practices"
            }},
            "support_quality": {{
                "support_channels": ["email", "chat", "phone", "community"],
                "response_times": {{
                    "email": "24 hours",
                    "chat": "5 minutes",
                    "phone": "immediate"
                }},
                "support_quality_rating": "excellent|good|fair|poor",
                "documentation_comprehensiveness": "excellent|good|fair|poor",
                "onboarding_experience": "smooth|moderate|difficult"
            }},
            "reliability_metrics": {{
                "uptime_track_record": "99.9%",
                "performance_consistency": "consistent|variable",
                "error_handling": "graceful|basic|poor",
                "monitoring_transparency": "public status page availability",
                "incident_communication": "how incidents are communicated"
            }},
            "learning_resources": {{
                "documentation_types": ["api docs", "user guides", "video tutorials"],
                "certification_programs": true/false,
                "training_availability": ["self-paced", "instructor-led", "community"],
                "best_practices_guides": true/false,
                "example_implementations": true/false
            }}
        }}
        """
        
        return self._call_perplexity_structured(prompt, "quality_indicators")
    
    def _call_perplexity_structured(self, prompt: str, data_type: str) -> Dict[str, Any]:
        """Make structured API call to Perplexity with enhanced prompting"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            enhanced_prompt = f"""
            {prompt}
            
            IMPORTANT INSTRUCTIONS:
            1. Research the tool thoroughly using all available sources
            2. Provide ONLY verified, factual information
            3. Use "unknown" or null for unverifiable data
            4. Be comprehensive but accurate
            5. Return valid JSON format only
            6. Include as much detail as possible for building the world's best AI tool directory
            """
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a comprehensive AI tool research assistant for building the world's best AI tool directory. Provide maximum detail with verified accuracy."
                    },
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1,  # Lower temperature for factual accuracy
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60  # Longer timeout for comprehensive research
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                    self.logger.info(f"Successfully extracted {data_type} with {len(parsed_data)} fields")
                    return parsed_data
                else:
                    self.logger.warning(f"Could not extract JSON from {data_type} response")
                    return {}
            else:
                self.logger.error(f"Perplexity API error for {data_type}: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error extracting {data_type}: {str(e)}")
            return {}
    
    def extract_website_intelligence(self, website_url: str) -> Dict[str, Any]:
        """Extract additional intelligence directly from the website"""
        
        try:
            response = self.session.get(website_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            intelligence = {}
            
            # Extract meta tags for additional insights
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', '').lower()
                property_attr = tag.get('property', '').lower()
                content = tag.get('content', '')
                
                if content:
                    if 'keywords' in name:
                        intelligence['meta_keywords'] = content.split(',')
                    elif 'author' in name:
                        intelligence['meta_author'] = content
                    elif 'og:title' in property_attr:
                        intelligence['og_title'] = content
                    elif 'og:description' in property_attr:
                        intelligence['og_description'] = content
                    elif 'twitter:site' in name:
                        intelligence['twitter_handle'] = content
            
            # Look for structured data (JSON-LD)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            if json_ld_scripts:
                try:
                    structured_data = json.loads(json_ld_scripts[0].get_text())
                    intelligence['structured_data'] = structured_data
                except:
                    pass
            
            # Extract additional social links
            social_patterns = {
                'twitter': r'twitter\.com/([^/\s"\']+)',
                'linkedin': r'linkedin\.com/company/([^/\s"\']+)',
                'github': r'github\.com/([^/\s"\']+)',
                'youtube': r'youtube\.com/([^/\s"\']+)',
                'facebook': r'facebook\.com/([^/\s"\']+)'
            }
            
            page_text = str(soup)
            social_links = {}
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    social_links[platform] = matches[0]
            
            if social_links:
                intelligence['social_links'] = social_links
            
            return intelligence
            
        except Exception as e:
            self.logger.warning(f"Error extracting website intelligence from {website_url}: {str(e)}")
            return {}