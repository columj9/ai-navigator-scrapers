import scrapy
from ainav_scrapers.items import AiToolLeadItem
from urllib.parse import urljoin
import datetime
# Removed PageCoroutine import for now, will add back if specific actions are needed via that route
# from scrapy_playwright.page import PageCoroutine

class TaaftSpider(scrapy.Spider):
    name = "taaft"
    allowed_domains = ["theresanaiforthat.com"]
    # Start at the main archive page to discover all period links
    start_urls = ["https://theresanaiforthat.com/period/"]

    # NFR1: Respectful Scraping - Define custom settings for rate limiting
    custom_settings = {
        # 'DOWNLOAD_DELAY': 2, # Playwright handles its own delays/waits
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0, # Number of concurrent requests to the same domain
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', # Common browser UA
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000, # 60 seconds for page loads
        # Ensure ROBOTSTXT_OBEY = True is in settings.py (default)
        'FEEDS': {
            'taaft_leads.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': None,
                'indent': 4,
                'item_export_kwargs': {
                    'export_empty_fields': True,
                },
            }
        },
        'CLOSESPIDER_ITEMCOUNT': 5, # Reduced for quicker Cloudflare testing
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_period_archives,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_event_handlers": { # Log page events
                        "load": "handle_load_event",
                        "domcontentloaded": "handle_domcontentloaded_event",
                        # "response": "handle_response_event", # Can be very verbose
                    }
                }
            )
    
    async def handle_load_event(self, page):
        self.logger.info(f"Playwright page 'load' event triggered for URL: {page.url}")

    async def handle_domcontentloaded_event(self, page):
        self.logger.info(f"Playwright page 'domcontentloaded' event triggered for URL: {page.url}")

    # async def handle_response_event(self, response):
    #     self.logger.info(f"Playwright received response: {response.status} for {response.url}")
    #     return True # Must return True or the response is dropped

    async def parse_period_archives(self, response):
        page = response.meta.get("playwright_page")
        self.logger.info(f"Scrapy received response with status {response.status} for {response.url}")

        if response.status == 403 and page:
            try:
                screenshot_path = f"playwright_screenshot_403_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                self.logger.info(f"Saved 403 screenshot to {screenshot_path} for {response.url}")
            except Exception as e:
                self.logger.error(f"Failed to take 403 screenshot for {response.url}: {e}")
        
        if page:
            await page.close()
        
        if response.status != 200:
            self.logger.error(f"Skipping parsing for {response.url} due to status {response.status}.")
            return

        self.logger.info(f"Parsing period archive discovery page: {response.url}")
        # Selector for links to specific period pages (e.g., /period/november/, /period/2023/, /period/2019/)
        # These links are usually in a list or grid on the /period/ page.
        # Assuming they are direct links within a main content area.
        # Example selector if they are in a div with class 'archive-links': response.css("div.archive-links a::attr(href)").getall()
        # Based on site structure, these are likely direct links: a[href^='/period/'] that are not the page itself.
        period_page_links = response.css("main a[href^='/period/']::attr(href)").getall()
        
        self.logger.info(f"Found {len(period_page_links)} period page links on {response.url}")
        unique_period_links = set()
        for link in period_page_links:
            full_link = response.urljoin(link)
            # Avoid re-scraping the main /period/ page if it's linked to itself
            if full_link != response.url and "/page/" not in full_link: # also avoid pagination links from period archive page itself
                 unique_period_links.add(full_link)

        for period_link in unique_period_links:
            self.logger.info(f"Yielding request for period page: {period_link}")
            yield scrapy.Request(
                period_link,
                callback=self.parse_period_listing,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )
        
        # Handle pagination on the /period/ archive page itself, if any (e.g. if there are many years/months)
        # Your selector for next_page was: a.show_more::attr(href). This might apply here if the /period/ page is long.
        next_archive_page = response.css('a.show_more::attr(href)').get() # VERIFIED SELECTOR for pagination on archive lists
        if next_archive_page:
            full_next_archive_page_url = response.urljoin(next_archive_page)
            self.logger.info(f"Found next period archive page: {full_next_archive_page_url}")
            yield scrapy.Request(
                full_next_archive_page_url,
                callback=self.parse_period_archives, # Recursive call for paginated archive page
                meta={
                    "playwright": True, 
                    "playwright_include_page": True,
                }
            )

    async def parse_period_listing(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        if response.status != 200:
            self.logger.error(f"Skipping parsing for listing page {response.url} due to status {response.status}.")
            return

        self.logger.info(f"Parsing tools list page: {response.url}")
        # tool_card_link: a.stats::attr(href)
        tool_detail_page_links = response.css('a.stats::attr(href)').getall() # VERIFIED SELECTOR
        self.logger.info(f"Found {len(tool_detail_page_links)} tool detail links on {response.url}")

        for relative_link in tool_detail_page_links:
            full_detail_url = response.urljoin(relative_link)
            yield scrapy.Request(
                full_detail_url,
                callback=self.parse_tool_detail,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )
        
        # Handle pagination on individual period listing pages (e.g. /period/november/)
        # next_page_link: a.show_more::attr(href)
        next_list_page = response.css('a.show_more::attr(href)').get() # VERIFIED SELECTOR for pagination on list pages
        if next_list_page:
            full_next_list_page_url = response.urljoin(next_list_page)
            self.logger.info(f"Found next tools list page: {full_next_list_page_url}")
            yield scrapy.Request(
                full_next_list_page_url,
                callback=self.parse_period_listing, # Recursive call for paginated list page
                meta={
                    "playwright": True, 
                    "playwright_include_page": True,
                }
            )

    async def parse_tool_detail(self, response):
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        if response.status != 200:
            self.logger.error(f"Skipping parsing for detail page {response.url} due to status {response.status}.")
            return

        item = AiToolLeadItem()
        item['source_directory'] = "theresanaiforthat.com"
        item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # website_url: a#ai_top_link::attr(href)
        # name: h1.title_inner::text
        item['tool_name_on_directory'] = response.css('h1.title_inner::text').get(default='').strip() # VERIFIED SELECTOR
        item['external_website_url'] = response.css('a#ai_top_link::attr(href)').get() # VERIFIED SELECTOR
        
        if item.get('external_website_url'): # Only yield if we got the crucial external URL
            self.logger.info(f"Successfully extracted lead: {item['tool_name_on_directory']} - {item['external_website_url']}")
            yield item
        else:
            self.logger.warning(f"Could not extract external_website_url from {response.url}. Name: {item.get('tool_name_on_directory')}")
