# backend/app/api/dependencies.py
"""
API dependencies.

This module defines common dependencies for API routes,
such as database sessions and pagination.
"""
from typing import Any
from fastapi import Depends, Query

from app.database.database import db_connection

async def get_db():
    """
    Provide a database connection for route handlers.
    
    Returns: Database connection object
    """
    async with db_connection() as conn:
        yield conn

def pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
) -> dict[str, int]:
    """
    Provide standardized pagination parameters.
    
    Returns: Dictionary with validated pagination parameters
    """
    # Ensure valid page values
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    # Calculate skip value for database queries
    skip = (page - 1) * page_size
    
    return {
        "page": page,
        "page_size": page_size,
        "skip": skip
    }