# backend/app/api/dependencies.py
"""
API dependencies.

This module defines common dependencies for API routes,
such as database sessions and pagination.
"""

def get_db():
    """
    Provide a database connection for route handlers.
    
    Algorithm:
    1. Get connection from database.get_db_connection()
    2. Yield connection to route handler
    3. Ensure connection is closed after request, even if errors occur
    
    Why dependency injection matters:
    - Centralizes connection management
    - Ensures proper cleanup
    - Simplifies testing with mocked connections
    
    Usage:
    @router.get("/endpoint")
    def endpoint(db: Depends(get_db)):
        # Use db connection here
    
    Returns: Database connection object
    """
    pass

def pagination_params(page, page_size):
    """
    Provide standardized pagination parameters.
    
    Algorithm:
    1. Validate and sanitize pagination inputs:
       - Ensure page >= 1 (default to 1)
       - Ensure page_size between 1 and 100 (default to 10)
    2. Calculate skip (offset) value: (page - 1) * page_size
    3. Return dictionary with page, page_size, and skip
    
    Why standardized pagination matters:
    - Consistent behavior across endpoints
    - Prevents invalid pagination values
    - Simplifies client-side implementation
    
    Usage:
    @router.get("/items")
    def get_items(pagination: Depends(pagination_params)):
        skip = pagination["skip"]
        limit = pagination["page_size"]
        # Use in query
    
    Returns: Dictionary with validated pagination parameters
    """
    pass