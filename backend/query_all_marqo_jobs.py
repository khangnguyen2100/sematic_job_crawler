#!/usr/bin/env python3
"""
Script to query all jobs data from Marqo
"""

import requests
import json
import os
from typing import Dict, Any, List

# Configuration
MARQO_URL = os.getenv("MARQO_URL", "http://localhost:8882")
INDEX_NAME = "job-index"

def get_all_jobs_by_search() -> Dict[str, Any]:
    """
    Get all jobs using a broad search query with high limit
    """
    try:
        # Use a broad query to match all documents
        search_payload = {
            "q": "",  # Empty query to match all documents
            "limit": 1000,  # High limit to get all jobs
            "offset": 0,
            "searchableAttributes": ["title", "description", "company_name"]
        }
        
        response = requests.post(
            f"{MARQO_URL}/indexes/{INDEX_NAME}/search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_payload)
        )
        
        if response.status_code != 200:
            print(f"Search request failed: {response.status_code} - {response.text}")
            return {"error": f"Request failed: {response.text}"}
            
        return response.json()
        
    except Exception as e:
        print(f"Error searching all jobs: {e}")
        return {"error": str(e)}

def get_index_stats() -> Dict[str, Any]:
    """
    Get index statistics
    """
    try:
        response = requests.get(f"{MARQO_URL}/indexes/{INDEX_NAME}/stats")
        
        if response.status_code != 200:
            print(f"Stats request failed: {response.status_code} - {response.text}")
            return {"error": f"Request failed: {response.text}"}
            
        return response.json()
        
    except Exception as e:
        print(f"Error getting index stats: {e}")
        return {"error": str(e)}

def get_all_jobs_paginated(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all jobs using pagination
    """
    all_jobs = []
    offset = 0
    
    while True:
        try:
            search_payload = {
                "q": "",
                "limit": limit,
                "offset": offset,
                "searchableAttributes": ["title", "description", "company_name"]
            }
            
            response = requests.post(
                f"{MARQO_URL}/indexes/{INDEX_NAME}/search",
                headers={"Content-Type": "application/json"},
                data=json.dumps(search_payload)
            )
            
            if response.status_code != 200:
                print(f"Search request failed: {response.status_code} - {response.text}")
                break
                
            results = response.json()
            hits = results.get("hits", [])
            
            if not hits:
                break
                
            all_jobs.extend(hits)
            offset += limit
            
            print(f"Retrieved {len(hits)} jobs (total so far: {len(all_jobs)})")
            
            # If we got fewer than the limit, we've reached the end
            if len(hits) < limit:
                break
                
        except Exception as e:
            print(f"Error in pagination: {e}")
            break
    
    return all_jobs

def main():
    print(f"Connecting to Marqo at: {MARQO_URL}")
    print(f"Index name: {INDEX_NAME}")
    print("-" * 50)
    
    # First, get index statistics
    print("Getting index statistics...")
    stats = get_index_stats()
    if "error" not in stats:
        print(f"Index stats: {json.dumps(stats, indent=2)}")
    else:
        print(f"Error getting stats: {stats['error']}")
    
    print("-" * 50)
    
    # Get all jobs using broad search
    print("Querying all jobs using broad search...")
    all_jobs_result = get_all_jobs_by_search()
    
    if "error" not in all_jobs_result:
        hits = all_jobs_result.get("hits", [])
        print(f"Found {len(hits)} jobs")
        
        # Display summary information
        print("\nJob Summary:")
        sources = {}
        companies = {}
        
        for job in hits:
            # Count by source
            source = job.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
            
            # Count by company
            company = job.get("company_name", "unknown")
            companies[company] = companies.get(company, 0) + 1
        
        print(f"Jobs by source: {json.dumps(sources, indent=2)}")
        print(f"Top 10 companies: {json.dumps(dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]), indent=2)}")
        
        # Display first few jobs as examples
        print(f"\nFirst 3 jobs (example):")
        for i, job in enumerate(hits[:3]):
            print(f"Job {i+1}:")
            print(f"  ID: {job.get('_id')}")
            print(f"  Title: {job.get('title')}")
            print(f"  Company: {job.get('company_name')}")
            print(f"  Source: {job.get('source')}")
            print(f"  Location: {job.get('location')}")
            print(f"  Score: {job.get('_score')}")
            print()
        
        # Save all jobs to file
        output_file = "all_marqo_jobs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs_result, f, indent=2, ensure_ascii=False)
        print(f"All jobs data saved to: {output_file}")
        
    else:
        print(f"Error querying jobs: {all_jobs_result['error']}")
        
        # Try paginated approach as fallback
        print("\nTrying paginated approach...")
        all_jobs = get_all_jobs_paginated()
        if all_jobs:
            print(f"Retrieved {len(all_jobs)} jobs using pagination")
            
            # Save paginated results
            output_file = "all_marqo_jobs_paginated.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"hits": all_jobs, "total": len(all_jobs)}, f, indent=2, ensure_ascii=False)
            print(f"Paginated jobs data saved to: {output_file}")

if __name__ == "__main__":
    main()
