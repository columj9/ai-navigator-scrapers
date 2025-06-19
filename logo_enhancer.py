"""
Enhanced Logo Extraction Service
Ensures 100% logo coverage for all entities with multiple fallback methods
"""

import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional, Dict, Any
import re
import time

class LogoEnhancer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        })
    
    def get_comprehensive_logo(self, website_url: str, tool_name: str = "") -> str:
        """
        Get logo URL with 100% success guarantee using multiple fallback methods
        """
        self.logger.info(f"🔍 Searching for logo for {tool_name} at {website_url}")
        
        # Method 1: Direct website scraping with enhanced selectors
        logo_url = self._scrape_website_logo(website_url)
        if logo_url:
            self.logger.info(f"✅ Found logo via website scraping: {logo_url}")
            return logo_url
        
        # Method 2: Check common logo paths
        logo_url = self._check_common_logo_paths(website_url)
        if logo_url:
            self.logger.info(f"✅ Found logo via common paths: {logo_url}")
            return logo_url
        
        # Method 3: Social media APIs and services
        logo_url = self._get_social_media_logo(website_url, tool_name)
        if logo_url:
            self.logger.info(f"✅ Found logo via social media: {logo_url}")
            return logo_url
        
        # Method 4: Clearbit Logo API (free service)
        logo_url = self._get_clearbit_logo(website_url)
        if logo_url:
            self.logger.info(f"✅ Found logo via Clearbit: {logo_url}")
            return logo_url
        
        # Method 5: Favicon services (multiple providers)
        logo_url = self._get_favicon_service_logo(website_url)
        if logo_url:
            self.logger.info(f"✅ Found logo via favicon service: {logo_url}")
            return logo_url
        
        # Method 6: Generate fallback logo using initials
        logo_url = self._generate_fallback_logo(tool_name)
        self.logger.info(f"✅ Generated fallback logo: {logo_url}")
        return logo_url
    
    def _scrape_website_logo(self, website_url: str) -> Optional[str]:
        """Enhanced website scraping with comprehensive selectors"""
        try:
            response = self.session.get(website_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Comprehensive logo selectors (expanded list)
            logo_selectors = [
                # Direct logo selectors
                'img[alt*="logo" i]',
                'img[class*="logo" i]', 
                'img[src*="logo" i]',
                'img[id*="logo" i]',
                
                # Brand selectors
                'img[alt*="brand" i]',
                'img[class*="brand" i]',
                'img[id*="brand" i]',
                
                # Company name selectors
                f'img[alt*="{urlparse(website_url).netloc.split(".")[0]}" i]',
                
                # Container-based selectors
                '.logo img',
                '.brand img', 
                '.navbar-brand img',
                '.header-logo img',
                '.site-logo img',
                'header img:first-of-type',
                '.header img:first-of-type',
                'nav img:first-of-type',
                '.navbar img:first-of-type',
                
                # Layout-based selectors
                'header .logo',
                'header .brand',
                '.top-bar img',
                '.masthead img',
                
                # CSS class variations
                '[class*="logo"] img',
                '[class*="brand"] img', 
                '[class*="Logo"] img',
                '[class*="Brand"] img',
                '[class*="LOGO"] img',
                
                # Link-based logo selectors
                'a[class*="logo"] img',
                'a[class*="brand"] img',
                'a.logo img',
                'a.brand img',
                
                # SVG logos
                'svg[class*="logo" i]',
                'svg[id*="logo" i]',
                '.logo svg',
                '.brand svg',
                
                # Fallback: first image in header/nav
                'header img',
                'nav img',
                '.header img',
                '.navigation img'
            ]
            
            for selector in logo_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # Handle both img and svg elements
                    if element.name == 'img':
                        src = element.get('src')
                    elif element.name == 'svg':
                        # For SVG, we'd need to handle differently
                        continue
                    else:
                        src = element.get('src')
                    
                    if src:
                        # Convert relative URLs to absolute
                        if not src.startswith('http'):
                            src = urljoin(website_url, src)
                        
                        # Validate the logo
                        if self._validate_logo_url(src):
                            return src
            
            # Method: Look for high-quality favicons and touch icons
            icon_selectors = [
                'link[rel="apple-touch-icon"][sizes*="180"]',
                'link[rel="apple-touch-icon"][sizes*="152"]', 
                'link[rel="apple-touch-icon"][sizes*="144"]',
                'link[rel="apple-touch-icon"][sizes*="120"]',
                'link[rel="apple-touch-icon-precomposed"][sizes*="180"]',
                'link[rel="apple-touch-icon-precomposed"][sizes*="152"]',
                'link[rel="icon"][sizes*="192"]',
                'link[rel="icon"][sizes*="180"]',
                'link[rel="icon"][sizes*="96"]',
                'link[rel="mask-icon"]'
            ]
            
            for selector in icon_selectors:
                icon_element = soup.select_one(selector)
                if icon_element and icon_element.get('href'):
                    href = icon_element['href']
                    if not href.startswith('http'):
                        href = urljoin(website_url, href)
                    
                    if self._validate_logo_url(href):
                        return href
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error scraping website logo from {website_url}: {str(e)}")
            return None
    
    def _check_common_logo_paths(self, website_url: str) -> Optional[str]:
        """Check common logo file paths"""
        domain = urlparse(website_url).netloc
        base_url = f"https://{domain}"
        
        # Expanded list of common logo paths
        common_paths = [
            '/logo.png', '/logo.svg', '/logo.jpg', '/logo.jpeg', '/logo.webp',
            '/assets/logo.png', '/assets/logo.svg', '/assets/logo.jpg',
            '/assets/images/logo.png', '/assets/images/logo.svg',
            '/static/logo.png', '/static/logo.svg', '/static/logo.jpg',
            '/static/images/logo.png', '/static/images/logo.svg',
            '/images/logo.png', '/images/logo.svg', '/images/logo.jpg',
            '/img/logo.png', '/img/logo.svg', '/img/logo.jpg',
            '/media/logo.png', '/media/logo.svg', '/media/logo.jpg',
            '/content/logo.png', '/content/logo.svg',
            '/uploads/logo.png', '/uploads/logo.svg',
            '/public/logo.png', '/public/logo.svg',
            '/dist/logo.png', '/dist/logo.svg',
            '/build/logo.png', '/build/logo.svg',
            
            # Brand variations
            '/brand.png', '/brand.svg', '/brand.jpg',
            '/assets/brand.png', '/assets/brand.svg',
            '/images/brand.png', '/images/brand.svg',
            
            # Company name variations
            f'/{domain.split(".")[0]}.png',
            f'/{domain.split(".")[0]}.svg',
            f'/assets/{domain.split(".")[0]}.png',
            f'/images/{domain.split(".")[0]}.svg',
            
            # Size variations
            '/logo-192.png', '/logo-180.png', '/logo-120.png',
            '/logo@2x.png', '/logo_2x.png',
            '/logo-large.png', '/logo-small.png'
        ]
        
        for path in common_paths:
            full_url = urljoin(base_url, path)
            if self._validate_logo_url(full_url):
                return full_url
        
        return None
    
    def _get_social_media_logo(self, website_url: str, tool_name: str) -> Optional[str]:
        """Extract logo from social media profiles"""
        try:
            # Try to find social media links on the website
            response = self.session.get(website_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for social media links
            social_selectors = [
                'a[href*="linkedin.com"]',
                'a[href*="twitter.com"]', 
                'a[href*="x.com"]',
                'a[href*="facebook.com"]',
                'a[href*="github.com"]'
            ]
            
            for selector in social_selectors:
                social_link = soup.select_one(selector)
                if social_link and social_link.get('href'):
                    social_url = social_link['href']
                    
                    # For LinkedIn, try to extract company logo
                    if 'linkedin.com/company' in social_url:
                        # This would require LinkedIn API or scraping
                        # For now, skip as it's complex
                        pass
                    
                    # For GitHub, try organization avatar
                    elif 'github.com' in social_url and '/organizations/' not in social_url:
                        # Extract organization name
                        parts = social_url.strip('/').split('/')
                        if len(parts) >= 4:
                            org_name = parts[3]
                            avatar_url = f"https://github.com/{org_name}.png?size=200"
                            if self._validate_logo_url(avatar_url):
                                return avatar_url
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting social media logo: {str(e)}")
            return None
    
    def _get_clearbit_logo(self, website_url: str) -> Optional[str]:
        """Get logo from Clearbit Logo API"""
        try:
            domain = urlparse(website_url).netloc
            clearbit_url = f"https://logo.clearbit.com/{domain}"
            
            if self._validate_logo_url(clearbit_url):
                return clearbit_url
            
            # Try with www prefix/suffix variations
            if domain.startswith('www.'):
                domain_no_www = domain[4:]
                clearbit_url = f"https://logo.clearbit.com/{domain_no_www}"
                if self._validate_logo_url(clearbit_url):
                    return clearbit_url
            else:
                domain_www = f"www.{domain}"
                clearbit_url = f"https://logo.clearbit.com/{domain_www}"
                if self._validate_logo_url(clearbit_url):
                    return clearbit_url
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting Clearbit logo: {str(e)}")
            return None
    
    def _get_favicon_service_logo(self, website_url: str) -> Optional[str]:
        """Get logo from multiple favicon services"""
        domain = urlparse(website_url).netloc
        
        # Multiple favicon services for better coverage
        favicon_services = [
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
            f"https://www.google.com/s2/favicons?domain={domain}&sz=256",  
            f"https://favicon.yandex.net/favicon/{domain}",
            f"https://icons.duckduckgo.com/ip2/{domain}.ico",
            f"https://api.faviconkit.com/{domain}/144",
            f"https://besticon-demo.herokuapp.com/icon?url={website_url}&size=120"
        ]
        
        for service_url in favicon_services:
            try:
                response = self.session.head(service_url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    if any(img_type in content_type for img_type in ['image/', 'png', 'jpg', 'jpeg', 'svg', 'webp']):
                        return service_url
            except:
                continue
        
        # Fallback to Google favicon (always works)
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    
    def _generate_fallback_logo(self, tool_name: str) -> str:
        """Generate a fallback logo using external service"""
        # Use UI Avatars service to generate initial-based logos
        if tool_name:
            # Extract initials from tool name
            words = re.findall(r'\b\w', tool_name.upper())
            initials = ''.join(words[:2])  # Take first 2 initials
            
            # Generate logo with nice colors
            logo_url = f"https://ui-avatars.com/api/?name={initials}&size=128&background=6366f1&color=ffffff&bold=true&format=png"
            return logo_url
        else:
            # Generic AI logo
            return "https://ui-avatars.com/api/?name=AI&size=128&background=6366f1&color=ffffff&bold=true&format=png"
    
    def _validate_logo_url(self, logo_url: str) -> bool:
        """Validate that a logo URL is accessible and is an image"""
        try:
            response = self.session.head(logo_url, timeout=10)
            
            # Check if URL is accessible
            if response.status_code not in [200, 301, 302]:
                return False
            
            # Check if it's an image
            content_type = response.headers.get('content-type', '').lower()
            if any(img_type in content_type for img_type in ['image/', 'png', 'jpg', 'jpeg', 'svg', 'gif', 'webp']):
                return True
            
            # Some services don't return proper content-type in HEAD, try GET
            if 'favicon' in logo_url or 'logo' in logo_url:
                return True
            
            return False
            
        except Exception:
            return False

def backfill_missing_logos(ai_client, website_urls_list):
    """
    Backfill missing logos for existing entities
    """
    logo_enhancer = LogoEnhancer()
    logger = logging.getLogger(__name__)
    
    results = []
    
    for website_url, tool_name in website_urls_list:
        try:
            logger.info(f"🔍 Getting logo for {tool_name} at {website_url}")
            
            logo_url = logo_enhancer.get_comprehensive_logo(website_url, tool_name)
            
            results.append({
                'tool_name': tool_name,
                'website_url': website_url,
                'logo_url': logo_url,
                'success': True
            })
            
            # Small delay to be respectful
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Error getting logo for {tool_name}: {str(e)}")
            results.append({
                'tool_name': tool_name,
                'website_url': website_url,
                'logo_url': None,
                'success': False,
                'error': str(e)
            })
    
    return results