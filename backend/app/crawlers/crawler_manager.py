from typing import List
import asyncio
from datetime import datetime

from .base_crawler import BaseCrawler
from .job_crawlers import TopCVCrawler, ITViecCrawler, VietnamWorksCrawler, LinkedInCrawler
from app.models.schemas import JobCreate, CrawlResult, CrawlSourceResult
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
    
    async def crawl_all_sources(self, max_jobs_per_source: int = 100) -> CrawlResult:
        """Crawl jobs from all available sources with detailed statistics"""
        start_time = datetime.utcnow()
        
        total_crawled = 0
        total_added = 0
        total_already_exist = 0
        all_errors = []
        source_results = {}
        
        for crawler in self.crawlers:
            source_start_time = datetime.utcnow()
            crawled_count = 0
            added_count = 0
            duplicates_count = 0
            source_errors = []
            
            try:
                print(f"Starting crawl for {crawler.source_name}...")
                
                # Check if source is available
                if not await crawler.is_available():
                    error_msg = f"{crawler.source_name} is not available"
                    print(error_msg)
                    source_errors.append(error_msg)
                    all_errors.append(error_msg)
                    
                    # Create failed source result
                    source_results[crawler.source_name] = CrawlSourceResult(
                        source=crawler.source_name,
                        total_crawled=0,
                        jobs_added=0,
                        jobs_already_exist=0,
                        errors=source_errors,
                        success_rate=0.0,
                        duration_seconds=0.0
                    )
                    continue
                
                # Crawl jobs
                jobs = await crawler.crawl_jobs(max_jobs_per_source)
                crawled_count = len(jobs)
                
                print(f"Crawled {crawled_count} jobs from {crawler.source_name}")
                
                # Process each job
                for job in jobs:
                    try:
                        # Check for duplicates using Marqo
                        is_duplicate = await self.marqo_service.check_duplicate_job(job)
                        
                        if is_duplicate:
                            duplicates_count += 1
                            continue
                        
                        # Add job to Marqo
                        marqo_id = await self.marqo_service.add_job(job)
                        added_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing job from {crawler.source_name}: {e}"
                        print(error_msg)
                        source_errors.append(error_msg)
                        all_errors.append(error_msg)
                
                source_end_time = datetime.utcnow()
                source_duration = (source_end_time - source_start_time).total_seconds()
                
                # Calculate success rate for this source
                success_rate = (added_count / crawled_count * 100) if crawled_count > 0 else 0
                
                # Create source result
                source_results[crawler.source_name] = CrawlSourceResult(
                    source=crawler.source_name,
                    total_crawled=crawled_count,
                    jobs_added=added_count,
                    jobs_already_exist=duplicates_count,
                    errors=source_errors,
                    success_rate=success_rate,
                    duration_seconds=source_duration
                )
                
                # Update totals
                total_crawled += crawled_count
                total_added += added_count
                total_already_exist += duplicates_count
                
                print(f"Completed {crawler.source_name}: {added_count} added, {duplicates_count} already exist")
                
            except Exception as e:
                error_msg = f"Error crawling {crawler.source_name}: {e}"
                print(error_msg)
                source_errors.append(error_msg)
                all_errors.append(error_msg)
                
                # Create failed source result
                source_results[crawler.source_name] = CrawlSourceResult(
                    source=crawler.source_name,
                    total_crawled=0,
                    jobs_added=0,
                    jobs_already_exist=0,
                    errors=source_errors,
                    success_rate=0.0,
                    duration_seconds=0.0
                )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate overall success rate
        overall_success_rate = (total_added / total_crawled * 100) if total_crawled > 0 else 0
        
        print(f"Crawling completed: {total_added} total jobs added, {total_already_exist} already existed")
        
        return CrawlResult(
            total_crawled=total_crawled,
            total_added=total_added,
            total_already_exist=total_already_exist,
            sources_processed=len(self.crawlers),
            errors=all_errors,
            source_results=source_results,
            started_at=start_time,
            completed_at=end_time,
            duration_seconds=duration,
            success_rate=overall_success_rate
        )
    
    async def crawl_source(self, source_name: str, max_jobs: int = 100) -> dict:
        """Crawl jobs from a specific source with detailed statistics"""
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
            already_exist_count = 0

            for job in jobs:
                try:
                    # Check for duplicates using Marqo
                    is_duplicate = await self.marqo_service.check_duplicate_job(job)

                    if is_duplicate:
                        already_exist_count += 1
                        continue

                    # Add job to Marqo
                    marqo_id = await self.marqo_service.add_job(job)
                    added_count += 1

                except Exception as e:
                    print(f"Error processing job: {e}")

            return {
                'source': source_name,
                'total_crawled': len(jobs),
                'jobs_added': added_count,
                'jobs_already_exist': already_exist_count,
                'success_rate': (added_count / len(jobs) * 100) if len(jobs) > 0 else 0
            }

        except Exception as e:
            return {'error': f"Error crawling {source_name}: {e}"}
    
    def get_available_sources(self) -> List[str]:
        """Get list of available crawler sources"""
        return [crawler.source_name for crawler in self.crawlers]
