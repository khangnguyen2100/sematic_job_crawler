from typing import List, Optional
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from .base_crawler import BaseCrawler
from .job_crawlers import TopCVCrawler, ITViecCrawler, VietnamWorksCrawler, LinkedInCrawler
from app.models.schemas import JobCreate, CrawlResult, CrawlSourceResult
from app.services.marqo_service import MarqoService
from app.services.crawl_logging_service import CrawlLoggingService, CrawlLogger, AsyncCrawlLogger
from app.services.config_service import config_service


class CrawlerManager:
    def __init__(self, marqo_service: MarqoService, db_session: Optional[Session] = None):
        self.marqo_service = marqo_service
        self.db_session = db_session
        self.logging_service = CrawlLoggingService(db_session) if db_session else None
        self.crawlers: List[BaseCrawler] = [
            TopCVCrawler(db_session=db_session),
            ITViecCrawler(db_session=db_session),
            VietnamWorksCrawler(db_session=db_session),
            LinkedInCrawler(db_session=db_session)
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
                # Use CrawlLogger if logging service is available
                if self.logging_service:
                    # Get dynamic crawler configuration
                    crawler_info = config_service.get_crawler_info(self.db_session, crawler.source_name)
                    
                    async with AsyncCrawlLogger(
                        self.logging_service,
                        site_name=crawler_info['site_name'],
                        site_url=crawler_info['site_url'],
                        request_url=crawler_info['site_url'],  # Use site URL as base request URL
                        crawler_type=crawler_info['crawler_type']
                    ) as logger:
                        # Check if source is available
                        if not await crawler.is_available():
                            error_msg = f"{crawler.source_name} is not available"
                            print(error_msg)
                            source_errors.append(error_msg)
                            all_errors.append(error_msg)
                            
                            # Complete with error
                            logger.complete(
                                response_status=503,  # Service Unavailable
                                response_time_ms=100,
                                jobs_found=0,
                                jobs_processed=0,
                                jobs_stored=0,
                                jobs_duplicated=0,
                                error_message=error_msg
                            )
                            
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
                        
                        # Complete the crawl session with results
                        logger.complete(
                            response_status=200,
                            response_time_ms=int(source_duration * 1000),
                            jobs_found=crawled_count,
                            jobs_processed=crawled_count,
                            jobs_stored=added_count,
                            jobs_duplicated=duplicates_count
                        )
                        
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
                        
                        print(f"Completed {crawler.source_name}: {added_count} added, {duplicates_count} already exist")
                        
                else:
                    # Fallback: crawl without logging
                    if not await crawler.is_available():
                        error_msg = f"{crawler.source_name} is not available"
                        print(error_msg)
                        source_errors.append(error_msg)
                        all_errors.append(error_msg)
                        continue
                    
                    jobs = await crawler.crawl_jobs(max_jobs_per_source)
                    crawled_count = len(jobs)
                    
                    for job in jobs:
                        try:
                            is_duplicate = await self.marqo_service.check_duplicate_job(job)
                            if is_duplicate:
                                duplicates_count += 1
                                continue
                            marqo_id = await self.marqo_service.add_job(job)
                            added_count += 1
                        except Exception as e:
                            error_msg = f"Error processing job from {crawler.source_name}: {e}"
                            print(error_msg)
                            source_errors.append(error_msg)
                            all_errors.append(error_msg)
                    
                    # Create source result
                    source_results[crawler.source_name] = CrawlSourceResult(
                        source=crawler.source_name,
                        total_crawled=crawled_count,
                        jobs_added=added_count,
                        jobs_already_exist=duplicates_count,
                        errors=source_errors,
                        success_rate=(added_count / crawled_count * 100) if crawled_count > 0 else 0,
                        duration_seconds=(datetime.utcnow() - source_start_time).total_seconds()
                    )
                
                # Update totals
                total_crawled += crawled_count
                total_added += added_count
                total_already_exist += duplicates_count
                
            except Exception as e:
                error_msg = f"Error crawling {crawler.source_name}: {e}"
                print(error_msg)
                source_errors.append(error_msg)
                all_errors.append(error_msg)
                
                # Create failed source result
                source_results[crawler.source_name] = CrawlSourceResult(
                    source=crawler.source_name,
                    total_crawled=crawled_count,
                    jobs_added=added_count,
                    jobs_already_exist=duplicates_count,
                    errors=source_errors,
                    success_rate=0.0,
                    duration_seconds=(datetime.utcnow() - source_start_time).total_seconds()
                )
                
                # Update totals with what we managed to process
                total_crawled += crawled_count
                total_added += added_count
                total_already_exist += duplicates_count
        
        # Calculate overall statistics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        overall_success_rate = (total_added / total_crawled * 100) if total_crawled > 0 else 0
        
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
        """Crawl jobs from a specific source"""
        for crawler in self.crawlers:
            if crawler.source_name.lower() == source_name.lower():
                try:
                    if not await crawler.is_available():
                        return {
                            'source': source_name,
                            'success': False,
                            'error': f'{source_name} is not available',
                            'jobs_added': 0,
                            'jobs_already_exist': 0
                        }
                    
                    jobs = await crawler.crawl_jobs(max_jobs)
                    added_count = 0
                    duplicates_count = 0
                    
                    for job in jobs:
                        try:
                            # Check for duplicates
                            is_duplicate = await self.marqo_service.check_duplicate_job(job)
                            
                            if is_duplicate:
                                duplicates_count += 1
                                continue
                            
                            # Add job to Marqo
                            marqo_id = await self.marqo_service.add_job(job)
                            added_count += 1
                            
                        except Exception as e:
                            print(f"Error processing job: {e}")
                            continue
                    
                    return {
                        'source': source_name,
                        'success': True,
                        'jobs_crawled': len(jobs),
                        'jobs_added': added_count,
                        'jobs_already_exist': duplicates_count
                    }
                    
                except Exception as e:
                    return {
                        'source': source_name,
                        'success': False,
                        'error': str(e),
                        'jobs_added': 0,
                        'jobs_already_exist': 0
                    }
        
        return {
            'source': source_name,
            'success': False,
            'error': f'Source {source_name} not found',
            'jobs_added': 0,
            'jobs_already_exist': 0
        }
    
    def get_available_sources(self) -> List[str]:
        """Get list of available source names"""
        return [crawler.source_name for crawler in self.crawlers]
