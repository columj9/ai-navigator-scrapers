import scrapy
from ainav_scrapers.items import AiToolLeadItem
from urllib.parse import urljoin
import datetime
# Consider adding Sitemapper for easier sitemap parsing if it gets complex
# from scrapy.spiders import SitemapSpider # or from scrapy.crawler import CrawlerProcess etc.

class ToolifySpider(scrapy.Spider):
    name = "toolify"
    allowed_domains = ["toolify.ai"]
    start_urls = ["https://www.toolify.ai/"]
    # If using SitemapSpider, you would define sitemap_urls instead of start_urls
    # sitemap_urls = ['https://www.toolify.ai/sitemap.xml']
    # sitemap_rules = [
    #     # Example:('/tool/', 'parse_tool_detail_page'), # Adjust pattern for tool detail URLs
    #     # Example:('/category/', 'parse_list_page'),    # Adjust pattern for category list URLs
    # ] # This is a more advanced setup, for now we start with start_urls and manual sitemap parsing

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True, # Enable auto-throttling
        'AUTOTHROTTLE_START_DELAY': 5, # Start with a 5s delay
        'AUTOTHROTTLE_MAX_DELAY': 60, # Max delay
        'DOWNLOAD_DELAY': 5, # Crucial: Be respectful and start with a high delay
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1, # Further limit concurrency
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Safari/537.36',
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000, # 60 seconds for Playwright page loads
        'FEEDS': {
            'toolify_leads.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
                'indent': None,
            }
        },
        # Playwright settings (already in settings.py but can be overridden here if needed)
        # 'DOWNLOAD_HANDLERS': {
        #     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        #     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        # },
        # 'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        # 'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'CLOSESPIDER_ITEMCOUNT': 100, # Aim for a good number of leads for V1, adjust as needed
        'ROBOTSTXT_OBEY': True,
    }

    def start_requests(self):
        # Option 1: Start with main page(s)
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list_page,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    # "playwright_page_event_handlers": {
                    #     "response": "handle_response" # Example for debugging
                    # }
                }
            )

        # Option 2: Add sitemap parsing logic
        # For simplicity, we'll stick to start_urls for now.
        # Sitemap parsing can be added here if needed:
        # yield scrapy.Request("https://www.toolify.ai/sitemap.xml", self.parse_sitemap)

    # async def handle_response(self, response):
    #     # Example Playwright response handler for debugging
    #     self.logger.info(f"Playwright received response for {response.url} (status: {response.status})")

    async def parse_sitemap(self, response):
        # Placeholder for sitemap parsing logic
        # This would typically use response.css() or response.xpath() with sitemap-specific selectors
        # to find further sitemaps or page URLs.
        # For example, to find <loc> tags:
        # urls = response.xpath('//*[local-name()="url"]/*[local-name()="loc"]/text()').getall()
        # for url in urls:
        #     if "/tool/" in url: # Example filter for tool pages
        #         yield scrapy.Request(url, self.parse_tool_detail, meta={"playwright": True, "playwright_include_page": True})
        #     elif "/category/" in url: # Example filter for category pages
        #         yield scrapy.Request(url, self.parse_list_page, meta={"playwright": True, "playwright_include_page": True})
        self.logger.info(f"Sitemap parsing not yet implemented for {response.url}")
        if False:
            yield None # Make it an async generator

    async def parse_list_page(self, response):
        page = response.meta.get("playwright_page")
        if page:
            # Placeholder: Add logic to click "load more" or handle pagination if selectors provided by user
            # e.g., await page.click("USER_PROVIDED_LOAD_MORE_SELECTOR")
            # await page.wait_for_timeout(5000) # Wait for content
            # response = response.replace(body=await page.content()) # Update response body
            await page.close()

        self.logger.info(f"Parsing list page: {response.url} (status: {response.status})")
        if response.status != 200:
            self.logger.error(f"Failed to load list page {response.url} with status {response.status}")
            return

        # USER TO PROVIDE SELECTORS HERE
        tool_card_selector = "div.tool-item"  # Placeholder - replace with actual selector
        detail_page_link_selector = "a.tool-link::attr(href)" # Placeholder
        tool_name_on_list_selector = "h3.tool-name::text" # Placeholder
        
        # self.logger.warning(f"Using placeholder selectors for list page {response.url}. Please provide actual selectors.")

        tool_cards = response.css(tool_card_selector)
        self.logger.info(f"Found {len(tool_cards)} tool cards on {response.url} using selector: '{tool_card_selector}'")
        
        if not tool_cards:
             self.logger.warning(f"No tool cards found on {response.url}. Check tool_card_selector: '{tool_card_selector}'")


        for card_index, card in enumerate(tool_cards):
            detail_page_link = card.css(detail_page_link_selector).get()
            tool_name_from_list = card.css(tool_name_on_list_selector).get(default='').strip()

            if not tool_name_from_list:
                 self.logger.warning(f"Card {card_index+1} on {response.url}: Could not extract tool name using selector '{tool_name_on_list_selector}'. Card HTML snippet: {card.get()[:150]}...")
            if not detail_page_link:
                 self.logger.warning(f"Card {card_index+1} for tool '{tool_name_from_list}' on {response.url}: Could not extract detail page link using selector '{detail_page_link_selector}'. Card HTML snippet: {card.get()[:150]}...")


            if detail_page_link:
                full_detail_page_url = response.urljoin(detail_page_link)
                self.logger.info(f"Found detail page link for '{tool_name_from_list}': {full_detail_page_url}")
                yield scrapy.Request(
                    full_detail_page_url,
                    callback=self.parse_tool_detail,
                    meta={
                        "playwright": True, # Detail pages might also need JS
                        "playwright_include_page": True,
                        "tool_name_from_list": tool_name_from_list,
                    }
                )
            # else: # Already logged above
                # self.logger.warning(f"Could not find detail page link for a card on {response.url}. Card HTML: {card.get()[:200]}...")
        
        # USER: Provide selector for next page (pagination)
        # next_page_selector = "a.next-page::attr(href)" # Placeholder
        # next_page = response.css(next_page_selector).get()
        # if next_page:
        #     yield scrapy.Request(response.urljoin(next_page), 
        #                          callback=self.parse_list_page,
        #                          meta=response.meta) # Propagate playwright meta

        if not tool_cards: # If no cards, and no next page logic implemented yet, this is to satisfy async generator
            if False: yield None

    async def parse_tool_detail(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        tool_name_from_list = response.meta.get("tool_name_from_list", "Unknown")
        self.logger.info(f"Parsing detail page for '{tool_name_from_list}': {response.url} (status: {response.status})")

        if response.status != 200:
            self.logger.error(f"Failed to load detail page {response.url} with status {response.status}")
            return

        item = AiToolLeadItem()
        item['source_directory'] = "toolify.ai"
        item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # USER TO PROVIDE SELECTORS HERE
        tool_name_on_detail_page_selector = "h1.tool-title::text" # Placeholder
        # Prioritize attributes like data-gofullurl, data-actual-url, or a clean href.
        # User needs to inspect and provide the best strategy.
        external_url_selectors = [
            "a.official-website-link::attr(data-gofullurl)", # Placeholder - highest priority
            "a.official-website-link::attr(data-actual-url)",# Placeholder - second priority
            "a.official-website-link::attr(href)",           # Placeholder - fallback
        ]
        
        # self.logger.warning(f"Using placeholder selectors for detail page {response.url}. Please provide actual selectors.")

        name_on_detail = response.css(tool_name_on_detail_page_selector).get(default='').strip()
        item['tool_name_on_directory'] = name_on_detail if name_on_detail else tool_name_from_list
        
        if not item['tool_name_on_directory']:
             self.logger.warning(f"Could not determine tool name for {response.url} from list or detail page.")


        external_url = None
        for selector_index, selector_str in enumerate(external_url_selectors):
            external_url = response.css(selector_str).get()
            if external_url:
                self.logger.info(f"Extracted external_url '{external_url}' using selector priority {selector_index+1}: '{selector_str}' for {item['tool_name_on_directory']}")
                break 
        
        if external_url:
            # USER: Refine this check based on toolify.ai's specific redirect patterns and robots.txt
            # This is a generic check.
            disallowed_patterns = ["/redirect/", "/visit/", "/track/", "affiliate=", "ref="] 
            is_disallowed = False
            for pattern in disallowed_patterns:
                if pattern in external_url.lower(): # Check lowercased URL
                    # Further check if it's a path on toolify.ai vs an external domain parameter
                    if external_url.startswith("/") or "toolify.ai" in urljoin(response.url, external_url):
                        self.logger.warning(f"Potential disallowed redirect pattern '{pattern}' found in URL '{external_url}' for tool '{item['tool_name_on_directory']}'. This URL might be skipped or needs careful review against robots.txt.")
                        # Depending on policy, you might 'return' here to not yield the item,
                        # or try to resolve it if allowed and feasible.
                        is_disallowed = True # Example, might need more nuanced handling
                        break
            
            if not is_disallowed: # Or more sophisticated logic
                item['external_website_url'] = response.urljoin(external_url) # Ensure it's absolute
                self.logger.info(f"Successfully extracted lead: {item['tool_name_on_directory']} - {item['external_website_url']}")
                yield item
            else:
                self.logger.error(f"Skipping item for '{item['tool_name_on_directory']}' due to disallowed URL pattern: {external_url}")

        else:
            self.logger.warning(f"Could not find external_website_url for '{item['tool_name_on_directory']}' on {response.url} using provided selectors: {external_url_selectors}")

        if not external_url: # To satisfy async generator if no item yielded
             if False: yield None 