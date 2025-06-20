import scrapy
from ainav_scrapers.items import AiToolLeadItem
import datetime

class FuturetoolsUltraSpider(scrapy.Spider):
    name = "futuretools_ultra"
    allowed_domains = ["futuretools.io"]
    
    def extract_all_possible_tools(self, response):
        """Extract tools using EVERY possible selector pattern"""
        
        # Ultra-comprehensive tool selectors
        tool_selectors = [
            # Known working selectors
            'div.tool.tool-home',
            'div.tool-card',
            'div.tool-item',
            
            # Generic patterns
            '[class*="tool"]:has(a)',
            '[data-tool]',
            '[data-tool-id]',
            '[data-item-id]',
            
            # Card patterns
            '.card:has(a[href*="/tool"])',
            '.card:has(a[href*="/ai-tool"])',
            '.item:has(a[href*="/tool"])',
            
            # Grid/list patterns
            '.grid-item:has(a)',
            '.list-item:has(a)',
            '.product-item:has(a)',
            '.ai-tool',
            '.tool-listing',
            
            # Generic containers with links
            'div:has(a[href*="/tool"]):not(:has(div:has(a[href*="/tool"])))',
            'article:has(a)',
            'section:has(a[href*="/tool"])',
            
            # Fallback: any container with external links
            'div:has(a[href^="http"]:not([href*="futuretools.io"]))',
        ]
        
        all_tools = []
        tools_on_page = 0
        
        for selector in tool_selectors:
            try:
                tool_cards = response.css(selector)
                if tool_cards:
                    self.logger.info(f"Found {len(tool_cards)} potential tools with selector: {selector}")
                    
                    for card in tool_cards:
                        tool_data = self.extract_tool_from_card(card, response)
                        if tool_data:
                            tool_key = f"{tool_data['name']}:{tool_data['url']}"
                            if tool_key not in self.scraped_tools:
                                self.scraped_tools.add(tool_key)
                                all_tools.append(tool_data)
                                tools_on_page += 1
                    
                    # If we found tools with this selector, we can be more confident
                    if tools_on_page > 0:
                        break
                        
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
        
        # Process found tools
        for tool_data in all_tools:
            yield self.create_tool_request(tool_data, response)
        
        self.total_tools_found += tools_on_page
        self.logger.info(f"✅ Extracted {tools_on_page} tools from {response.url}")
        self.logger.info(f"📊 Total tools found so far: {self.total_tools_found}")

    def ultra_aggressive_page_discovery(self, response):
        """Discover ALL possible pages with tools"""
        
        # Look for any links that might contain tools
        discovery_patterns = [
            'a[href*="/tool"]',
            'a[href*="/ai-tool"]',
            'a[href*="/category"]',
            'a[href*="/browse"]',
            'a[href*="/search"]',
            'a[href*="/filter"]',
            'a[href*="/page"]',
            'a[href*="?page="]',
            'a[href*="?p="]',
            'nav a',
            '.navigation a',
            '.menu a',
            '.sidebar a',
            '.pagination a',
        ]
        
        discovered_urls = set()
        
        for pattern in discovery_patterns:
            links = response.css(f'{pattern}::attr(href)').getall()
            for link in links:
                if link:
                    full_url = response.urljoin(link)
                    if self.is_valid_discovery_url(full_url):
                        discovered_urls.add(full_url)
        
        # Follow discovered URLs
        for url in discovered_urls:
            if url not in self.discovered_pages:
                self.discovered_pages.add(url)
                
                yield scrapy.Request(
                    url,
                    callback=self.parse_list_page,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "page_type": "discovered",
                        "discovery_source": response.url
                    },
                    dont_filter=False
                )

    def discover_all_pagination(self, response):
        """Discover all pagination pages"""
        
        base_url = response.url.split('?')[0]  # Remove existing query params
        
        # Try different pagination patterns
        for pattern in self.pagination_patterns:
            for page_num in range(1, min(self.max_pages_to_check, 101)):  # Check up to 100 pages initially
                page_url = base_url + pattern.format(page_num)
                
                if page_url not in self.discovered_pages:
                    self.discovered_pages.add(page_url)
                    
                    yield scrapy.Request(
                        page_url,
                        callback=self.parse_list_page,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                            "page_type": "pagination",
                            "discovery_source": f"pagination_{pattern}_{page_num}"
                        },
                        dont_filter=False,
                        errback=self.handle_pagination_error
                    )