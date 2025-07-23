from fastapi import Request
import hashlib

def get_user_id(request: Request) -> str:
    """
    Generate a user ID based on IP address and user agent
    This creates a pseudo-anonymous identifier for tracking user interactions
    """
    # Get client IP address
    client_ip = request.client.host
    
    # Handle forwarded headers (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Get user agent for additional uniqueness
    user_agent = request.headers.get("User-Agent", "")
    
    # Create a hash-based user ID
    # This provides some privacy while still allowing tracking of the same user
    combined = f"{client_ip}:{user_agent}"
    user_id = hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    return user_id

def get_client_ip(request: Request) -> str:
    """Get the real client IP address"""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host
