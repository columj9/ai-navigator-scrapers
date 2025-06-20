import scrapy
from ainav_scrapers.items import AiToolLeadItem
import datetime

class FuturetoolsDiscoverySpider(scrapy.Spider):
    name = "futuretools_discovery"
    allowed_domains = ["futuretools.io"]
    
    start_urls = ['https://www.futuretools.io/tools/warp-terminal', 'https://www.futuretools.io/tools/indipen', 'https://www.futuretools.io/tools/willow-voice', 'https://www.futuretools.io/tools/skywork', 'https://www.futuretools.io/tools/purecode-ai', 'https://www.futuretools.io/tools/duix', 'https://www.futuretools.io/tools/votars', 'https://www.futuretools.io/tools/postplanify', 'https://www.futuretools.io/tools/scribbe-ai-note-taker', 'https://www.futuretools.io/tools/nimblr-ai', 'https://www.futuretools.io/tools/open-paper', 'https://www.futuretools.io/tools/agentnest', 'https://www.futuretools.io/tools/grimly-ai', 'https://www.futuretools.io/tools/voagents-ai', 'https://www.futuretools.io/tools/hatch', 'https://www.futuretools.io/tools/lunacal', 'https://www.futuretools.io/tools/schedx', 'https://www.futuretools.io/tools/propzella', 'https://www.futuretools.io/tools/socialaf', 'https://www.futuretools.io/tools/weavy', 'https://www.futuretools.io/tools/cloudeagle-ai', 'https://www.futuretools.io/tools/bismuth', 'https://www.futuretools.io/tools/plansom', 'https://www.futuretools.io/tools/nlevel-ai', 'https://www.futuretools.io/tools/agentpass-ai', 'https://www.futuretools.io/tools/flux-playground', 'https://www.futuretools.io/tools/kuberns', 'https://www.futuretools.io/tools/rierino', 'https://www.futuretools.io/tools/rekla-ai', 'https://www.futuretools.io/tools/prism', 'https://www.futuretools.io/tools/myriade', 'https://www.futuretools.io/tools/propstyle', 'https://www.futuretools.io/tools/line0', 'https://www.futuretools.io/tools/pubmed-ai', 'https://www.futuretools.io/tools/handtext-ai', 'https://www.futuretools.io/tools/promptve', 'https://www.futuretools.io/tools/blaze-ai', 'https://www.futuretools.io/tools/promptatlas', 'https://www.futuretools.io/tools/buildship-tools', 'https://www.futuretools.io/tools/mindly', 'https://www.futuretools.io/tools/kvitly', 'https://www.futuretools.io/tools/sheetsy', 'https://www.futuretools.io/tools/modelslab', 'https://www.futuretools.io/tools/tapflow', 'https://www.futuretools.io/tools/kosmik', 'https://www.futuretools.io/tools/monobot-cx', 'https://www.futuretools.io/tools/chat4data', 'https://www.futuretools.io/tools/prompt-shuttle', 'https://www.futuretools.io/tools/caimera-ai', 'https://www.futuretools.io/tools/playwise']  # First 50 URLs
    
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'DOWNLOAD_DELAY': 0.5,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'FEEDS': {
            'futuretools_discovery_leads.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
            }
        },
        'ROBOTSTXT_OBEY': True,
    }

    def parse(self, response):
        if response.status != 200:
            return
        
        # Extract tool name from URL or page
        tool_name = response.url.split('/')[-1].replace('-', ' ').title()
        
        # Try to get the actual tool name from the page
        page_title = response.css('h1::text').get()
        if page_title:
            tool_name = page_title.strip()
        
        # Extract external URL
        external_url = response.css('a.link-block-2::attr(href)').get()
        
        if not external_url:
            # Try alternative selectors
            selectors = [
                'a[href^="http"]:not([href*="futuretools.io"])::attr(href)',
                'a[target="_blank"]::attr(href)',
                '.website-link::attr(href)',
            ]
            for selector in selectors:
                external_url = response.css(selector).get()
                if external_url:
                    break
        
        if external_url:
            item = AiToolLeadItem()
            item['tool_name_on_directory'] = tool_name
            item['external_website_url'] = external_url
            item['source_directory'] = "futuretools.io"
            item['scraped_date'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            yield item
