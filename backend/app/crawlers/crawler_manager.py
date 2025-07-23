from typing import List
import asyncio

from .base_crawler import BaseCrawler
from .job_crawlers import TopCVCrawler, ITViecCrawler, VietnamWorksCrawler, LinkedInCrawler
from app.models.schemas import JobCreate
from app.services.marqo_service import MarqoService

class CrawlerManager:
    def __init__(self, marqo_service: MarqoService):
        self.marqo_service = marqo_service
        self.crawlers: List[BaseCrawler] = [
            TopCVCrawler(),
            ITViecCrawler(),
            VietnamWorksCrawler(),
            LinkedInCrawler()
        ]
    
    async def crawl_all_sources(self, max_jobs_per_source: int = 100) -> dict:
        """Crawl jobs from all available sources"""
        results = {
            'total_crawled': 0,
            'total_added': 0,
            'duplicates_skipped': 0,
            'errors': [],
            'source_results': {}
        }
        
        for crawler in self.crawlers:
            try:
                print(f"Starting crawl for {crawler.source_name}...")
                
                # Check if source is available
                if not await crawler.is_available():
                    error_msg = f"{crawler.source_name} is not available"
                    print(error_msg)
                    results['errors'].append(error_msg)
                    continue
                
                # Crawl jobs
                jobs = await crawler.crawl_jobs(max_jobs_per_source)
                crawled_count = len(jobs)
                added_count = 0
                duplicates_count = 0
                
                print(f"Crawled {crawled_count} jobs from {crawler.source_name}")
                
                # Process each job
                for job in jobs:
                    try:
                        # Check for duplicates
                        is_duplicate = await self.marqo_service.check_duplicate_job(job)
                        
                        if is_duplicate:
                            duplicates_count += 1
                            continue
                        
                        # Add job to Marqo
                        await self.marqo_service.add_job(job)
                        added_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing job from {crawler.source_name}: {e}"
                        print(error_msg)
                        results['errors'].append(error_msg)
                
                # Update results
                results['total_crawled'] += crawled_count
                results['total_added'] += added_count
                results['duplicates_skipped'] += duplicates_count
                results['source_results'][crawler.source_name] = {
                    'crawled': crawled_count,
                    'added': added_count,
                    'duplicates': duplicates_count
                }
                
                print(f"Completed {crawler.source_name}: {added_count} added, {duplicates_count} duplicates")
                
            except Exception as e:
                error_msg = f"Error crawling {crawler.source_name}: {e}"
                print(error_msg)
                results['errors'].append(error_msg)
        
        print(f"Crawling completed: {results['total_added']} total jobs added")
        return results
    
    async def crawl_source(self, source_name: str, max_jobs: int = 100) -> dict:
        """Crawl jobs from a specific source"""
        crawler = None
        for c in self.crawlers:
            if c.source_name.lower() == source_name.lower():
                crawler = c
                break
        
        if not crawler:
            return {
                'error': f"Crawler for {source_name} not found",
                'available_sources': [c.source_name for c in self.crawlers]
            }
        
        try:
            if not await crawler.is_available():
                return {'error': f"{source_name} is not available"}
            
            jobs = await crawler.crawl_jobs(max_jobs)
            added_count = 0
            duplicates_count = 0
            
            for job in jobs:
                try:
                    if not await self.marqo_service.check_duplicate_job(job):
                        await self.marqo_service.add_job(job)
                        added_count += 1
                    else:
                        duplicates_count += 1
                except Exception as e:
                    print(f"Error processing job: {e}")
            
            return {
                'source': source_name,
                'crawled': len(jobs),
                'added': added_count,
                'duplicates': duplicates_count
            }
            
        except Exception as e:
            return {'error': f"Error crawling {source_name}: {e}"}
    
    def get_available_sources(self) -> List[str]:
        """Get list of available crawler sources"""
        return [crawler.source_name for crawler in self.crawlers]
