"""
URL utilities for job processing
"""
from urllib.parse import urlparse, urlunparse
from typing import Optional


def clean_job_url(url: Optional[str]) -> Optional[str]:
    """
    Remove query parameters and fragments from a job URL to create a clean URL for duplicate checking.
    
    Example:
        Input: "https://www.topcv.vn/viec-lam/it-lead/1833111.html?ta_source=JobSearchList_LinkDetail&u_sr_id=yg7oVjZzNlcCvwZGUTNtXw7AvBVplV3At9TO1LYT_1755341525"
        Output: "https://www.topcv.vn/viec-lam/it-lead/1833111.html"
    
    Args:
        url: The original URL that may contain query parameters and fragments
        
    Returns:
        Clean URL without query parameters and fragments, or None if invalid URL
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        # Parse the URL
        parsed = urlparse(url.strip())
        
        # Reconstruct URL without query and fragment
        clean_parsed = parsed._replace(query='', fragment='')
        clean_url = urlunparse(clean_parsed)
        
        return clean_url if clean_url else None
        
    except Exception as e:
        print(f"Error cleaning URL '{url}': {e}")
        return None


def extract_base_domain(url: Optional[str]) -> Optional[str]:
    """
    Extract the base domain from a URL.
    
    Example:
        Input: "https://www.topcv.vn/viec-lam/it-lead/1833111.html"
        Output: "topcv.vn"
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Base domain or None if invalid URL
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if netloc.startswith('www.'):
            netloc = netloc[4:]
            
        return netloc if netloc else None
        
    except Exception as e:
        print(f"Error extracting domain from URL '{url}': {e}")
        return None
