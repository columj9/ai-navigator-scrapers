"""
SIMPLE BUT AGGRESSIVE FUTURETOOLS SCRAPER
Focus on getting THOUSANDS of tools efficiently
"""

import scrapy
from ainav_scrapers.items import AiToolLeadItem
import datetime

class FuturetoolsMegaSpider(scrapy.Spider):
    name = "futuretools_mega"
    allowed_domains = ["futuretools.io"]
    
    start_urls = [
        "https://www.futuretools.io/",
    ]

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
        'FEEDS': {
            'futuretools_mega_all.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
            }
        },
        'ROBOTSTXT_OBEY': True,
        'CLOSESPIDER_TIMEOUT': 1800,  # 30 minutes max
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_tools = set()
        self.total_found = 0

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_with_js,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                }
            )

    async def parse_with_js(self, response):
        page = response.meta.get("playwright_page")
        
        if page:
            try:
                # MEGA LOADING - try to load EVERYTHING
                self.logger.info("🚀 Starting MEGA loading of all content...")
                
                # Try 50 load more clicks!
                for attempt in range(50):
                    try:
                        # Multiple load more strategies
                        load_buttons = [
                            'button:has-text("Load More")',
                            'button:has-text("Show More")',
                            '.load-more',
                            'button[class*="load"]',
                            'a:has-text("Load More")',
                        ]
                        
                        clicked = False
                        for button_selector in load_buttons:
                            try:
                                button = await page.query_selector(button_selector)
                                if button and await button.is_visible():
                                    await button.click()
                                    await page.wait_for_timeout(3000)
                                    clicked = True
                                    self.logger.info(f"MEGA Load More clicked: attempt {attempt + 1}")
                                    break
                            except:
                                continue
                        
                        if not clicked:
                            # Try scrolling instead
                            try:
                                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                await page.wait_for_timeout(2000)
                            except:
                                break
                        
                    except Exception as e:
                        self.logger.debug(f"Load attempt {attempt + 1} failed: {str(e)}")
                        break
                
                self.logger.info("🏁 MEGA loading complete")
                
                # Get final content
                content = await page.content()
                response = response.replace(body=content)
                
            except Exception as e:
                self.logger.error(f"MEGA loading error: {str(e)}")
            finally:
                await page.close()

        # Now extract ALL tools
        return self.extract_mega_tools(response)

    def extract_mega_tools(self, response):
        """Extract maximum number of tools"""
        
        self.logger.info("🔍 Extracting MEGA tools...")
        
        # Use the working selector but get ALL tools
        tool_cards = response.css('div.tool.tool-home')
        self.logger.info(f"🎯 Found {len(tool_cards)} tool cards")
        
        tools_processed = 0
        
        for i, card in enumerate(tool_cards, 1):
            try:
                # Extract tool info
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
                        tools_processed += 1
                        
                        full_url = response.urljoin(detail_link)
                        self.logger.info(f"🎯 [{tools_processed}] Queuing: {tool_name}")
                        
                        yield scrapy.Request(
                            full_url,
                            callback=self.parse_tool_detail,
                            meta={"tool_name": tool_name}
                        )
                
            except Exception as e:
                self.logger.debug(f"Error processing card {i}: {str(e)}")
                continue
        
        self.total_found = tools_processed
        self.logger.info(f"🎉 MEGA extraction complete: {tools_processed} tools found!")

    def parse_tool_detail(self, response):
        """Parse tool detail page"""
        tool_name = response.meta.get("tool_name", "Unknown")
        
        if response.status != 200:
            self.logger.error(f"Failed to load tool page: {response.url}")
            return

        # Extract external URL
        external_url = response.css('a.link-block-2::attr(href)').get()
        
        if not external_url:
            # Try alternatives
            alternatives = [
                'a[href^="http"]:not([href*="futuretools.io"])::attr(href)',
                'a[target="_blank"]::attr(href)',
            ]
            for selector in alternatives:
                external_url = response.css(selector).get()
                if external_url:
                    break

        if external_url:
            item = AiToolLeadItem()
            item['tool_name_on_directory'] = tool_name
            item['external_website_url'] = external_url
            item['source_directory'] = "futuretools.io"
            item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            self.logger.info(f"✅ MEGA extracted: {tool_name} -> {external_url}")
            yield item
        else:
            self.logger.warning(f"❌ No external URL for {tool_name}")

    def closed(self, reason):
        self.logger.info(f"🎉 MEGA FUTURETOOLS SCRAPING COMPLETE!")
        self.logger.info(f"📊 Total tools found: {len(self.scraped_tools)}")
        self.logger.info(f"📊 Reason: {reason}")
        
        if len(self.scraped_tools) >= 1000:
            self.logger.info(f"🌟 INCREDIBLE! We got {len(self.scraped_tools)} tools!")
        elif len(self.scraped_tools) >= 500:
            self.logger.info(f"🎉 EXCELLENT! {len(self.scraped_tools)} tools scraped!")
        elif len(self.scraped_tools) >= 200:
            self.logger.info(f"✅ GREAT! {len(self.scraped_tools)} tools found!")
        else:
            self.logger.info(f"📊 Found {len(self.scraped_tools)} tools total")