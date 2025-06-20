import scrapy
from ainav_scrapers.items import AiToolLeadItem
from urllib.parse import urljoin
import datetime

class SimplifiedFuturetoolsAllSpider(scrapy.Spider):
    name = "futuretools_all"
    allowed_domains = ["futuretools.io"]
    
    # Focus on working URLs first
    start_urls = [
        "https://www.futuretools.io/",
        "https://www.futuretools.io/tools", 
        # Add more as we discover them
    ]

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'FEEDS': {
            'futuretools_all_leads.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
                'indent': None,
            }
        },
        'ROBOTSTXT_OBEY': True,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_tools = set()
        self.total_found = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list_page,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )

    async def parse_list_page(self, response):
        page = response.meta.get("playwright_page")
        
        if page:
            try:
                # Handle load more buttons - simplified approach
                for attempt in range(10):  # Try up to 10 load more clicks
                    try:
                        # Multiple possible selectors for load more
                        load_more_selectors = [
                            'button:contains("Load More")',
                            'button:contains("Show More")',
                            '.load-more',
                            '[data-load-more]'
                        ]
                        
                        clicked = False
                        for selector in load_more_selectors:
                            try:
                                button = await page.query_selector(selector)
                                if button and await button.is_visible():
                                    await button.click()
                                    await page.wait_for_timeout(3000)
                                    clicked = True
                                    self.logger.info(f"Clicked load more button, attempt {attempt + 1}")
                                    break
                            except:
                                continue
                        
                        if not clicked:
                            break
                    except:
                        break
                
                # Get updated content
                updated_content = await page.content()
                response = response.replace(body=updated_content)
                
            except Exception as e:
                self.logger.warning(f"Error with dynamic loading: {str(e)}")
            finally:
                await page.close()

        self.logger.info(f"Processing: {response.url}")

        # Find tool cards - use the working selector
        tool_cards = response.css('div.tool.tool-home')
        self.total_found += len(tool_cards)
        self.logger.info(f"Found {len(tool_cards)} tools on {response.url}")

        for i, card in enumerate(tool_cards, 1):
            # Extract tool information
            detail_link = card.css('a.tool-item-link-block---new::attr(href)').get()
            tool_name = card.css('a.tool-item-link---new::text').get()
            
            if tool_name:
                tool_name = tool_name.strip()
            else:
                tool_name = f"Tool-{i}"
            
            if detail_link:
                # Check for duplicates
                tool_key = f"{tool_name}:{detail_link}"
                if tool_key not in self.scraped_tools:
                    self.scraped_tools.add(tool_key)
                    
                    full_url = response.urljoin(detail_link)
                    self.logger.info(f"Queuing tool {i}: {tool_name} -> {full_url}")
                    
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_tool_detail,
                        meta={
                            "tool_name": tool_name,
                            "playwright": True,
                            "playwright_include_page": True,
                        }
                    )

        # Look for additional discovery opportunities
        # Check for pagination or more tools links
        more_tools_links = response.css('a[href*="tools"]::attr(href)').getall()
        for link in more_tools_links:
            full_link = response.urljoin(link)
            if full_link not in [req.url for req in self.crawler.engine.slot.scheduler.pending_requests()]:
                if any(domain in full_link for domain in self.allowed_domains):
                    self.logger.info(f"Discovered new tools page: {full_link}")
                    yield scrapy.Request(
                        full_link,
                        callback=self.parse_list_page,
                        meta={
                            "playwright": True,
                            "playwright_include_page": True,
                        }
                    )

    async def parse_tool_detail(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        tool_name = response.meta.get("tool_name", "Unknown")
        self.logger.info(f"Parsing detail for: {tool_name} at {response.url}")

        if response.status != 200:
            self.logger.error(f"Failed to load {response.url} - status {response.status}")
            return

        # Extract external URL
        external_url = response.css('a.link-block-2::attr(href)').get()
        
        if not external_url:
            # Try alternative selectors
            alternative_selectors = [
                'a[href^="http"]:not([href*="futuretools.io"])::attr(href)',
                '.external-link::attr(href)',
                'a[target="_blank"]::attr(href)',
            ]
            for selector in alternative_selectors:
                external_url = response.css(selector).get()
                if external_url:
                    break

        if external_url:
            # Create item
            item = AiToolLeadItem()
            item['tool_name_on_directory'] = tool_name
            item['external_website_url'] = external_url
            item['source_directory'] = "futuretools.io"
            item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            self.logger.info(f"✅ Extracted: {tool_name} -> {external_url}")
            yield item
        else:
            self.logger.warning(f"❌ No external URL found for {tool_name} at {response.url}")

    def closed(self, reason):
        self.logger.info(f"🎉 Scraping complete!")
        self.logger.info(f"📊 Found {self.total_found} total tools")
        self.logger.info(f"📊 Unique tools processed: {len(self.scraped_tools)}")
        self.logger.info(f"📊 Reason: {reason}")