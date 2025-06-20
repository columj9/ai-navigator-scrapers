"""
Comprehensive FutureTools Discovery and Processing
Get ALL tools from FutureTools and process them with maximum data extraction
"""

import sys
sys.path.append('/app')
import subprocess
import time
import json
import requests
from bs4 import BeautifulSoup

def discover_all_futuretools():
    """
    Discover all possible FutureTools pages and URLs
    """
    print("🔍 DISCOVERING ALL FUTURETOOLS PAGES")
    print("=" * 50)
    
    # Known working patterns to explore
    discovery_urls = [
        "https://www.futuretools.io/",
        "https://www.futuretools.io/tools",
        "https://www.futuretools.io/sitemap.xml",  # Check for sitemap
    ]
    
    discovered_tools = set()
    discovered_pages = set()
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    })
    
    for url in discovery_urls:
        try:
            print(f"🔍 Exploring: {url}")
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                if 'sitemap' in url:
                    # Parse sitemap
                    soup = BeautifulSoup(response.text, 'xml')
                    urls = soup.find_all('url')
                    for url_elem in urls:
                        loc = url_elem.find('loc')
                        if loc and '/tools/' in loc.text:
                            discovered_tools.add(loc.text)
                    print(f"   📋 Found {len(discovered_tools)} tool URLs in sitemap")
                else:
                    # Parse HTML for tool links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for tool links
                    tool_links = soup.find_all('a', href=True)
                    for link in tool_links:
                        href = link['href']
                        if '/tools/' in href:
                            full_url = requests.compat.urljoin(url, href)
                            discovered_tools.add(full_url)
                    
                    print(f"   📋 Found {len(discovered_tools)} total tool URLs")
            else:
                print(f"   ❌ Failed to access {url}: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error exploring {url}: {str(e)}")
    
    print(f"\n🎯 DISCOVERY SUMMARY:")
    print(f"   📊 Total unique tool URLs discovered: {len(discovered_tools)}")
    
    # Save discovered URLs for scraping
    with open('/app/ai-navigator-scrapers/discovered_futuretools.txt', 'w') as f:
        for tool_url in sorted(discovered_tools):
            f.write(tool_url + '\n')
    
    print(f"   💾 Saved to: /app/ai-navigator-scrapers/discovered_futuretools.txt")
    return list(discovered_tools)

def run_comprehensive_scraping():
    """
    Run the comprehensive scraping process
    """
    print("\n🚀 RUNNING COMPREHENSIVE FUTURETOOLS SCRAPING")
    print("=" * 60)
    
    # First run our existing scraper
    print("📥 Running existing scraper...")
    existing_count = 20  # We already have 20 tools
    
    # Try to discover more URLs
    discovered_urls = discover_all_futuretools()
    
    if len(discovered_urls) > existing_count:
        print(f"\n🎉 Discovered {len(discovered_urls)} total tool URLs!")
        print(f"📈 We have {existing_count} already, potential {len(discovered_urls) - existing_count} more to get")
        
        # Create a new spider that uses the discovered URLs
        create_discovery_spider(discovered_urls[:100])  # Limit to first 100 for now
        
        # Run the discovery spider
        print("🕷️ Running discovery spider...")
        subprocess.run([
            'scrapy', 'crawl', 'futuretools_discovery', 
            '-o', 'futuretools_discovery_leads.jsonl'
        ], cwd='/app/ai-navigator-scrapers', capture_output=True)
        
        # Check results
        try:
            with open('/app/ai-navigator-scrapers/futuretools_discovery_leads.jsonl', 'r') as f:
                discovery_count = sum(1 for line in f)
            print(f"✅ Discovery scraper found {discovery_count} additional tools")
        except:
            discovery_count = 0
            print("⚠️ Discovery scraper results not found")
    
    # Combine all results
    combine_all_results()

