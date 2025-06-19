"""
Taxonomy Service for mapping scraped categories/tags/features to AI Navigator API UUIDs
"""

import logging
from typing import Dict, List, Optional, Any
from difflib import SequenceMatcher
import json
import os

class TaxonomyService:
    def __init__(self, ai_navigator_client):
        self.client = ai_navigator_client
        self.categories_map = {}  # name -> id mapping
        self.tags_map = {}       # name -> id mapping 
        self.features_map = {}   # name -> id mapping
        self.missing_items = []  # Track items not found
        self.logger = logging.getLogger(__name__)
        
        # Load taxonomy on initialization
        self._load_taxonomy()
    
    def _load_taxonomy(self):
        """Load categories, tags, and features from API"""
        try:
            # Load categories
            categories = self.client.get_categories()
            for category in categories:
                name = category.get('name', '').lower().strip()
                if name:
                    self.categories_map[name] = category.get('id')
            
            self.logger.info(f"Loaded {len(self.categories_map)} categories")
            
            # Load tags
            tags = self.client.get_tags()
            for tag in tags:
                name = tag.get('name', '').lower().strip()
                if name:
                    self.tags_map[name] = tag.get('id')
            
            self.logger.info(f"Loaded {len(self.tags_map)} tags")
            
            # Load features
            features = self.client.get_features()
            for feature in features:
                name = feature.get('name', '').lower().strip()
                if name:
                    self.features_map[name] = feature.get('id')
            
            self.logger.info(f"Loaded {len(self.features_map)} features")
            
        except Exception as e:
            self.logger.error(f"Error loading taxonomy: {str(e)}")
    
    def _find_best_match(self, scraped_name: str, taxonomy_map: Dict[str, str], threshold: float = 0.6) -> Optional[str]:
        """Find best matching taxonomy item using fuzzy string matching"""
        scraped_name = scraped_name.lower().strip()
        
        # First try exact match
        if scraped_name in taxonomy_map:
            return taxonomy_map[scraped_name]
        
        # Try partial matches and common variations
        category_mappings = {
            'ai': 'natural language processing',
            'chatbots': 'natural language processing', 
            'language models': 'natural language processing',
            'nlp': 'natural language processing',
            'computer vision': 'computer vision',
            'image': 'computer vision',
            'vision': 'computer vision',
            'data science': 'data science & analytics',
            'analytics': 'data science & analytics',
            'data analysis': 'data science & analytics',
            'machine learning': 'machine learning platforms',
            'ml': 'machine learning platforms',
            'developer': 'developer tools',
            'development': 'developer tools',
            'coding': 'developer tools',
            'infrastructure': 'ai infrastructure',
            'robotics': 'robotics & automation',
            'automation': 'robotics & automation',
            'education': 'ai education & learning',
            'learning': 'ai education & learning',
            'ethics': 'ai ethics & governance'
        }
        
        tag_mappings = {
            'ai chatbot': 'free tier',  # Map to available tags
            'language generation': 'api access',
            'code assistance': 'api access',
            'data analysis': 'data visualization',
            'free': 'free tier',
            'api': 'api access',
            'cloud': 'cloud-based',
            'beginner': 'beginner-friendly'
        }
        
        feature_mappings = {
            'generates human-like text responses': 'gui interface',
            'summarizes meetings and documents': 'detailed documentation',
            'assists with code generation and debugging': 'cli tool',
            'supports real-time voice conversations': 'active community support',
            'analyzes images and data': 'detailed documentation',
            'creates images from text descriptions': 'gui interface',
            'deep research capabilities': 'detailed documentation',
            'mobile file uploads': 'gui interface',
            'tone and formatting preferences': 'gui interface',
            'free trial': 'free trial available',
            'trial': 'free trial available',
            'documentation': 'detailed documentation',
            'community': 'active community support',
            'gui': 'gui interface',
            'command line': 'cli tool',
            'cli': 'cli tool'
        }
        
        # Choose the right mapping based on taxonomy type
        if 'categories' in str(taxonomy_map):
            mappings = category_mappings
        elif 'tags' in str(taxonomy_map):
            mappings = tag_mappings  
        else:
            mappings = feature_mappings
            
        # Check for keyword matches
        for keyword, mapped_value in mappings.items():
            if keyword in scraped_name:
                if mapped_value in taxonomy_map:
                    return taxonomy_map[mapped_value]
        
        # Try fuzzy matching as fallback
        best_match = None
        best_score = 0
        
        for taxonomy_name in taxonomy_map.keys():
            score = SequenceMatcher(None, scraped_name, taxonomy_name).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = taxonomy_map[taxonomy_name]
        
        return best_match
    
    def map_categories(self, scraped_categories: List[str]) -> List[str]:
        """Map scraped category names to UUIDs"""
        mapped_ids = []
        
        for category_name in scraped_categories:
            if not category_name or not category_name.strip():
                continue
                
            category_id = self._find_best_match(category_name, self.categories_map)
            
            if category_id:
                mapped_ids.append(category_id)
                self.logger.debug(f"Mapped category '{category_name}' to ID: {category_id}")
            else:
                self.logger.warning(f"Could not map category: '{category_name}'")
                self._log_missing_item('category', category_name)
        
        return mapped_ids
    
    def map_tags(self, scraped_tags: List[str]) -> List[str]:
        """Map scraped tag names to UUIDs"""
        mapped_ids = []
        
        for tag_name in scraped_tags:
            if not tag_name or not tag_name.strip():
                continue
                
            tag_id = self._find_best_match(tag_name, self.tags_map)
            
            if tag_id:
                mapped_ids.append(tag_id)
                self.logger.debug(f"Mapped tag '{tag_name}' to ID: {tag_id}")
            else:
                self.logger.warning(f"Could not map tag: '{tag_name}'")
                self._log_missing_item('tag', tag_name)
        
        return mapped_ids
    
    def map_features(self, scraped_features: List[str]) -> List[str]:
        """Map scraped feature names to UUIDs"""
        mapped_ids = []
        
        for feature_name in scraped_features:
            if not feature_name or not feature_name.strip():
                continue
                
            feature_id = self._find_best_match(feature_name, self.features_map)
            
            if feature_id:
                mapped_ids.append(feature_id)
                self.logger.debug(f"Mapped feature '{feature_name}' to ID: {feature_id}")
            else:
                self.logger.warning(f"Could not map feature: '{feature_name}'")
                self._log_missing_item('feature', feature_name)
        
        return mapped_ids
    
    def _log_missing_item(self, item_type: str, item_name: str):
        """Log missing taxonomy items for admin review"""
        missing_item = {
            'type': item_type,
            'name': item_name,
            'timestamp': str(datetime.now())
        }
        self.missing_items.append(missing_item)
        
        # Write to log file
        log_file = '/app/missing_taxonomy.log'
        try:
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(missing_item)}\n")
        except Exception as e:
            self.logger.error(f"Could not write to missing taxonomy log: {str(e)}")
    
    def get_missing_items(self) -> List[Dict[str, Any]]:
        """Get all missing taxonomy items from current session"""
        return self.missing_items
    
    def get_default_category_id(self) -> Optional[str]:
        """Get a default category ID for tools without specific category"""
        # Look for common default categories
        defaults = ['ai tools', 'artificial intelligence', 'productivity', 'general']
        
        for default_name in defaults:
            if default_name in self.categories_map:
                return self.categories_map[default_name]
        
        # Return first category if available
        if self.categories_map:
            return list(self.categories_map.values())[0]
        
        return None

from datetime import datetime