"""
FastAPI Backend Server for AI Navigator Scraper Management
Provides API endpoints to manage scraping jobs and monitor progress
"""

import os
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import json
import asyncio
from datetime import datetime

# Add project root to path for imports
sys.path.append('/app')

from scraper_pipeline import ScraperPipeline

# Initialize FastAPI app
app = FastAPI(title="AI Navigator Scraper API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline = None

# Pydantic models
class ScrapingJobRequest(BaseModel):
    spider_name: str
    max_items: Optional[int] = 50

class ScrapingJobResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    message: str
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize the scraper pipeline on startup"""
    global pipeline
    try:
        pipeline = ScraperPipeline()
        logger.info("Scraper pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scraper pipeline: {str(e)}")
        raise

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/spiders")
async def get_available_spiders():
    """Get list of available Scrapy spiders"""
    try:
        spiders = pipeline.get_available_spiders() if pipeline else []
        return {"spiders": spiders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_pipeline_status():
    """Get current pipeline status"""
    try:
        status = pipeline.get_status() if pipeline else {"is_running": False}
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start-scraping", response_model=ScrapingJobResponse)
async def start_scraping_job(request: ScrapingJobRequest, background_tasks: BackgroundTasks):
    """Start a new scraping job"""
    try:
        if not pipeline:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        # Validate spider name
        available_spiders = pipeline.get_available_spiders()
        if request.spider_name not in available_spiders:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid spider name. Available: {available_spiders}"
            )
        
        # Start scraping job in background
        def run_scraper():
            try:
                result = pipeline.run_spider(request.spider_name, request.max_items)
                logger.info(f"Scraping job completed: {result}")
            except Exception as e:
                logger.error(f"Background scraping job failed: {str(e)}")
        
        background_tasks.add_task(run_scraper)
        
        return ScrapingJobResponse(
            success=True,
            job_id=f"{request.spider_name}_{int(asyncio.get_event_loop().time())}",
            message=f"Started scraping job for {request.spider_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scraping job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-services")
async def test_services():
    """Test all pipeline services"""
    try:
        if not pipeline:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        results = pipeline.test_services()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    try:
        log_file = "/app/scraper_pipeline.log"
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        return {"logs": [line.strip() for line in logs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/missing-taxonomy")
async def get_missing_taxonomy():
    """Get missing taxonomy items that need admin review"""
    try:
        missing_file = "/app/missing_taxonomy.log"
        missing_items = []
        
        if os.path.exists(missing_file):
            with open(missing_file, 'r') as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        missing_items.append(item)
                    except json.JSONDecodeError:
                        continue
        
        return {"missing_items": missing_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraping-results/{spider_name}")
async def get_scraping_results(spider_name: str):
    """Get results from a specific spider"""
    try:
        results_file = f"/app/ai-navigator-scrapers/{spider_name}_leads.jsonl"
        results = []
        
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                for line in f:
                    try:
                        result = json.loads(line.strip())
                        results.append(result)
                    except json.JSONDecodeError:
                        continue
        
        return {
            "spider_name": spider_name,
            "results_count": len(results),
            "results": results[-50:]  # Return last 50 results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)