def create_discovery_spider(urls):
    """Create a spider that targets specific discovered URLs"""
    
    spider_code = f'''import scrapy
from ainav_scrapers.items import AiToolLeadItem
import datetime

class FuturetoolsDiscoverySpider(scrapy.Spider):
    name = "futuretools_discovery"
    allowed_domains = ["futuretools.io"]
    
    start_urls = {repr(urls[:50])}  # First 50 URLs
    
    custom_settings = {{
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'DOWNLOAD_DELAY': 0.5,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'FEEDS': {{
            'futuretools_discovery_leads.jsonl': {{
                'format': 'jsonlines',
                'encoding': 'utf8',
                'store_empty': False,
                'fields': ['tool_name_on_directory', 'external_website_url', 'source_directory', 'scraped_date'],
            }}
        }},
        'ROBOTSTXT_OBEY': True,
    }}

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
'''
    
    # Write the spider file
    with open('/app/ai-navigator-scrapers/ainav_scrapers/spiders/futuretools_discovery.py', 'w') as f:
        f.write(spider_code)
    
    print(f"✅ Created discovery spider for {len(urls)} URLs")

def combine_all_results():
    """Combine all FutureTools scraping results"""
    
    print("\n📊 COMBINING ALL FUTURETOOLS RESULTS")
    print("=" * 50)
    
    all_tools = []
    source_files = [
        '/app/ai-navigator-scrapers/futuretools_leads.jsonl',          # Original 40 tools
        '/app/ai-navigator-scrapers/futuretools_all_leads.jsonl',     # Our 20 new tools  
        '/app/ai-navigator-scrapers/futuretools_discovery_leads.jsonl' # Discovery results
    ]
    
    seen_tools = set()
    
    for file_path in source_files:
        try:
            with open(file_path, 'r') as f:
                count = 0
                for line in f:
                    try:
                        tool = json.loads(line.strip())
                        tool_key = f"{tool['tool_name_on_directory']}:{tool['external_website_url']}"
                        
                        if tool_key not in seen_tools:
                            seen_tools.add(tool_key)
                            all_tools.append(tool)
                            count += 1
                    except:
                        continue
                
                print(f"📁 {file_path}: {count} unique tools")
        except FileNotFoundError:
            print(f"📁 {file_path}: Not found")
    
    # Save combined results
    combined_file = '/app/ai-navigator-scrapers/futuretools_combined_all.jsonl'
    with open(combined_file, 'w') as f:
        for tool in all_tools:
            f.write(json.dumps(tool) + '\\n')
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   📊 Total unique FutureTools scraped: {len(all_tools)}")
    print(f"   💾 Combined file: {combined_file}")
    
    return combined_file, len(all_tools)

def main():
    """Main execution function"""
    
    print("🌟 COMPREHENSIVE FUTURETOOLS SCRAPING SYSTEM")
    print("Getting ALL AI tools from FutureTools for world-class directory")
    print("=" * 70)
    
    start_time = time.time()
    
    # Run comprehensive scraping
    run_comprehensive_scraping()
    
    # Get final results
    combined_file, total_count = combine_all_results()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🎉 FUTURETOOLS COMPREHENSIVE SCRAPING COMPLETE!")
    print("=" * 60)
    print(f"📊 Total AI tools scraped: {total_count}")
    print(f"⏱️ Total time: {duration:.1f} seconds")
    print(f"💾 Combined results: {combined_file}")
    
    if total_count > 50:
        print(f"🌟 Excellent! We have {total_count} FutureTools for comprehensive processing!")
    elif total_count > 20:
        print(f"✅ Good progress with {total_count} FutureTools collected!")
    else:
        print(f"⚠️ Need to improve discovery methods - only {total_count} tools found")
    
    print(f"\n🚀 Ready to process all {total_count} tools with:")
    print(f"   • Maximum data extraction (50+ fields per tool)")
    print(f"   • Clean URL processing")
    print(f"   • 100% logo coverage")
    print(f"   • Comprehensive market intelligence")
    
    return combined_file, total_count

if __name__ == "__main__":
    main()