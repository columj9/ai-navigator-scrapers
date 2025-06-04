import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse

# Configuration
BASE_URL = "https://theresanaiforthat.com/"
START_PATH = "" # Start from the homepage, adjust if a specific category page is better
OUTPUT_FILE = "tool_leads_taaft.txt"
USER_AGENT = "AINavigatorURLFetcher/1.0 (+https://github.com/your-repo/ai-navigator-scrapers)" # Replace with your project/contact info
REQUEST_DELAY_SECONDS = 2
MAX_PAGES_TO_SCRAPE = 5 # Limit for initial testing, set to a higher number or None for full scrape

def fetch_page(url):
    print(f"Fetching page: {url}")
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_tool_website_urls(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    extracted_urls = set()

    # --- Selector for tool cards/links ---
    # This needs to be identified by inspecting the site's HTML.
    # We are looking for an <a> tag that directly links to the *external* tool website,
    # or an <a> tag that links to an internal detail page from which we can then get the external link.
    # For "There's an AI for That", list pages link to internal detail pages.
    # The actual external link is on the detail page.
    # For *this script's purpose (Phase 1)*, we need the links on the LISTING pages
    # that lead to the DETAIL pages on theresanaiforthat.com.
    # The Scrapy spider (taaft.py) will then visit these detail pages to get the *external* tool URL.
    
    # Selector for links to individual tool *detail pages* on theresanaiforthat.com
    # From previous work, a good guess was: 'a.item-card[data-testid="tool-card-link"]'
    # We need the href attribute from these.
    tool_detail_page_links = soup.select('a.item-card[data-testid="tool-card-link"]')

    for link_tag in tool_detail_page_links:
        href = link_tag.get('href')
        if href:
            full_detail_page_url = urljoin(base_url, href)
            # For THIS script (directory_url_extractor), we are collecting these internal detail page URLs
            # The Scrapy spider will then visit these to get the *actual external* tool URL.
            # However, the user request for Phase 1 is:
            # "Identify and extract the external links that point directly to the individual AI tool websites."
            # "Important: We only want the URL of the tool's own website, not the URL of the tool's page on "There's An AI For That"."
            # This means this script needs to visit EACH detail page to get the external link.
            # This makes this script more complex than just a list page scraper.
            # Let's adjust the plan: this script will get URLs of *detail pages* on TAAFT.
            # The Scrapy spider will then be responsible for visiting those detail pages
            # AND THEN extracting the final external tool URL.
            # For now, this script will output TAAFT detail page URLs.
            # We can refine this if we find direct external links on list pages,
            # or decide this script should do the two-step hop (list -> detail -> external URL).

            # Let's stick to the original intent for this script: get *external* tool URLs.
            # This means this script needs to:
            # 1. Scrape list pages for links to detail pages.
            # 2. For each detail page link, visit it.
            # 3. On the detail page, find the actual external tool website URL.
            
            # Given the complexity, and to keep this script focused on *URL extraction from a directory*,
            # a simpler approach for Phase 1 is to extract the URLs of the *detail pages* on TAAFT.
            # The Scrapy spider (already partially built for TAAFT) is better suited for
            # visiting those detail pages and then extracting the final external website link.

            # Re-evaluating the user's request: "Identify and extract the external links that point
            # directly to the individual AI tool websites."
            # This implies this script *should* try to get the final external link.
            # This means for each tool_detail_page_url found, we need another request.

            # This script will collect the TAAFT *detail page* URLs.
            # The existing `taaft` Scrapy spider is already designed to visit these
            # detail pages and extract the `website_url` (external).
            # So, this script's output should be `tool_detail_pages_taaft.txt`.
            # The Scrapy spider will consume this.
            #
            # Let's adjust output file name and purpose slightly to reflect this.
            # No, the request is clear: "external links that point directly to the individual AI tool websites"
            # This means this script needs to find the link on the list page that *leads* to the page containing the external link
            # and then visit *that* page to get the external link.

            # The `a.item-card` elements on the list pages are the ones to follow.
            # Their `href` attribute is a relative path to the tool's detail page on TAAFT.
            
            # Let's assume the current `tool_detail_page_links` selector correctly identifies these.
            # For each such link, we need to make another request.

            detail_page_url = urljoin(base_url, href)
            print(f"  Found detail page link: {detail_page_url}")
            time.sleep(REQUEST_DELAY_SECONDS) # Delay before fetching detail page
            detail_html = fetch_page(detail_page_url)
            if detail_html:
                detail_soup = BeautifulSoup(detail_html, 'html.parser')
                # --- Selector for the actual external tool website link on the DETAIL page ---
                # This was 'a.visit-button::attr(href)' or similar from Scrapy spider.
                # Let's use a more generic search for a prominent link that's likely the official site.
                # Often these are marked with "Visit Website" or are the main large clickable element.
                # Example Selector: response.css('a[data-testid="tool-visit-button"]::attr(href)').get()
                external_link_tag = detail_soup.select_one('a[data-testid="tool-visit-button"]')
                if external_link_tag and external_link_tag.get('href'):
                    tool_site_url = external_link_tag.get('href')
                    # Basic validation if it's an external link
                    if urlparse(tool_site_url).netloc and urlparse(tool_site_url).scheme:
                        print(f"    Extracted external tool URL: {tool_site_url}")
                        extracted_urls.add(tool_site_url)
                    else:
                        print(f"    Skipping non-external or invalid URL: {tool_site_url}")
                else:
                    print(f"    Could not find external link button on {detail_page_url}")
            

    return extracted_urls

def find_next_page_url(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    # --- Selector for the "Next Page" link ---
    # Example: response.css('a.pagination-link[rel="next"]::attr(href)').get()
    next_page_tag = soup.select_one('a.pagination-link[rel="next"]') # Adjusted based on Scrapy spider
    if next_page_tag and next_page_tag.get('href'):
        next_page_path = next_page_tag.get('href')
        return urljoin(base_url, next_page_path)
    return None

def main():
    all_tool_website_urls = set()
    current_page_url = urljoin(BASE_URL, START_PATH)
    page_count = 0

    while current_page_url and (MAX_PAGES_TO_SCRAPE is None or page_count < MAX_PAGES_TO_SCRAPE):
        page_count += 1
        print(f"--- Processing Page {page_count}: {current_page_url} ---")
        html_content = fetch_page(current_page_url)

        if page_count == 1 and html_content: # Save first page for inspection
            with open("temp_first_page_output.html", "w", encoding="utf-8") as f_html:
                f_html.write(html_content)
            print("Saved initial HTML to temp_first_page_output.html for inspection.")

        if html_content:
            tool_urls_on_page = extract_tool_website_urls(html_content, BASE_URL)
            if tool_urls_on_page:
                all_tool_website_urls.update(tool_urls_on_page)
            
            current_page_url = find_next_page_url(html_content, BASE_URL)
            if current_page_url:
                print(f"Found next page: {current_page_url}")
            else:
                print("No next page found or max pages reached.")
        else:
            print(f"Failed to fetch content from {current_page_url}, stopping.")
            break
        
        print(f"Sleeping for {REQUEST_DELAY_SECONDS} seconds before next list page...")
        time.sleep(REQUEST_DELAY_SECONDS)

    if all_tool_website_urls:
        print(f"\n--- Found {len(all_tool_website_urls)} unique tool website URLs ---")
        # Ensure the directory for the output file exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            for url in sorted(list(all_tool_website_urls)):
                f.write(url + "\n")
        print(f"Saved URLs to {OUTPUT_FILE}")
    else:
        print("No tool website URLs extracted.")

if __name__ == "__main__":
    main() 