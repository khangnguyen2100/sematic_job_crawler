#!/usr/bin/env python3
"""
Detailed analysis of all jobs data from Marqo
"""

import json
from collections import Counter
from datetime import datetime
import pandas as pd

def analyze_jobs_data(json_file: str):
    """
    Perform detailed analysis of jobs data
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('hits', [])
        print(f"Total jobs in Marqo: {len(jobs)}")
        print("=" * 60)
        
        # 1. Analysis by Source
        sources = [job.get('source', 'Unknown') for job in jobs]
        source_counts = Counter(sources)
        print("Jobs by Source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        print()
        
        # 2. Analysis by Company
        companies = [job.get('company_name', 'Unknown') for job in jobs]
        company_counts = Counter(companies)
        print("Top 15 Companies:")
        for company, count in company_counts.most_common(15):
            print(f"  {company}: {count}")
        print()
        
        # 3. Analysis by Location
        locations = [job.get('location', 'Unknown') for job in jobs]
        location_counts = Counter(locations)
        print("Jobs by Location:")
        for location, count in location_counts.most_common(10):
            print(f"  {location}: {count}")
        print()
        
        # 4. Analysis by Job Type
        job_types = [job.get('job_type', 'Unknown') for job in jobs]
        job_type_counts = Counter(job_types)
        print("Jobs by Type:")
        for job_type, count in job_type_counts.items():
            print(f"  {job_type}: {count}")
        print()
        
        # 5. Analysis by Experience Level
        experience_levels = [job.get('experience_level', 'Unknown') for job in jobs]
        experience_counts = Counter(experience_levels)
        print("Jobs by Experience Level:")
        for level, count in experience_counts.items():
            print(f"  {level}: {count}")
        print()
        
        # 6. Salary Analysis
        salaries = [job.get('salary') for job in jobs if job.get('salary')]
        print(f"Jobs with salary information: {len(salaries)} out of {len(jobs)}")
        if salaries:
            print("Sample salaries:")
            for i, salary in enumerate(salaries[:10]):
                print(f"  {salary}")
        print()
        
        # 7. Date Analysis
        posted_dates = []
        created_dates = []
        
        for job in jobs:
            if job.get('posted_date'):
                try:
                    posted_dates.append(datetime.fromisoformat(job['posted_date'].replace('Z', '+00:00')))
                except:
                    pass
            
            if job.get('created_at'):
                try:
                    created_dates.append(datetime.fromisoformat(job['created_at'].replace('Z', '+00:00')))
                except:
                    pass
        
        if posted_dates:
            print(f"Posted date range: {min(posted_dates)} to {max(posted_dates)}")
        if created_dates:
            print(f"Crawled date range: {min(created_dates)} to {max(created_dates)}")
        print()
        
        # 8. Job Title Analysis
        titles = [job.get('title', '') for job in jobs]
        title_words = []
        for title in titles:
            title_words.extend(title.lower().split())
        
        word_counts = Counter(title_words)
        print("Most common words in job titles:")
        for word, count in word_counts.most_common(20):
            if len(word) > 2:  # Filter out very short words
                print(f"  {word}: {count}")
        print()
        
        # 9. Full job examples
        print("First 5 complete job examples:")
        print("-" * 40)
        for i, job in enumerate(jobs[:5]):
            print(f"Job {i+1}:")
            print(f"  ID: {job.get('_id')}")
            print(f"  Title: {job.get('title')}")
            print(f"  Company: {job.get('company_name')}")
            print(f"  Location: {job.get('location')}")
            print(f"  Salary: {job.get('salary')}")
            print(f"  Experience: {job.get('experience_level')}")
            print(f"  Job Type: {job.get('job_type')}")
            print(f"  Source: {job.get('source')}")
            print(f"  Posted Date: {job.get('posted_date')}")
            print(f"  URL: {job.get('original_url')}")
            print(f"  Description: {job.get('description')[:200]}...")
            print(f"  Score: {job.get('_score')}")
            print("-" * 40)
        
        # 10. Data quality analysis
        print("Data Quality Analysis:")
        required_fields = ['title', 'company_name', 'source', 'original_url']
        optional_fields = ['location', 'salary', 'job_type', 'experience_level', 'description']
        
        for field in required_fields:
            missing = sum(1 for job in jobs if not job.get(field))
            print(f"  {field}: {len(jobs) - missing}/{len(jobs)} ({((len(jobs) - missing)/len(jobs)*100):.1f}%)")
        
        for field in optional_fields:
            missing = sum(1 for job in jobs if not job.get(field))
            print(f"  {field}: {len(jobs) - missing}/{len(jobs)} ({((len(jobs) - missing)/len(jobs)*100):.1f}%)")
        
    except Exception as e:
        print(f"Error analyzing jobs data: {e}")

if __name__ == "__main__":
    analyze_jobs_data("all_marqo_jobs.json")
