"""
Main Scraper Pipeline
Coordinates the entire scraping and data processing workflow
"""

import logging
import sys
import os
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Add the project root to Python path for imports
sys.path.append('/app')

from ai_navigator_client import AINavigatorClient
from data_enrichment_service import DataEnrichmentService
from taxonomy_service import TaxonomyService
from enhanced_item_processor import EnhancedItemProcessor

class ScraperPipeline:
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Initialize services
        self.ai_client = AINavigatorClient()
        self.enrichment_service = DataEnrichmentService("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")
        self.taxonomy_service = TaxonomyService(self.ai_client)
        self.item_processor = EnhancedItemProcessor(
            self.ai_client,
            self.enrichment_service, 
            self.taxonomy_service
        )
        
        # Pipeline state
        self.is_running = False
        self.current_job = None
        self.stats = {
            'total_processed': 0,
            'successful_submissions': 0,
            'failed_submissions': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/scraper_pipeline.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def run_spider(self, spider_name: str, max_items: Optional[int] = None) -> Dict[str, Any]:
        """Run a specific Scrapy spider and process results"""
        
        if self.is_running:
            return {
                'success': False,
                'message': 'Another scraping job is already running',
                'job_id': self.current_job
            }
        
        self.is_running = True
        job_id = f"{spider_name}_{int(time.time())}"
        self.current_job = job_id
        
        try:
            self.logger.info(f"Starting scraping job: {job_id}")
            
            # Reset stats
            self.stats = {
                'total_processed': 0,
                'successful_submissions': 0,
                'failed_submissions': 0,
                'duplicates_skipped': 0,
                'errors': [],
                'spider_name': spider_name,
                'job_id': job_id,
                'start_time': time.time()
            }
            
            # Run the spider
            spider_results = self._run_scrapy_spider(spider_name, max_items)
            
            if not spider_results['success']:
                return spider_results
            
            # Process the scraped leads
            leads_file = spider_results['output_file']
            self._process_leads_file(leads_file)
            
            # Final stats
            self.stats['end_time'] = time.time()
            self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']
            
            self.logger.info(f"Completed scraping job: {job_id}")
            self.logger.info(f"Stats: {json.dumps(self.stats, indent=2)}")
            
            return {
                'success': True,
                'job_id': job_id,
                'stats': self.stats,
                'message': f"Successfully processed {self.stats['successful_submissions']} entities"
            }
            
        except Exception as e:
            self.logger.error(f"Error in scraping job {job_id}: {str(e)}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'stats': self.stats
            }
        finally:
            self.is_running = False
            self.current_job = None
    
    def _run_scrapy_spider(self, spider_name: str, max_items: Optional[int] = None) -> Dict[str, Any]:
        """Execute the Scrapy spider"""
        try:
            scrapy_dir = "/app/ai-navigator-scrapers"
            output_file = f"/app/ai-navigator-scrapers/{spider_name}_leads.jsonl"
            
            # Build scrapy command
            cmd_parts = [
                "cd", scrapy_dir, "&&",
                "scrapy", "crawl", spider_name,
                "-o", output_file
            ]
            
            if max_items:
                cmd_parts.extend(["-s", f"CLOSESPIDER_ITEMCOUNT={max_items}"])
            
            cmd = " ".join(cmd_parts)
            
            self.logger.info(f"Running command: {cmd}")
            
            # Execute command
            import subprocess
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Spider {spider_name} completed successfully")
                return {
                    'success': True,
                    'output_file': output_file,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                self.logger.error(f"Spider {spider_name} failed with code {result.returncode}")
                self.logger.error(f"STDERR: {result.stderr}")
                return {
                    'success': False,
                    'error': f"Spider failed with exit code {result.returncode}",
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Spider execution timed out after 1 hour'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error running spider: {str(e)}"
            }
    
    def _process_leads_file(self, leads_file: str):
        """Process scraped leads from JSONL file"""
        if not os.path.exists(leads_file):
            self.logger.error(f"Leads file not found: {leads_file}")
            return
        
        self.logger.info(f"Processing leads from: {leads_file}")
        
        with open(leads_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    lead_item = json.loads(line.strip())
                    self._process_single_lead(lead_item, line_num)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON on line {line_num}: {str(e)}")
                    self.stats['errors'].append(f"Line {line_num}: Invalid JSON")
                except Exception as e:
                    self.logger.error(f"Error processing line {line_num}: {str(e)}")
                    self.stats['errors'].append(f"Line {line_num}: {str(e)}")
    
    def _process_single_lead(self, lead_item: Dict[str, Any], line_num: int):
        """Process a single lead item"""
        self.stats['total_processed'] += 1
        
        try:
            # Transform lead to CreateEntityDto
            entity_dto = self.item_processor.process_lead_item(lead_item)
            
            if not entity_dto:
                self.stats['duplicates_skipped'] += 1
                return
            
            # Submit to AI Navigator API
            result = self.ai_client.create_entity(entity_dto)
            
            if result:
                self.stats['successful_submissions'] += 1
                self.logger.info(f"Successfully created entity: {entity_dto.get('name')}")
            else:
                self.stats['failed_submissions'] += 1
                self.logger.error(f"Failed to create entity: {entity_dto.get('name')}")
                
        except Exception as e:
            self.stats['failed_submissions'] += 1
            self.stats['errors'].append(f"Line {line_num}: {str(e)}")
            self.logger.error(f"Error processing lead on line {line_num}: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'is_running': self.is_running,
            'current_job': self.current_job,
            'stats': self.stats
        }
    
    def get_available_spiders(self) -> List[str]:
        """Get list of available Scrapy spiders"""
        return ['toolify', 'taaft', 'futuretools']
    
    def test_services(self) -> Dict[str, Any]:
        """Test all services to ensure they're working"""
        results = {}
        
        # Test AI Navigator API
        try:
            categories = self.ai_client.get_categories()
            results['ai_navigator_api'] = {
                'status': 'success',
                'categories_count': len(categories)
            }
        except Exception as e:
            results['ai_navigator_api'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test Data Enrichment Service
        try:
            test_data = self.enrichment_service.enrich_tool_data("ChatGPT", "https://chat.openai.com", "AI chatbot")
            results['data_enrichment'] = {
                'status': 'success',
                'test_keys': list(test_data.keys()) if test_data else []
            }
        except Exception as e:
            results['data_enrichment'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Test Taxonomy Service
        try:
            missing_items = self.taxonomy_service.get_missing_items()
            results['taxonomy_service'] = {
                'status': 'success',
                'categories_loaded': len(self.taxonomy_service.categories_map),
                'tags_loaded': len(self.taxonomy_service.tags_map),
                'features_loaded': len(self.taxonomy_service.features_map)
            }
        except Exception as e:
            results['taxonomy_service'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return results

# Main execution
if __name__ == "__main__":
    pipeline = ScraperPipeline()
    
    # Test services
    print("Testing services...")
    test_results = pipeline.test_services()
    print(json.dumps(test_results, indent=2))
    
    # Run a spider if specified
    if len(sys.argv) > 1:
        spider_name = sys.argv[1]
        max_items = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        print(f"Running spider: {spider_name} with max {max_items} items")
        result = pipeline.run_spider(spider_name, max_items)
        print(json.dumps(result, indent=2))