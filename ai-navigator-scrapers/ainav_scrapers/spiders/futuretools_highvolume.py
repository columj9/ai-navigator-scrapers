"""
SIMPLE HIGH-VOLUME FUTURETOOLS SCRAPER
Fast scraping without JavaScript - focused on getting ALL tools
"""

import scrapy
from ainav_scrapers.items import AiToolLeadItem
import datetime
import time

class FuturetoolsHighVolumeSpider(scrapy.Spider):
    name = "futuretools_highvolume"
    allowed_domains = ["futuretools.io"]
    
    # Try multiple entry points
    start_urls = [
        "https://www.futuretools.io/",
        "https://www.futuretools.io/tools",
    ]

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,  # Faster
        'DOWNLOAD_DELAY': 0.5,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'FEEDS': {
            'futuretools_highvolume_all.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
            }
        },
        'ROBOTSTXT_OBEY': True,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_tools = set()
        self.pages_tried = set()
        self.total_found = 0

    def parse(self, response):
        """Parse homepage and look for tools"""
        self.logger.info(f"🔍 Parsing: {response.url}")
        
        if response.status != 200:
            self.logger.error(f"Failed to load {response.url}")
            return

        # Find tool cards
        tool_cards = response.css('div.tool.tool-home')
        self.logger.info(f"🎯 Found {len(tool_cards)} tools on {response.url}")
        
        for i, card in enumerate(tool_cards, 1):
            detail_link = card.css('a.tool-item-link-block---new::attr(href)').get()
            tool_name = card.css('a.tool-item-link---new::text').get()
            
            if tool_name:
                tool_name = tool_name.strip()
            else:
                tool_name = f"Tool-{i}"
            
            if detail_link:
                tool_key = f"{tool_name}:{detail_link}"
                if tool_key not in self.scraped_tools:
                    self.scraped_tools.add(tool_key)
                    
                    full_url = response.urljoin(detail_link)
                    self.logger.info(f"🎯 Queuing: {tool_name}")
                    
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_tool_detail,
                        meta={"tool_name": tool_name}
                    )
        
        # Try to find more pages by looking for pagination or "load more" URLs
        # Look for any links that might lead to more tools
        more_tool_links = response.css('a[href*="page"], a[href*="?p="], .pagination a, .load-more').xpath('@href').getall()
        
        for link in more_tool_links:
            if link:
                full_link = response.urljoin(link)
                if full_link not in self.pages_tried and self.is_tools_page(full_link):
                    self.pages_tried.add(full_link)
                    self.logger.info(f"🔗 Following: {full_link}")
                    
                    yield scrapy.Request(
                        full_link,
                        callback=self.parse,
                        dont_filter=False
                    )
        
        # Try systematic pagination
        yield from self.try_pagination(response)

    def try_pagination(self, response):
        """Try systematic pagination to find more tools"""
        base_url = response.url.split('?')[0]
        
        # Try different pagination patterns
        patterns = [
            '?page={}',
            '?p={}',
            '/page/{}',
        ]
        
        for pattern in patterns:
            for page_num in range(2, 26):  # Try pages 2-25
                page_url = base_url + pattern.format(page_num)
                
                if page_url not in self.pages_tried:
                    self.pages_tried.add(page_url)
                    
                    yield scrapy.Request(
                        page_url,
                        callback=self.parse,
                        dont_filter=False,
                        errback=self.handle_page_error,
                        meta={"page_type": "pagination"}
                    )

    def is_tools_page(self, url):
        """Check if URL likely contains tools"""
        return any(keyword in url.lower() for keyword in ['tool', 'page', 'browse', 'directory'])

    def parse_tool_detail(self, response):
        """Parse individual tool detail page"""
        tool_name = response.meta.get("tool_name", "Unknown")
        
        if response.status != 200:
            self.logger.warning(f"Failed to load tool page for {tool_name}: {response.url}")
            return

        # Extract external URL using multiple selectors
        external_selectors = [
            'a.link-block-2::attr(href)',
            'a[href^="http"]:not([href*="futuretools.io"])::attr(href)',
            'a[target="_blank"]::attr(href)',
            '.website-link::attr(href)',
            '.external-link::attr(href)',
            '.official-site::attr(href)',
        ]

        external_url = None
        for selector in external_selectors:
            external_url = response.css(selector).get()
            if external_url and external_url.startswith('http'):
                break

        if external_url:
            item = AiToolLeadItem()
            item['tool_name_on_directory'] = tool_name
            item['external_website_url'] = external_url
            item['source_directory'] = "futuretools.io"
            item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            self.total_found += 1
            self.logger.info(f"✅ [{self.total_found}] {tool_name} -> {external_url}")
            yield item
        else:
            self.logger.warning(f"❌ No external URL found for {tool_name} at {response.url}")

    def handle_page_error(self, failure):
        """Handle pagination errors gracefully"""
        self.logger.debug(f"Page error (likely end of pagination): {failure.request.url}")

    def closed(self, reason):
        """Spider closing statistics"""
        self.logger.info(f"🎉 HIGH-VOLUME FUTURETOOLS SCRAPING COMPLETE!")
        self.logger.info(f"📊 Total tools found: {len(self.scraped_tools)}")
        self.logger.info(f"📊 Total extracted: {self.total_found}")
        self.logger.info(f"📊 Pages tried: {len(self.pages_tried)}")
        self.logger.info(f"📊 Closure reason: {reason}")
        
        if self.total_found >= 500:
            self.logger.info(f"🌟 EXCELLENT! We found {self.total_found} tools!")
        elif self.total_found >= 200:
            self.logger.info(f"✅ GREAT! {self.total_found} tools extracted!")
        elif self.total_found >= 100:
            self.logger.info(f"👍 GOOD! {self.total_found} tools found!")
        else:
            self.logger.info(f"📊 Found {self.total_found} tools - may need to explore more pages")