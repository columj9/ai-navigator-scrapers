import scrapy
from ainav_scrapers.items import AiToolLeadItem # Ensure this item is defined correctly
from urllib.parse import urljoin
import datetime

class FuturetoolsSpider(scrapy.Spider):
    name = "futuretools"
    allowed_domains = ["futuretools.io"]
    start_urls = ["https://www.futuretools.io/"] # Start with the homepage
    # Consider adding more start URLs like popular category pages if homepage is too limited
    # e.g., "https://www.futuretools.io/browse-tools/", "https://www.futuretools.io/ai-tools/category/copywriting"

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 30,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2, # Be respectful
        'DOWNLOAD_DELAY': 1, # Minimum delay between requests to the same domain
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000, # 60 seconds
        'FEEDS': {
            'futuretools_leads.jsonl': { # Using .jsonl for line-delimited JSON
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'], # Explicitly order fields
                'indent': None, # No indent for jsonlines
            }
        },
        'CLOSESPIDER_ITEMCOUNT': 50, # Get a decent number of leads for testing, adjust as needed
        # 'ROBOTSTXT_OBEY': True, # Default, but good to be mindful
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_list_page,
                meta={
                    "playwright": True, # Start with Playwright in case of JS-dependencies not immediately obvious
                    "playwright_include_page": True,
                    # Add playwright_page_event_handlers if debugging is needed
                }
            )

    async def parse_list_page(self, response):
        page = response.meta.get("playwright_page")
        if page:
            # Potential place to implement "Load More" clicks if necessary:
            # for _ in range(MAX_LOAD_MORE_CLICKS): 
            #     try:
            #         await page.click("YOUR_LOAD_MORE_BUTTON_SELECTOR", timeout=5000)
            #         await page.wait_for_timeout(3000) # Wait for content to load
            #     except Exception as e:
            #         self.logger.info(f"No more 'Load More' button or error: {e}")
            #         break
            # updated_content = await page.content()
            # response = response.replace(body=updated_content)
            await page.close()

        self.logger.info(f"Parsing list page: {response.url} (status: {response.status})")
        if response.status != 200:
            self.logger.error(f"Failed to load list page {response.url} with status {response.status}")
            return

        # Selector for Tool Card Container: div.tool.tool-home
        tool_cards = response.css('div.tool.tool-home')
        self.logger.info(f"Found {len(tool_cards)} tool cards on {response.url}")

        for card in tool_cards:
            # Link to Detail Page: a.tool-item-link-block---new::attr(href)
            detail_page_link = card.css('a.tool-item-link-block---new::attr(href)').get()
            
            # Tool Name (on List Page): a.tool-item-link---new::text
            # This is the name of the link itself, usually the tool's name
            tool_name_from_list = card.css('a.tool-item-link---new::text').get(default='').strip()

            if detail_page_link:
                full_detail_page_url = response.urljoin(detail_page_link)
                self.logger.info(f"Found detail page link for '{tool_name_from_list}': {full_detail_page_url}")
                yield scrapy.Request(
                    full_detail_page_url,
                    callback=self.parse_tool_detail,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "tool_name_from_list": tool_name_from_list, # Pass name for context
                    }
                )
            else:
                self.logger.warning(f"Could not find detail page link for a card on {response.url}. Card HTML: {card.get()[:200]}...")

        # TODO: Implement proper pagination or "Load More" logic here if selectors are found
        # For now, this spider will only process tools on the initial load of start_urls.
        # Example for a next page link:
        # next_page = response.css('YOUR_NEXT_PAGE_SELECTOR::attr(href)').get()
        # if next_page:
        #     yield scrapy.Request(response.urljoin(next_page), callback=self.parse_list_page, meta=response.meta)

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
        item['source_directory'] = "futuretools.io"
        item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Tool Name (Detail Page): h1.heading-3::text
        # Use name from list page as primary, but can confirm/override with detail page name if needed.
        # For AiToolLeadItem, tool_name_on_directory is fine from the list page.
        item['tool_name_on_directory'] = tool_name_from_list 
        # If you need the name from detail page specifically:
        # name_on_detail = response.css('h1.heading-3::text').get(default='').strip()
        # if name_on_detail: item['tool_name_on_directory'] = name_on_detail
        
        # External Website URL: a.link-block-2::attr(href)
        external_url = response.css('a.link-block-2::attr(href)').get()

        if external_url:
            # Check if the URL is a /goto/ or /recommends/ link, which robots.txt disallows following directly
            if "/goto/" in external_url or "/recommends/" in external_url:
                self.logger.warning(f"Found a disallowed path in external URL '{external_url}' for tool '{item['tool_name_on_directory']}'. Respecting robots.txt. This lead might be incomplete or require manual verification if no other direct link is found.")
                # We should not yield this if we cannot get a direct link without going through disallowed paths.
                # However, sometimes the *actual* target URL is also available in another attribute like 'data-gofullurl' or similar on the *same* anchor tag.
                # For futuretools.io, it seems they might use 'data-gofullurl' sometimes, but your selector is for 'href'.
                # Let's assume for now the `a.link-block-2` directly holds the true external URL or we can't get it ethically.
                # If `a.link-block-2::attr(href)` IS the final external URL (not a /goto/ path), then this is fine.
                # If it IS a /goto/ path, we have a problem. You'll need to re-inspect if there's another attribute on that same <a> tag
                # that holds the *actual* final destination URL. For example:
                # direct_external_url = response.css('a.link-block-2::attr(data-actual-url-attribute-if-exists)').get()
                # if direct_external_url:
                #    item['external_website_url'] = direct_external_url
                # else: # cannot get direct link
                #    self.logger.error(f"Cannot ethically extract direct external URL for {item['tool_name_on_directory']}")
                #    return # Do not yield item
                item['external_website_url'] = external_url # Assuming for now it's not a /goto/ or is handled correctly by site
            else:
                item['external_website_url'] = external_url

            if item.get('external_website_url'): # Check again after potential filtering
                 self.logger.info(f"Successfully extracted lead: {item['tool_name_on_directory']} - {item['external_website_url']}")
                 yield item
            else:
                self.logger.warning(f"Could not extract a usable external_website_url for '{item['tool_name_on_directory']}' from {response.url}")
        else:
            self.logger.warning(f"Could not find external_website_url for '{item['tool_name_on_directory']}' on {response.url}")
