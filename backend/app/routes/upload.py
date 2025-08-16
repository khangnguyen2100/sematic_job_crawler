from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List
import pandas as pd
import io
from datetime import datetime

from app.models.schemas import JobCreate, JobSource, UploadResponse, JobBulkUpload
from app.services.marqo_service import MarqoService
from app.models.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

def get_marqo_service():
    from app.main import marqo_service
    return marqo_service

@router.post("/upload/csv", response_model=UploadResponse)
async def upload_jobs_csv(
    file: UploadFile = File(...),
    marqo_service: MarqoService = Depends(get_marqo_service),
    db: Session = Depends(get_db)
):
    """
    ## Upload Jobs from CSV
    
    Upload job data from a CSV file and automatically index them for semantic search.
    
    ### CSV Format Required:
    The CSV file must contain these columns:
    ```
    title,company,description,source,url
    "Software Engineer","Tech Corp","Python developer role...","linkedin","https://..."
    "Data Scientist","AI Startup","Machine learning position...","topcv","https://..."
    ```
    
    ### Processing Steps:
    1. **File Validation**: Checks CSV format and required columns
    2. **Data Processing**: Parses and validates job data
    3. **Database Storage**: Saves jobs to PostgreSQL database
    4. **Vector Indexing**: Creates embeddings in Marqo for semantic search
    
    ### File Requirements:
    - **Format**: CSV file (.csv)
    - **Size**: Maximum 10MB
    - **Encoding**: UTF-8 recommended
    - **Required Columns**: title, company, description, source, url
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['title', 'description', 'company_name', 'original_url']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        # Check for alternative column names and rename them
        column_mappings = {
            'company': 'company_name',
            'url': 'original_url'
        }
        
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Re-check for missing columns after mapping
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Process jobs
        jobs = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle posted_date
                posted_date = datetime.utcnow()
                if 'posted_date' in df.columns and pd.notna(row['posted_date']):
                    try:
                        posted_date = pd.to_datetime(row['posted_date'])
                    except:
                        pass  # Use current date if parsing fails
                
                # Handle source
                job_source = JobSource.OTHER  # Default source
                if 'source' in df.columns and pd.notna(row['source']):
                    try:
                        job_source = JobSource(str(row['source']))
                    except ValueError:
                        job_source = JobSource.OTHER  # Use default if invalid source
                
                job = JobCreate(
                    title=str(row['title']),
                    description=str(row['description']),
                    company_name=str(row['company_name']),
                    posted_date=posted_date,
                    source=job_source,
                    original_url=str(row['original_url']),
                    location=str(row.get('location', '')) if pd.notna(row.get('location')) else None,
                    salary=str(row.get('salary', '')) if pd.notna(row.get('salary')) else None,
                    job_type=str(row.get('job_type', '')) if pd.notna(row.get('job_type')) else None,
                    experience_level=str(row.get('experience_level', '')) if pd.notna(row.get('experience_level')) else None
                )
                jobs.append(job)
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        if not jobs:
            raise HTTPException(status_code=400, detail="No valid jobs found in CSV")
        
        # Check for duplicates and add jobs
        processed_jobs = 0
        
        for job in jobs:
            try:
                # Check for duplicates using PostgreSQL
                is_duplicate = marqo_service.check_duplicate_job(job, db)
                
                if not is_duplicate:
                    # Add job to Marqo
                    job_id = await marqo_service.add_job(job)
                    processed_jobs += 1
                else:
                    errors.append(f"Duplicate job skipped: {job.title} at {job.company_name}")
                    
            except Exception as e:
                errors.append(f"Error adding job '{job.title}': {str(e)}")
        
        return UploadResponse(
            message=f"Successfully processed {processed_jobs} jobs from CSV",
            processed_jobs=processed_jobs,
            errors=errors
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")

@router.post("/upload/json", response_model=UploadResponse)
async def upload_jobs_json(
    jobs_payload: JobBulkUpload,
    marqo_service: MarqoService = Depends(get_marqo_service),
    db: Session = Depends(get_db)
):
    """Upload jobs from JSON data"""
    
    if not jobs_payload.jobs:
        raise HTTPException(status_code=400, detail="No jobs provided")
    
    try:
        processed_jobs = 0
        errors = []
        
        for i, job in enumerate(jobs_payload.jobs):
            try:
                # Check for duplicates using PostgreSQL
                is_duplicate = marqo_service.check_duplicate_job(job, db)
                
                if not is_duplicate:
                    # Add job to Marqo
                    job_id = await marqo_service.add_job(job)
                    processed_jobs += 1
                else:
                    errors.append(f"Job {i + 1}: Duplicate skipped - {job.title} at {job.company_name}")
                    
            except Exception as e:
                errors.append(f"Job {i + 1}: Error adding '{job.title}' - {str(e)}")
        
        return UploadResponse(
            message=f"Successfully processed {processed_jobs} jobs from JSON",
            processed_jobs=processed_jobs,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process JSON: {str(e)}")

@router.get("/upload/template")
async def download_csv_template():
    """Download CSV template for job uploads"""
    
    template_data = {
        'title': ['Software Developer', 'Frontend Engineer'],
        'description': [
            'We are looking for a skilled software developer...',
            'Join our team as a frontend engineer...'
        ],
        'company_name': ['Tech Company A', 'Startup B'],
        'original_url': [
            'https://example.com/job1',
            'https://example.com/job2'
        ],
        'posted_date': ['2024-01-15', '2024-01-16'],
        'location': ['Ho Chi Minh City', 'Ha Noi'],
        'salary': ['15-25 million VND', '20-30 million VND'],
        'job_type': ['Full-time', 'Full-time'],
        'experience_level': ['Mid-level', 'Senior']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create CSV content
    csv_content = df.to_csv(index=False)
    
    from fastapi.responses import Response
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=job_upload_template.csv"}
    )
