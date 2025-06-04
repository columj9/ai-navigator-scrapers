Product Requirements Document (PRD): AI Navigator - Data Scrapers V1

1. Introduction & Goals

Product: AI Navigator - Data Scrapers V1

Goal: To automatically populate and maintain an initial dataset of AI tools and related entities within the AI Navigator platform by scraping publicly available information from selected online sources. This will provide foundational content for users to discover and evaluate AI solutions.

Primary Objective V1: Gather core information (name, description, website URL, categories, tags) for a significant number of AI tools from 2-3 high-value directory/listing websites.

Secondary Objective V1 (If Feasible): Collect basic review metadata (e.g., average rating, review count) if readily available alongside tool listings. Full review text scraping is a lower priority for V1.

2. Target Users (Internal)

AI Navigator Platform (Database needs to be populated)

AI Navigator Curation/Admin Team (To verify and enrich scraped data)

3. User Stories / Functional Requirements (V1)

FS1: Scrape AI Tool Directories: The system must be able to scrape designated AI tool directory websites to extract information about individual AI tools.

FS2: Extract Core Tool Information: For each tool, the scraper must extract (at minimum):

Tool Name

Website URL

Short Description / Tagline

Categories/Tags (as listed on the source site)

FS3: Extract Extended Tool Information (If Available): If easily accessible on the source page, extract:

Longer Description

Logo URL

Pricing Model Indication (e.g., "Free", "Freemium", "Paid")

FS4: Data Storage: Scraped data must be structured and stored in a temporary/staging area or directly inserted/updated into the public.entities and relevant public.entity_details_tool tables (with appropriate mapping).

FS5: Deduplication: The system should attempt to avoid creating duplicate entries for the same tool if it's found on multiple sources or during subsequent scrapes (e.g., based on website URL or name + close description).

FS6: Basic Review Metadata (Stretch Goal for V1): If a source page lists an average user rating and/or a review count for a tool, extract this information. (Actual review text is out of scope for V1 scraping).

FS7: Configuration: The scraper should be configurable to target specific websites and define selectors for data extraction.

FS8: Logging: The scraper must log its activities, including successfully scraped items, errors encountered, and sites visited.

FS9: Scheduling (Future V1.1): The ability to schedule scrapers to run periodically (e.g., daily/weekly) to find new tools or update existing ones. (For V1, manual execution is acceptable).

4. Non-Functional Requirements

NFR1: Respectful Scraping: Adhere to robots.txt, implement rate limiting, and use appropriate user agents.

NFR2: Resilience: Scrapers should be reasonably resilient to minor changes in website structure, though major redesigns will require updates.

NFR3: Maintainability: Scraper code should be modular and well-documented to allow for easier updates and addition of new sources.

NFR4: Error Handling: Gracefully handle network errors, missing data elements, and unexpected page structures.

5. Scope (V1)

IN SCOPE:

Scraping 2-3 pre-identified AI tool directory websites.

Scraping core entity information as defined in FS2 & FS3.

Basic deduplication based on website URL.

Storing data in the AI Navigator database.

Basic logging.

Manual execution of scrapers.

(Stretch) Scraping review metadata (average rating, review count).

OUT OF SCOPE (for V1):

Scraping Twitter (X) or other highly restrictive social media platforms.

Scraping actual review text content.

Advanced AI/NLP for data cleaning or categorization beyond what's on the source.

Automated scheduling of scrapers (can be V1.1).

A UI for managing scrapers.

Scraping images/logos directly (focus on URLs).

6. Success Metrics (V1)

Successfully scrape and ingest data for at least 500 unique AI tools into the database.

Achieve >80% accuracy in extracting core fields (name, URL, description) from target sites.

Scrapers complete runs on target sites without significant manual intervention for common errors.

Phased Plan for Creating Scrapers (V1)

Phase 0: Preparation & Setup (1-2 days)

Choose Initial Target Sites (2-3):

Action: Based on previous discussion, select 2-3 high-value AI tool directories (e.g., "There's An AI For That," another similar one, Product Hunt AI section).

Verify: Check their robots.txt and Terms of Service for scraping guidelines.

Set Up Python Scraper Project:

Action: Create a new Git repository (e.g., ai-navigator-scrapers).

Set up a Python environment (e.g., using venv or conda).

Install core libraries: scrapy, playwright (if needed for JS-heavy sites, start with Scrapy), python-dotenv (for DB credentials), psycopg2-binary (for PostgreSQL).

Database Access Configuration:

Action: Ensure the scraper environment can securely access the Supabase PostgreSQL database. Set up .env for DATABASE_URL.

Define a simple Python script to test DB connection and basic inserts/updates.

Phase 1: Scraper for First Target Site (e.g., "There's An AI For That") (3-5 days)

Site Analysis:

Action: Manually analyze the HTML structure of the target site's list pages and individual tool detail pages. Identify CSS selectors or XPath expressions for each data point (name, URL, description, categories, tags, logo URL, pricing indication, review metadata if present).

Develop Scrapy Spider:

Action: Create a new Scrapy spider for the target site.

Implement logic to navigate through list pages/pagination.

Implement logic to follow links to detail pages.

Implement extraction logic using the identified selectors.

Implement basic error handling for missing elements.

Data Cleaning & Structuring:

Action: Clean extracted data (remove whitespace, normalize basic formats).

Map extracted categories/tags to your existing Categories and Tags (or prepare them for insertion if new).

Structure the data to match your entities and entity_details_tool (or a staging table) schema.

Database Insertion Logic:

Action: Implement functions to connect to the database and insert/update the scraped data.

Implement basic deduplication: Before inserting, check if an entity with the same website_url already exists. If so, consider updating it or skipping.

Logging:

Action: Add logging for successful scrapes, items processed, errors, etc.

Initial Testing & Iteration:

Action: Run the scraper on a small subset of pages. Debug and refine selectors and logic.

Phase 2: Scraper for Second Target Site (e.g., Product Hunt AI) (3-5 days)

API First:

Action: Thoroughly investigate Product Hunt's API. If it provides the necessary data, prioritize using it.

Repeat Phase 1 Steps: If API is insufficient, repeat site analysis, spider development, data cleaning, DB insertion, and testing for the second site. Note structural differences.

Phase 3: Scraper for Third Target Site (Optional for V1, if needed) (2-4 days)

Repeat Phase 1 Steps.

Phase 4: Refinement, Robustness & Documentation (2-3 days)

Error Handling & Resilience:

Action: Improve error handling across all scrapers. Add retries for network issues. Make selectors more robust if possible.

Configuration:

Action: Externalize site-specific configurations (start URLs, key selectors) if not already done, to make adding new sites easier.

Deduplication Enhancement:

Action: Review and improve the deduplication logic.

Code Documentation:

Action: Add comments and a basic README for the scraper project.

Full Test Runs:

Action: Run all scrapers to populate a significant amount of data. Monitor logs.

Consideration for Reviews (V1 - Stretch Goal):

During Phase 1, 2, or 3 (Site Analysis for each target):

Action: Identify if average rating and review count are easily extractable alongside other tool data.

If yes, add logic to the spider to extract these.

Map these to the avg_rating and review_count fields in your entities table (or a temporary field if you want to verify them first).

Important: This is for metadata only. Scraping individual review text is explicitly out of scope for V1 due to complexity and potential ethical/ToS concerns with some sites.

This plan provides a focused V1 for getting core AI tool data. We can iterate and add more sources, more data points (like full reviews if ethically sourced and technically feasible), and automation in subsequent versions.