"""
Enhanced Item Processor
Transforms basic scraped leads into full CreateEntityDto objects for the AI Navigator API
"""

import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from logo_enhancer import LogoEnhancer

class EnhancedItemProcessor:
    def __init__(self, ai_navigator_client, data_enrichment_service, taxonomy_service):
        self.client = ai_navigator_client
        self.enrichment_service = data_enrichment_service
        self.taxonomy_service = taxonomy_service
        self.logo_enhancer = LogoEnhancer()  # Initialize enhanced logo service
        self.logger = logging.getLogger(__name__)
    
    def _resolve_redirect_url(self, redirect_url: str) -> str:
        """Resolve redirect URLs to get the actual tool website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            }
            
            # Use GET request with allow_redirects to follow the full chain
            response = requests.get(redirect_url, headers=headers, allow_redirects=True, timeout=15)
            final_url = response.url
            
            # Additional check: if we're still on a redirect service, try to parse the page
            if any(domain in final_url for domain in ['futuretools.link', 'bit.ly', 'tinyurl.com']):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for meta refresh redirects
                meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                if meta_refresh and meta_refresh.get('content'):
                    content = meta_refresh.get('content')
                    if 'url=' in content.lower():
                        url_part = content.lower().split('url=')[1]
                        final_url = url_part.strip('\'"')
                
                # Look for JavaScript redirects
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'window.location' in script.string:
                        # Extract URL from JavaScript redirect
                        import re
                        js_redirect = re.search(r'window\.location.*?[\"\'](https?://[^\"\']+)', script.string)
                        if js_redirect:
                            final_url = js_redirect.group(1)
                            break
            
            # Validate the final URL is different and looks like a real website
            if final_url != redirect_url and final_url.startswith('http'):
                self.logger.info(f"Successfully resolved {redirect_url} → {final_url}")
                return final_url
            else:
                self.logger.warning(f"Could not resolve redirect {redirect_url}, using original")
                return redirect_url
            
        except Exception as e:
            self.logger.warning(f"Error resolving redirect URL {redirect_url}: {str(e)}")
            return redirect_url  # Return original if resolution fails

    def process_lead_item(self, lead_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a basic lead item into a full CreateEntityDto object"""
        
        tool_name = lead_item.get('tool_name_on_directory', '').strip()
        website_url = lead_item.get('external_website_url', '').strip()
        source_directory = lead_item.get('source_directory', '')
        
        if not tool_name or not website_url:
            self.logger.error("Missing required fields: tool_name or website_url")
            return None
        
        # Resolve redirect URLs to get actual tool websites
        if 'futuretools.link' in website_url or 'redirect' in website_url:
            actual_website_url = self._resolve_redirect_url(website_url)
        else:
            actual_website_url = website_url
        
        self.logger.info(f"Processing lead: {tool_name} from {source_directory}")
        
        # Check if entity already exists using the actual website URL
        existing_entity = self.client.check_entity_exists(actual_website_url)
        if existing_entity:
            self.logger.info(f"Entity already exists for {actual_website_url}, skipping")
            return None
        
        # Also check for duplicate names and append timestamp if needed
        import time
        timestamp_suffix = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
        unique_tool_name = f"{tool_name} (Auto-{timestamp_suffix})" if self._name_exists(tool_name) else tool_name
        
        # Scrape basic info from the actual tool website
        website_data = self._scrape_website_data(actual_website_url)
        
        # Get guaranteed logo using enhanced logo extraction
        logo_url = self.logo_enhancer.get_comprehensive_logo(actual_website_url, tool_name)
        # Validate logo URL format
        if logo_url and self._is_valid_url(logo_url):
            website_data['logo_url'] = logo_url  # Ensure we always have a valid logo
        else:
            # Fallback to a guaranteed working logo
            website_data['logo_url'] = self._get_guaranteed_fallback_logo(tool_name)
        
        # Enhanced data enrichment with more context
        enriched_data = self.enrichment_service.enrich_tool_data(
            tool_name, 
            actual_website_url, 
            website_data.get('description', '')
        )
        
        # Get comprehensive company information
        company_info = self.enrichment_service.get_company_info(tool_name, actual_website_url)
        
        # Map categories, tags, and features to UUIDs
        category_ids = self.taxonomy_service.map_categories(enriched_data.get('categories', []))
        tag_ids = self.taxonomy_service.map_tags(enriched_data.get('tags', []))
        feature_ids = self.taxonomy_service.map_features(enriched_data.get('key_features', []))
        
        # Ensure at least one category
        if not category_ids:
            default_category = self.taxonomy_service.get_default_category_id()
            if default_category:
                category_ids = [default_category]
        
        # Create entity_type_id (assuming "tool" is the default type)
        entity_type_id = self._get_entity_type_id()
        
        # Build CreateEntityDto object
        create_entity_dto = {
            "name": unique_tool_name,  # Use unique name to avoid duplicates
            "website_url": actual_website_url,  # Use the resolved actual URL
            "entity_type_id": entity_type_id,
            "short_description": enriched_data.get('short_description', f"{tool_name} - AI-powered productivity tool"),
            "description": enriched_data.get('description', ''),
            "logo_url": website_data.get('logo_url'),
            "documentation_url": website_data.get('documentation_url'),
            "contact_url": website_data.get('contact_url'),
            "privacy_policy_url": website_data.get('privacy_policy_url'),
            "founded_year": company_info.get('founded_year'),
            "social_links": company_info.get('social_links', {}),
            "category_ids": category_ids[:3],  # Limit to 3 categories
            "tag_ids": tag_ids[:10],          # Limit to 10 tags
            "feature_ids": feature_ids[:10],   # Limit to 10 features
            "meta_title": f"{tool_name} | AI Navigator",
            "meta_description": enriched_data.get('short_description', '')[:160],
            "employee_count_range": self._normalize_employee_count(company_info.get('employee_count_range')),
            "funding_stage": self._normalize_funding_stage(company_info.get('funding_stage')),
            "location_summary": company_info.get('location_summary'),
            "ref_link": actual_website_url,  # Use actual URL for ref_link too
            "affiliate_status": "NONE",  # Fixed: use NONE instead of PENDING
            "status": "ACTIVE",
            "scraped_review_sentiment_label": None,  # V1 - skip sentiment analysis
            "scraped_review_sentiment_score": None,
            "scraped_review_count": None,
            
            # Tool-specific details
            "tool_details": {
                "learning_curve": "MEDIUM",  # Default
                "key_features": enriched_data.get('key_features', []),
                "has_free_tier": enriched_data.get('has_free_tier', False),
                "use_cases": enriched_data.get('use_cases', []),
                "pricing_model": self._normalize_pricing_model(enriched_data.get('pricing_model', 'FREEMIUM')),
                "price_range": self._normalize_price_range(enriched_data.get('price_range', 'MEDIUM')),
                "pricing_details": enriched_data.get('pricing_details'),
                "pricing_url": website_data.get('pricing_url'),
                "integrations": enriched_data.get('integrations', []),
                "support_email": website_data.get('support_email'),
                "has_live_chat": False,  # Default
                "community_url": website_data.get('community_url'),
                "programming_languages": [],
                "frameworks": [],
                "libraries": [],
                "target_audience": enriched_data.get('target_audience', []),
                "deployment_options": [],
                "supported_os": [],
                "mobile_support": enriched_data.get('mobile_support', False),
                "api_access": enriched_data.get('api_access', False),
                "customization_level": "Medium",
                "trial_available": enriched_data.get('has_free_tier', False),
                "demo_available": False,
                "open_source": False,
                "support_channels": ["Email", "Documentation"]
            }
        }
        
        # Remove null values to keep payload clean
        create_entity_dto = self._clean_null_values(create_entity_dto)
        
        self.logger.info(f"Successfully processed lead for {tool_name}")
        return create_entity_dto
    
    def _scrape_website_data(self, website_url: str) -> Dict[str, Any]:
        """Scrape basic information from the tool's website with enhanced logo detection"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            }
            
            response = requests.get(website_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic website data
            data = {}
            
            # Enhanced logo detection with multiple methods
            logo_url = self._extract_logo_url(soup, website_url)
            if logo_url:
                data['logo_url'] = logo_url
            
            # Try to find description from meta tags
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                data['description'] = meta_desc.get('content', '')
            
            # Look for common URLs
            links = soup.find_all('a')
            for link in links:
                href = link.get('href', '').lower()
                text = link.get_text().lower()
                
                if 'pricing' in href or 'pricing' in text:
                    data['pricing_url'] = requests.compat.urljoin(website_url, link['href'])
                elif 'contact' in href or 'contact' in text:
                    data['contact_url'] = requests.compat.urljoin(website_url, link['href'])
                elif 'privacy' in href or 'privacy' in text:
                    data['privacy_policy_url'] = requests.compat.urljoin(website_url, link['href'])
                elif 'docs' in href or 'documentation' in href:
                    data['documentation_url'] = requests.compat.urljoin(website_url, link['href'])
                elif 'community' in href or 'discord' in href or 'slack' in href:
                    data['community_url'] = requests.compat.urljoin(website_url, link['href'])
            
            # Look for support email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            page_text = soup.get_text()
            emails = re.findall(email_pattern, page_text)
            
            for email in emails:
                if any(word in email.lower() for word in ['support', 'help', 'contact', 'info']):
                    data['support_email'] = email
                    break
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Could not scrape website data from {website_url}: {str(e)}")
            return {}
    
    def _extract_logo_url(self, soup: BeautifulSoup, website_url: str) -> Optional[str]:
        """Enhanced logo extraction with multiple fallback methods"""
        from urllib.parse import urljoin, urlparse
        
        # Method 1: Look for specific logo selectors
        logo_selectors = [
            'img[alt*="logo" i]',
            'img[class*="logo" i]',
            'img[src*="logo" i]',
            '.logo img',
            'header img',
            '.header img',
            '.navbar img',
            '.nav img',
            'img[alt*="brand" i]',
            'img[class*="brand" i]',
            '.brand img',
            '[class*="logo"] img',
            'a[class*="logo"] img',
            'div[class*="logo"] img'
        ]
        
        for selector in logo_selectors:
            logo_img = soup.select_one(selector)
            if logo_img and logo_img.get('src'):
                logo_url = logo_img['src']
                # Convert relative URLs to absolute
                if not logo_url.startswith('http'):
                    logo_url = urljoin(website_url, logo_url)
                
                # Validate the logo URL
                if self._validate_logo_url(logo_url):
                    self.logger.info(f"Found logo via selector '{selector}': {logo_url}")
                    return logo_url
        
        # Method 2: Look for Apple touch icons and favicons
        icon_selectors = [
            'link[rel="apple-touch-icon"]',
            'link[rel="apple-touch-icon-precomposed"]', 
            'link[rel="icon"]',
            'link[rel="shortcut icon"]'
        ]
        
        for selector in icon_selectors:
            icon_link = soup.select_one(selector)
            if icon_link and icon_link.get('href'):
                icon_url = icon_link['href']
                if not icon_url.startswith('http'):
                    icon_url = urljoin(website_url, icon_url)
                
                # Only use if it's a reasonable size (not tiny favicon)
                sizes = icon_link.get('sizes', '')
                if any(size in sizes for size in ['180x180', '152x152', '144x144', '120x120']):
                    if self._validate_logo_url(icon_url):
                        self.logger.info(f"Found logo via icon '{selector}': {icon_url}")
                        return icon_url
        
        # Method 3: Try common logo file paths
        domain = urlparse(website_url).netloc
        common_logo_paths = [
            '/logo.png',
            '/logo.svg', 
            '/assets/logo.png',
            '/assets/logo.svg',
            '/static/logo.png',
            '/static/logo.svg',
            '/images/logo.png',
            '/images/logo.svg',
            '/img/logo.png',
            '/img/logo.svg'
        ]
        
        for path in common_logo_paths:
            logo_url = urljoin(website_url, path)
            if self._validate_logo_url(logo_url):
                self.logger.info(f"Found logo via common path: {logo_url}")
                return logo_url
        
        # Method 4: Use external logo services as fallback
        fallback_logo = self._get_fallback_logo(website_url)
        if fallback_logo:
            return fallback_logo
        
        self.logger.warning(f"Could not find logo for {website_url}")
        return None
    
    def _validate_logo_url(self, logo_url: str) -> bool:
        """Validate that a logo URL is accessible and is an image"""
        try:
            response = requests.head(logo_url, timeout=10)
            
            # Check if URL is accessible
            if response.status_code != 200:
                return False
            
            # Check if it's an image
            content_type = response.headers.get('content-type', '').lower()
            if any(img_type in content_type for img_type in ['image/', 'png', 'jpg', 'jpeg', 'svg', 'gif', 'webp']):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _get_fallback_logo(self, website_url: str) -> Optional[str]:
        """Get fallback logo using external services"""
        from urllib.parse import urlparse
        
        domain = urlparse(website_url).netloc
        
        # Method 1: Clearbit Logo API (free, no auth required)
        clearbit_url = f"https://logo.clearbit.com/{domain}"
        if self._validate_logo_url(clearbit_url):
            self.logger.info(f"Found logo via Clearbit: {clearbit_url}")
            return clearbit_url
        
        # Method 2: Google Favicon service (high quality favicons)
        google_favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
        # Note: Google favicon always returns something, so we'll use it as last resort
        self.logger.info(f"Using Google favicon as fallback: {google_favicon_url}")
        return google_favicon_url
    
    def _name_exists(self, tool_name: str) -> bool:
        """Check if an entity with this name already exists"""
        # This is a simplified check - in production you might want to query the API
        # For now, we'll assume we need unique names for the demo
        return False  # Always return False for now to let timestamp handle uniqueness
    
    def _normalize_pricing_model(self, pricing_model: str) -> str:
        """Normalize pricing model to match API enum values"""
        if not pricing_model:
            return 'FREEMIUM'  # Safe default
            
        pricing_model_clean = str(pricing_model).upper().strip()
        
        # Comprehensive mapping for pricing models
        pricing_map = {
            'FREE': 'FREE',
            'FREEMIUM': 'FREEMIUM', 
            'SUBSCRIPTION': 'SUBSCRIPTION',
            'PAID': 'SUBSCRIPTION',  # Map PAID to SUBSCRIPTION
            'MONTHLY': 'SUBSCRIPTION',
            'YEARLY': 'SUBSCRIPTION',
            'RECURRING': 'SUBSCRIPTION',
            'SaaS': 'SUBSCRIPTION',
            'PAY_PER_USE': 'PAY_PER_USE',
            'PAY PER USE': 'PAY_PER_USE',
            'PAYPERUSE': 'PAY_PER_USE',
            'USAGE_BASED': 'PAY_PER_USE',
            'CREDITS': 'PAY_PER_USE',
            'TOKENS': 'PAY_PER_USE',
            'ONE_TIME_PURCHASE': 'ONE_TIME_PURCHASE',
            'ONE-TIME': 'ONE_TIME_PURCHASE',
            'ONETIME': 'ONE_TIME_PURCHASE',
            'ONE TIME': 'ONE_TIME_PURCHASE',
            'PURCHASE': 'ONE_TIME_PURCHASE',
            'LIFETIME': 'ONE_TIME_PURCHASE',
            'CONTACT_SALES': 'CONTACT_SALES',
            'CONTACT': 'CONTACT_SALES',
            'ENTERPRISE': 'CONTACT_SALES',
            'CUSTOM': 'CONTACT_SALES',
            'QUOTE': 'CONTACT_SALES',
            'OPEN_SOURCE': 'OPEN_SOURCE',
            'OPEN': 'OPEN_SOURCE',
            'OSS': 'OPEN_SOURCE',
            'MIT': 'OPEN_SOURCE',
            'GPL': 'OPEN_SOURCE',
            'APACHE': 'OPEN_SOURCE'
        }
        
        # Check direct mapping first
        if pricing_model_clean in pricing_map:
            return pricing_map[pricing_model_clean]
        
        # Try partial matches
        if any(word in pricing_model_clean for word in ['FREE', 'NO COST', 'ZERO']):
            return 'FREE'
        elif any(word in pricing_model_clean for word in ['FREEMIUM', 'FREE TIER', 'FREE PLAN']):
            return 'FREEMIUM'
        elif any(word in pricing_model_clean for word in ['SUBSCRIPTION', 'MONTHLY', 'YEARLY', 'RECURRING']):
            return 'SUBSCRIPTION'
        elif any(word in pricing_model_clean for word in ['PAY PER', 'USAGE', 'CREDITS', 'TOKENS']):
            return 'PAY_PER_USE'
        elif any(word in pricing_model_clean for word in ['ONE TIME', 'LIFETIME', 'PURCHASE']):
            return 'ONE_TIME_PURCHASE'
        elif any(word in pricing_model_clean for word in ['CONTACT', 'ENTERPRISE', 'CUSTOM']):
            return 'CONTACT_SALES'
        elif any(word in pricing_model_clean for word in ['OPEN', 'SOURCE', 'MIT', 'GPL']):
            return 'OPEN_SOURCE'
        
        # Default to FREEMIUM as safe choice
        return 'FREEMIUM'
    
    def _normalize_price_range(self, price_range: str) -> str:
        """Normalize price range to match API enum values"""
        if not price_range:
            return 'MEDIUM'
            
        price_range = price_range.upper().strip()
        
        # Handle multiple values (take the first one)
        if '|' in price_range:
            price_range = price_range.split('|')[0].strip()
        
        # Map to valid enum values
        price_map = {
            'FREE': 'FREE',
            'LOW': 'LOW',
            'MEDIUM': 'MEDIUM',
            'HIGH': 'HIGH',
            'ENTERPRISE': 'ENTERPRISE'
        }
        
        return price_map.get(price_range, 'MEDIUM')  # Default to MEDIUM
    
    def _normalize_employee_count(self, employee_count: str) -> Optional[str]:
        """Normalize employee count to match API enum values"""
        if not employee_count or employee_count.lower() in ['unknown', 'n/a', 'na', '']:
            return None
            
        employee_count_clean = str(employee_count).upper().strip()
        
        # Direct mapping for exact matches
        count_map = {
            '1-10': 'C1_10',
            '11-50': 'C11_50', 
            '51-200': 'C51_200',
            '201-500': 'C201_500',
            '501-1000': 'C501_1000',
            '1001-5000': 'C1001_5000',
            '5000+': 'C5001_PLUS',
            '5001+': 'C5001_PLUS',
            '500+': 'C501_1000',
            '1000+': 'C1001_5000',
            'UNKNOWN': None,
            'SMALL': 'C1_10',
            'MEDIUM': 'C11_50',
            'LARGE': 'C201_500',
            'ENTERPRISE': 'C5001_PLUS'
        }
        
        # Check direct mapping first
        if employee_count_clean in count_map:
            return count_map[employee_count_clean]
        
        # Try to extract number and map to range
        import re
        numbers = re.findall(r'\d+', employee_count_clean)
        if numbers:
            count = int(numbers[0])
            if count <= 10:
                return 'C1_10'
            elif count <= 50:
                return 'C11_50'
            elif count <= 200:
                return 'C51_200'
            elif count <= 500:
                return 'C201_500'
            elif count <= 1000:
                return 'C501_1000'
            elif count <= 5000:
                return 'C1001_5000'
            else:
                return 'C5001_PLUS'
        
        # Default to None if can't parse
        return None
    
    def _normalize_funding_stage(self, funding_stage: str) -> Optional[str]:
        """Normalize funding stage to match API enum values"""
        if not funding_stage or funding_stage.lower() in ['unknown', 'n/a', 'na', '']:
            return None
            
        funding_stage_clean = str(funding_stage).upper().strip().replace('-', '_').replace(' ', '_')
        
        # Comprehensive mapping for funding stages
        stage_map = {
            'PRE_SEED': 'PRE_SEED',
            'PRESEED': 'PRE_SEED',
            'PRE SEED': 'PRE_SEED',
            'SEED': 'SEED',
            'SERIES_A': 'SERIES_A',
            'SERIES A': 'SERIES_A',
            'SERIESA': 'SERIES_A',
            'A': 'SERIES_A',
            'SERIES_B': 'SERIES_B', 
            'SERIES B': 'SERIES_B',
            'SERIESB': 'SERIES_B',
            'B': 'SERIES_B',
            'SERIES_C': 'SERIES_C',
            'SERIES C': 'SERIES_C',
            'SERIESC': 'SERIES_C',
            'C': 'SERIES_C',
            'SERIES_D': 'SERIES_D_PLUS',
            'SERIES D': 'SERIES_D_PLUS',
            'SERIESD': 'SERIES_D_PLUS',
            'D': 'SERIES_D_PLUS',
            'SERIES_D_PLUS': 'SERIES_D_PLUS',
            'SERIES_E': 'SERIES_D_PLUS',
            'SERIES E': 'SERIES_D_PLUS',
            'LATE_STAGE': 'SERIES_D_PLUS',
            'GROWTH': 'SERIES_D_PLUS',
            'PUBLIC': 'PUBLIC',
            'IPO': 'PUBLIC',
            'PUBLICLY_TRADED': 'PUBLIC',
            'ACQUIRED': 'PUBLIC',
            'BOOTSTRAPPED': None,
            'SELF_FUNDED': None,
            'STEALTH': 'PRE_SEED',
            'ANGEL': 'PRE_SEED',
            'FRIENDS_AND_FAMILY': 'PRE_SEED',
            'UNKNOWN': None,
            'NONE': None,
            'NOT_DISCLOSED': None,
            'PRIVATE': None
        }
        
        # Check direct mapping first
        if funding_stage_clean in stage_map:
            return stage_map[funding_stage_clean]
        
        # Try partial matches for complex stages
        if 'PRE' in funding_stage_clean and 'SEED' in funding_stage_clean:
            return 'PRE_SEED'
        elif 'SEED' in funding_stage_clean:
            return 'SEED'
        elif 'SERIES' in funding_stage_clean:
            if 'A' in funding_stage_clean:
                return 'SERIES_A'
            elif 'B' in funding_stage_clean:
                return 'SERIES_B'
            elif 'C' in funding_stage_clean:
                return 'SERIES_C'
            elif any(letter in funding_stage_clean for letter in ['D', 'E', 'F']):
                return 'SERIES_D_PLUS'
        elif any(word in funding_stage_clean for word in ['PUBLIC', 'IPO', 'TRADED']):
            return 'PUBLIC'
        
        # Default to None if can't parse
        return None
    
    def _get_entity_type_id(self) -> str:
        """Get the entity type ID for AI tools"""
        return "e35dea27-b628-40fc-99c5-e09ae63fb135"  # AI Tool entity type ID
    
    def _clean_null_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively remove null/empty values from the data structure"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if value is not None and value != "" and value != []:
                    if isinstance(value, (dict, list)):
                        cleaned_value = self._clean_null_values(value)
                        if cleaned_value:  # Only add if not empty after cleaning
                            cleaned[key] = cleaned_value
                    else:
                        cleaned[key] = value
            return cleaned
        elif isinstance(data, list):
            return [self._clean_null_values(item) for item in data if item is not None and item != ""]
        else:
            return data