# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AinavScrapersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class AiToolItem(scrapy.Item):
    # Core Information (FS2)
    name = scrapy.Field()
    website_url = scrapy.Field()
    short_description = scrapy.Field()
    categories = scrapy.Field() # List of strings
    tags = scrapy.Field() # List of strings

    # Extended Tool Information (FS3)
    long_description = scrapy.Field()
    logo_url = scrapy.Field()
    pricing_model = scrapy.Field() # e.g., "Free", "Freemium", "Paid"

    # Review Metadata (FS6 - Stretch Goal)
    average_rating = scrapy.Field()
    review_count = scrapy.Field()

    # Source Information (for tracking where data came from)
    source_url = scrapy.Field() # URL of the page where the item was scraped
    scraped_date = scrapy.Field()


class AiToolLeadItem(scrapy.Item):
    tool_name_on_directory = scrapy.Field() # Name as seen on TAAFT
    external_website_url = scrapy.Field()  # The crucial external URL
    source_directory = scrapy.Field()      # e.g., "theresanaiforthat.com"
    scraped_date = scrapy.Field() # To know when the lead was generated
