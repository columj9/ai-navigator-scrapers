import scrapy
from ainav_scrapers.items import AiToolLeadItem
from urllib.parse import urljoin
import datetime
import asyncio

class ComprehensiveFuturetoolsSpider(scrapy.Spider):
    name = "futuretools_complete"
    allowed_domains = ["futuretools.io"]
    
    # Comprehensive start URLs to get ALL tools
    start_urls = [
        "https://www.futuretools.io/",
        "https://www.futuretools.io/tools", 
        "https://www.futuretools.io/browse-tools",
        "https://www.futuretools.io/ai-tools",
        # Category pages to ensure comprehensive coverage
        "https://www.futuretools.io/ai-tools/category/copywriting",
        "https://www.futuretools.io/ai-tools/category/design", 
        "https://www.futuretools.io/ai-tools/category/video",
        "https://www.futuretools.io/ai-tools/category/audio",
        "https://www.futuretools.io/ai-tools/category/code",
        "https://www.futuretools.io/ai-tools/category/business",
        "https://www.futuretools.io/ai-tools/category/productivity",
        "https://www.futuretools.io/ai-tools/category/research",
        "https://www.futuretools.io/ai-tools/category/education",
        "https://www.futuretools.io/ai-tools/category/marketing",
        "https://www.futuretools.io/ai-tools/category/sales",
        "https://www.futuretools.io/ai-tools/category/customer-support",
        "https://www.futuretools.io/ai-tools/category/social-media",
        "https://www.futuretools.io/ai-tools/category/finance",
        "https://www.futuretools.io/ai-tools/category/healthcare",
        "https://www.futuretools.io/ai-tools/category/legal",
        "https://www.futuretools.io/ai-tools/category/real-estate",
        "https://www.futuretools.io/ai-tools/category/travel",
        "https://www.futuretools.io/ai-tools/category/gaming",
        "https://www.futuretools.io/ai-tools/category/fitness",
        "https://www.futuretools.io/ai-tools/category/fashion",
        "https://www.futuretools.io/ai-tools/category/food",
        "https://www.futuretools.io/ai-tools/category/entertainment",
    ]

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,  # Faster for comprehensive scraping
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # Slightly more aggressive for speed
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        'FEEDS': {
            'futuretools_complete_leads.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date', 'category', 'page_url'],
                'indent': None,
            }
        },
        # REMOVED ITEM LIMIT - Scrape everything!
        # 'CLOSESPIDER_ITEMCOUNT': 50,  # Remove this to get ALL tools
        'ROBOTSTXT_OBEY': True,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',  # Ensure no duplicate URLs
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_tools = set()  # Track scraped tools to avoid duplicates
        self.total_tools_found = 0
        self.pages_processed = 0

    def start_requests(self):
        """Generate requests for all start URLs with comprehensive coverage"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list_page,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "page_type": "start_page",
                    "source_url": url
                }
            )

    async def parse_list_page(self, response):
        """Parse tool listing pages with comprehensive extraction"""
        page = response.meta.get("playwright_page")
        source_url = response.meta.get("source_url", response.url)
        
        self.pages_processed += 1
        self.logger.info(f"Processing page {self.pages_processed}: {response.url}")
        
        if page:
            try:
                # Handle infinite scroll / load more buttons
                await self.handle_dynamic_loading(page, response)
                
                # Get updated content after dynamic loading
                updated_content = await page.content()
                response = response.replace(body=updated_content)
                
            except Exception as e:
                self.logger.warning(f"Error handling dynamic content on {response.url}: {str(e)}")
            finally:
                await page.close()

        if response.status != 200:
            self.logger.error(f"Failed to load page {response.url} with status {response.status}")
            return

        # Multiple selectors to catch all possible tool card formats
        tool_selectors = [
            'div.tool.tool-home',           # Homepage format
            'div.tool-card',                # Grid format
            'div.tool-item',                # List format
            '.tool-container',              # Alternative container
            '[class*="tool"][class*="card"]', # Flexible class matching
            'div[data-tool-id]',            # Data attribute format
        ]
        
        tools_found = []
        for selector in tool_selectors:
            tool_cards = response.css(selector)
            if tool_cards:
                tools_found.extend(tool_cards)
                self.logger.info(f"Found {len(tool_cards)} tools using selector '{selector}' on {response.url}")

        # Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in tools_found:
            tool_html = tool.get()
            if tool_html not in seen:
                seen.add(tool_html)
                unique_tools.append(tool)

        total_tools_on_page = len(unique_tools)
        self.total_tools_found += total_tools_on_page
        self.logger.info(f"Total unique tools on {response.url}: {total_tools_on_page}")

        # Process each tool
        for i, card in enumerate(unique_tools, 1):
            await self.process_tool_card(card, response, source_url, i, total_tools_on_page)

        # Look for pagination and additional pages
        await self.handle_pagination(response)

        # Discover and follow category links for comprehensive coverage
        await self.discover_additional_pages(response)

        self.logger.info(f"Page {response.url} complete. Total tools found so far: {self.total_tools_found}")

    async def handle_dynamic_loading(self, page, response):
        """Handle infinite scroll and load more buttons"""
        max_load_attempts = 20  # Maximum "Load More" clicks
        load_more_selectors = [
            'button[class*="load-more"]',
            'button[class*="show-more"]', 
            '.load-more-button',
            'button:contains("Load More")',
            'button:contains("Show More")',
            '[data-action="load-more"]',
            '.pagination-load-more',
        ]
        
        for attempt in range(max_load_attempts):
            try:
                # Try different load more selectors
                load_more_clicked = False
                for selector in load_more_selectors:
                    try:
                        # Check if button exists and is visible
                        load_more_button = await page.query_selector(selector)
                        if load_more_button:
                            # Check if button is visible and clickable
                            is_visible = await load_more_button.is_visible()
                            is_enabled = await load_more_button.is_enabled()
                            
                            if is_visible and is_enabled:
                                self.logger.info(f"Clicking load more button (attempt {attempt + 1}) with selector: {selector}")
                                await load_more_button.click()
                                load_more_clicked = True
                                
                                # Wait for new content to load
                                await page.wait_for_timeout(3000)
                                break
                    except Exception as e:
                        self.logger.debug(f"Load more selector '{selector}' failed: {str(e)}")
                        continue

                if not load_more_clicked:
                    # Try infinite scroll
                    try:
                        # Scroll to bottom to trigger infinite scroll
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(2000)
                        
                        # Check if new content loaded by comparing page height
                        current_height = await page.evaluate("document.body.scrollHeight")
                        await page.wait_for_timeout(1000)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        
                        if new_height > current_height:
                            self.logger.info(f"Infinite scroll triggered new content (attempt {attempt + 1})")
                            await page.wait_for_timeout(2000)  # Wait for content to fully load
                        else:
                            self.logger.info(f"No more content to load after {attempt + 1} attempts")
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"Infinite scroll attempt {attempt + 1} failed: {str(e)}")
                        break
                else:
                    # Wait a bit more after successful load more click
                    await page.wait_for_timeout(2000)

            except Exception as e:
                self.logger.warning(f"Dynamic loading attempt {attempt + 1} failed: {str(e)}")
                break

        self.logger.info(f"Dynamic loading completed after {attempt + 1} attempts")

    async def process_tool_card(self, card, response, source_url, index, total):
        """Process individual tool card with multiple selector strategies"""
        
        # Multiple strategies for extracting tool information
        detail_link_selectors = [
            'a.tool-item-link-block---new::attr(href)',  # Current selector
            'a.tool-link::attr(href)',
            'a[href*="/tool/"]::attr(href)',
            'a[href*="/ai-tools/"]::attr(href)',
            '.tool-title a::attr(href)',
            '.tool-name a::attr(href)',
            'a::attr(href)',  # Fallback - any link in the card
        ]
        
        tool_name_selectors = [
            'a.tool-item-link---new::text',  # Current selector
            '.tool-title::text',
            '.tool-name::text',
            'h3::text',
            'h2::text',
            '.title::text',
            'a::text',  # Fallback
        ]
        
        # Extract detail page link
        detail_page_link = None
        for selector in detail_link_selectors:
            detail_page_link = card.css(selector).get()
            if detail_page_link:
                break
        
        # Extract tool name
        tool_name_from_list = None
        for selector in tool_name_selectors:
            tool_name_from_list = card.css(selector).get()
            if tool_name_from_list:
                tool_name_from_list = tool_name_from_list.strip()
                if tool_name_from_list:  # Make sure it's not empty
                    break
        
        if not tool_name_from_list:
            tool_name_from_list = f"Tool-{index}"  # Fallback name
        
        # Extract category if available
        category = self.extract_category_from_url(source_url)
        
        self.logger.debug(f"Processing tool {index}/{total}: {tool_name_from_list}")
        
        if detail_page_link:
            # Avoid duplicate processing
            tool_key = f"{tool_name_from_list}:{detail_page_link}"
            if tool_key not in self.scraped_tools:
                self.scraped_tools.add(tool_key)
                
                full_detail_page_url = response.urljoin(detail_page_link)
                self.logger.info(f"Queuing tool {index}/{total}: '{tool_name_from_list}' -> {full_detail_page_url}")
                
                yield scrapy.Request(
                    full_detail_page_url,
                    callback=self.parse_tool_detail,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "tool_name_from_list": tool_name_from_list,
                        "category": category,
                        "source_page": response.url,
                    }
                )
            else:
                self.logger.debug(f"Skipping duplicate tool: {tool_name_from_list}")
        else:
            self.logger.warning(f"Could not find detail page link for tool {index}/{total} on {response.url}")
            # Log the card HTML for debugging
            self.logger.debug(f"Card HTML: {card.get()[:300]}...")

    def extract_category_from_url(self, url):
        """Extract category from URL path"""
        if "/category/" in url:
            parts = url.split("/category/")
            if len(parts) > 1:
                category = parts[1].split("/")[0].replace("-", " ").title()
                return category
        return "General"

    async def handle_pagination(self, response):
        """Handle pagination links"""
        pagination_selectors = [
            'a[rel="next"]::attr(href)',
            '.pagination-next::attr(href)',
            '.next-page::attr(href)',
            'a:contains("Next")::attr(href)',
            'a:contains("→")::attr(href)',
            '[data-page="next"]::attr(href)',
        ]
        
        for selector in pagination_selectors:
            next_page = response.css(selector).get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                self.logger.info(f"Found next page: {next_page_url}")
                
                yield scrapy.Request(
                    next_page_url,
                    callback=self.parse_list_page,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "page_type": "pagination",
                        "source_url": response.url,
                    }
                )
                break

    async def discover_additional_pages(self, response):
        """Discover additional category and tool pages"""
        
        # Look for category links
        category_selectors = [
            'a[href*="/category/"]::attr(href)',
            'a[href*="/ai-tools/category/"]::attr(href)',
            '.category-link::attr(href)',
            'nav a::attr(href)',
        ]
        
        category_links = set()
        for selector in category_selectors:
            links = response.css(selector).getall()
            for link in links:
                if "/category/" in link:
                    category_links.add(response.urljoin(link))
        
        # Follow new category pages
        for category_url in category_links:
            if category_url not in [req.url for req in self.crawler.engine.slot.scheduler.pending_requests()]:
                self.logger.info(f"Discovered new category page: {category_url}")
                
                yield scrapy.Request(
                    category_url,
                    callback=self.parse_list_page,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "page_type": "discovered_category",
                        "source_url": category_url,
                    }
                )

    async def parse_tool_detail(self, response):
        """Parse individual tool detail page"""
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        tool_name_from_list = response.meta.get("tool_name_from_list", "Unknown")
        category = response.meta.get("category", "General")
        source_page = response.meta.get("source_page", "")
        
        self.logger.info(f"Parsing tool detail: '{tool_name_from_list}' from {response.url}")

        if response.status != 200:
            self.logger.error(f"Failed to load tool detail page {response.url} with status {response.status}")
            return

        item = AiToolLeadItem()
        item['source_directory'] = "futuretools.io"
        item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        item['tool_name_on_directory'] = tool_name_from_list
        item['category'] = category
        item['page_url'] = response.url

        # Multiple selectors for external URL with enhanced extraction
        external_url_selectors = [
            'a.link-block-2::attr(href)',           # Current selector
            'a[class*="external-link"]::attr(href)',
            'a[href^="http"]:not([href*="futuretools.io"])::attr(href)',  # Any external link
            '.website-link::attr(href)',
            '.official-link::attr(href)',
            'a[data-external-url]::attr(data-external-url)',
            'a[data-url]::attr(data-url)',
        ]

        external_url = None
        for selector in external_url_selectors:
            external_url = response.css(selector).get()
            if external_url and not external_url.startswith('#'):
                break

        if external_url:
            # Enhanced validation for external URLs
            if any(disallowed in external_url for disallowed in ["/goto/", "/recommends/", "/track/"]):
                self.logger.warning(f"Found disallowed tracking URL for '{tool_name_from_list}': {external_url}")
                
                # Try to extract the actual destination URL from data attributes
                direct_url_selectors = [
                    'a.link-block-2::attr(data-actual-url)',
                    'a.link-block-2::attr(data-external-url)',
                    'a.link-block-2::attr(data-target-url)',
                    'a.link-block-2::attr(data-href)',
                ]
                
                for direct_selector in direct_url_selectors:
                    direct_url = response.css(direct_selector).get()
                    if direct_url:
                        external_url = direct_url
                        self.logger.info(f"Found direct URL in data attribute: {external_url}")
                        break
                else:
                    # If we can't find a direct URL, we'll use the tracking URL but log it
                    self.logger.warning(f"Using tracking URL for '{tool_name_from_list}' as no direct URL found")

            item['external_website_url'] = external_url
            
            self.logger.info(f"✅ Successfully extracted: {tool_name_from_list} -> {external_url}")
            yield item
        else:
            self.logger.warning(f"❌ Could not find external URL for '{tool_name_from_list}' on {response.url}")
            # Still yield the item but with a placeholder URL for investigation
            item['external_website_url'] = f"NOT_FOUND:{response.url}"
            yield item

    def closed(self, reason):
        """Spider closed callback with comprehensive statistics"""
        self.logger.info(f"🎉 FutureTools comprehensive scraping completed!")
        self.logger.info(f"📊 Final Statistics:")
        self.logger.info(f"   • Total tools scraped: {len(self.scraped_tools)}")
        self.logger.info(f"   • Total pages processed: {self.pages_processed}")
        self.logger.info(f"   • Unique tools found: {self.total_tools_found}")
        self.logger.info(f"   • Closure reason: {reason}")
        
        if len(self.scraped_tools) > 100:
            self.logger.info(f"🌟 Excellent! Scraped {len(self.scraped_tools)} tools for comprehensive AI directory!")
        elif len(self.scraped_tools) > 50:
            self.logger.info(f"✅ Good coverage with {len(self.scraped_tools)} tools scraped!")
        else:
            self.logger.warning(f"⚠️ Lower than expected: only {len(self.scraped_tools)} tools scraped")