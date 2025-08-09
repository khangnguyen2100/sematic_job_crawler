"""
Test script for sync job functionality
"""
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawl_progress_service import crawl_progress_service

def test_sync_job_creation():
    """Test creating a sync job"""
    print("Testing sync job creation...")
    
    # Create a test job
    job_id = crawl_progress_service.create_crawl_job("TopCV", {
        "search_keywords": ["python-developer"],
        "max_pages": 2,
        "request_delay": 1.0
    })
    
    print(f"Created job ID: {job_id}")
    
    # Get job progress
    progress = crawl_progress_service.get_job_progress(job_id)
    if progress:
        print(f"Job status: {progress.status}")
        print(f"Number of steps: {len(progress.steps)}")
        print("Steps:")
        for i, step in enumerate(progress.steps):
            print(f"  {i+1}. {step.name}: {step.status}")
    else:
        print("Failed to get job progress")
    
    # Test updating a step
    print("\nTesting step update...")
    success = crawl_progress_service.update_step(
        job_id, "1", "running", "Initializing crawler..."
    )
    print(f"Step update success: {success}")
    
    # Get updated progress
    progress = crawl_progress_service.get_job_progress(job_id)
    if progress:
        first_step = progress.steps[0]
        print(f"First step status: {first_step.status}")
        print(f"First step message: {first_step.message}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_sync_job_creation()
